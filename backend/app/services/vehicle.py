"""Service helpers for interacting with vehicle records."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
from uuid import uuid4

from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.vehicle import (
    Vehicle,
    VehicleDocumentType,
    VehicleStatus,
    VehicleType,
)
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


@dataclass(slots=True)
class VehicleDocumentReminder:
    """Lightweight representation of an expiring vehicle document."""

    vehicle_id: int
    registration_number: str
    document_type: VehicleDocumentType
    expiry_date: date
    days_until_expiry: int
    document_path: Optional[str]


_DOCUMENT_FIELD_MAP = {
    VehicleDocumentType.TAX: "tax_document_path",
    VehicleDocumentType.INSURANCE: "insurance_document_path",
    VehicleDocumentType.INSPECTION: "inspection_document_path",
}

_DOCUMENT_EXPIRY_MAP = {
    VehicleDocumentType.TAX: "tax_expiry_date",
    VehicleDocumentType.INSURANCE: "insurance_expiry_date",
    VehicleDocumentType.INSPECTION: "inspection_expiry_date",
}


async def get_vehicle_by_id(session: AsyncSession, vehicle_id: int) -> Optional[Vehicle]:
    """Return the vehicle with the supplied primary key, if present."""
    result = await session.execute(select(Vehicle).where(Vehicle.id == vehicle_id))
    return result.scalar_one_or_none()


async def get_vehicle_by_registration_number(
    session: AsyncSession, registration_number: str
) -> Optional[Vehicle]:
    """Return the vehicle associated with *registration_number*, if any."""
    normalised = registration_number.strip().upper()
    result = await session.execute(
        select(Vehicle).where(func.upper(Vehicle.registration_number) == normalised)
    )
    return result.scalar_one_or_none()


async def list_vehicles(
    session: AsyncSession,
    *,
    skip: int = 0,
    limit: Optional[int] = None,
    status: Optional[VehicleStatus] = None,
    vehicle_type: Optional[VehicleType] = None,
    search: Optional[str] = None,
) -> list[Vehicle]:
    """Return a list of vehicles filtered by the provided parameters."""
    stmt: Select[tuple[Vehicle]] = select(Vehicle).order_by(Vehicle.id)

    if status is not None:
        stmt = stmt.where(Vehicle.status == status)

    if vehicle_type is not None:
        stmt = stmt.where(Vehicle.vehicle_type == vehicle_type)

    if search:
        pattern = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Vehicle.registration_number).like(pattern),
                func.lower(Vehicle.brand).like(pattern),
                func.lower(Vehicle.model).like(pattern),
            )
        )

    if skip:
        stmt = stmt.offset(skip)

    if limit is not None:
        stmt = stmt.limit(limit)

    result = await session.execute(stmt)
    return list(result.scalars().all())


async def create_vehicle(session: AsyncSession, vehicle_in: VehicleCreate) -> Vehicle:
    """Persist a new vehicle record after validating constraints."""
    existing = await get_vehicle_by_registration_number(
        session, vehicle_in.registration_number
    )
    if existing is not None:
        raise ValueError("Vehicle with this registration number already exists")

    vehicle = Vehicle(**vehicle_in.model_dump())
    session.add(vehicle)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ValueError("Vehicle with this registration number already exists") from exc

    await session.refresh(vehicle)
    return vehicle


async def update_vehicle(
    session: AsyncSession, *, vehicle: Vehicle, vehicle_update: VehicleUpdate
) -> Vehicle:
    """Update the supplied *vehicle* with the provided attributes."""
    data = vehicle_update.model_dump(exclude_unset=True)

    new_registration = data.get("registration_number")
    if new_registration and new_registration != vehicle.registration_number:
        existing = await get_vehicle_by_registration_number(session, new_registration)
        if existing is not None and existing.id != vehicle.id:
            raise ValueError("Vehicle with this registration number already exists")

    for field, value in data.items():
        setattr(vehicle, field, value)

    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ValueError("Vehicle with this registration number already exists") from exc

    await session.refresh(vehicle)
    return vehicle


async def store_vehicle_document(
    session: AsyncSession,
    *,
    vehicle: Vehicle,
    document_type: VehicleDocumentType,
    filename: str,
    content: bytes,
) -> str:
    """Persist *content* as the uploaded document for *vehicle*."""

    if not filename:
        raise ValueError("Uploaded file must include a filename")

    extension = Path(filename).suffix.lower()
    if not extension:
        raise ValueError("Uploaded file must have an extension")

    extension_without_dot = extension[1:] if extension.startswith(".") else extension
    allowed_extensions = {ext.lower() for ext in settings.ALLOWED_EXTENSIONS}
    if extension_without_dot not in allowed_extensions:
        raise ValueError(
            f"File type '{extension_without_dot}' is not permitted; allowed types: "
            f"{', '.join(sorted(allowed_extensions))}"
        )

    if not content:
        raise ValueError("Uploaded file is empty")

    if len(content) > settings.MAX_FILE_SIZE:
        raise ValueError("Uploaded file exceeds the maximum allowed size")

    upload_root = Path(settings.UPLOAD_DIR)
    document_dir = upload_root / "vehicles" / str(vehicle.id) / document_type.value
    document_dir.mkdir(parents=True, exist_ok=True)

    filename_on_disk = f"{uuid4().hex}{extension}"
    file_path = document_dir / filename_on_disk
    file_path.write_bytes(content)

    field_name = _DOCUMENT_FIELD_MAP[document_type]
    existing_path = getattr(vehicle, field_name)
    if existing_path:
        try:
            existing_file = upload_root / Path(existing_path)
            existing_file.unlink(missing_ok=True)
        except OSError:  # pragma: no cover - filesystem issues should not fail request
            pass

    relative_path = file_path.relative_to(upload_root).as_posix()
    setattr(vehicle, field_name, relative_path)

    await session.commit()
    await session.refresh(vehicle)
    return relative_path


async def update_vehicle_status(
    session: AsyncSession, *, vehicle: Vehicle, status: VehicleStatus
) -> Vehicle:
    """Update only the status field for *vehicle*."""
    vehicle.status = status
    await session.commit()
    await session.refresh(vehicle)
    return vehicle


async def delete_vehicle(session: AsyncSession, *, vehicle: Vehicle) -> None:
    """Delete the supplied *vehicle* from the database."""
    await session.delete(vehicle)
    await session.commit()


async def get_expiring_vehicle_documents(
    session: AsyncSession, *, within_days: int = 30
) -> list[VehicleDocumentReminder]:
    """Return vehicle documents that expire within the provided window."""

    if within_days < 0:
        raise ValueError("within_days must be greater than or equal to zero")

    today = date.today()
    window_end = today + timedelta(days=within_days)

    conditions = [
        getattr(Vehicle, expiry_attr).between(today, window_end)
        for expiry_attr in _DOCUMENT_EXPIRY_MAP.values()
    ]

    if not conditions:
        return []

    stmt: Select[tuple[Vehicle]] = select(Vehicle).where(or_(*conditions))
    result = await session.execute(stmt)
    vehicles = result.scalars().all()

    reminders: list[VehicleDocumentReminder] = []
    for vehicle in vehicles:
        for document_type, expiry_attr in _DOCUMENT_EXPIRY_MAP.items():
            expiry_date = getattr(vehicle, expiry_attr)
            if expiry_date is None:
                continue
            if expiry_date < today or expiry_date > window_end:
                continue

            path_attr = _DOCUMENT_FIELD_MAP[document_type]
            reminders.append(
                VehicleDocumentReminder(
                    vehicle_id=vehicle.id,
                    registration_number=vehicle.registration_number,
                    document_type=document_type,
                    expiry_date=expiry_date,
                    days_until_expiry=(expiry_date - today).days,
                    document_path=getattr(vehicle, path_attr),
                )
            )

    reminders.sort(
        key=lambda reminder: (
            reminder.expiry_date,
            reminder.vehicle_id,
            reminder.document_type.value,
        )
    )
    return reminders
