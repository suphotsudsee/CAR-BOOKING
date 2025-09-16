"""Service helpers for interacting with vehicle records."""

from __future__ import annotations

from typing import Optional

from sqlalchemy import Select, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import Vehicle, VehicleStatus, VehicleType
from app.schemas.vehicle import VehicleCreate, VehicleUpdate


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
