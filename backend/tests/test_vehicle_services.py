from datetime import date, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.vehicle import (
    FuelType,
    VehicleDocumentType,
    VehicleStatus,
    VehicleType,
)
from app.schemas import VehicleCreate, VehicleUpdate
from app.services import (
    create_vehicle,
    delete_vehicle,
    get_expiring_vehicle_documents,
    get_vehicle_by_id,
    list_vehicles,
    update_vehicle,
    update_vehicle_status,
)


@pytest.mark.asyncio
async def test_create_vehicle(async_session: AsyncSession) -> None:
    vehicle_in = VehicleCreate(
        registration_number="b 1234 xyz",
        vehicle_type=VehicleType.SEDAN,
        brand="Toyota",
        model="Camry",
        year_manufactured=2021,
        seating_capacity=4,
        fuel_type=FuelType.GASOLINE,
        current_mileage=10000,
    )

    vehicle = await create_vehicle(async_session, vehicle_in)

    assert vehicle.id is not None
    assert vehicle.registration_number == "B 1234 XYZ"
    assert vehicle.status == VehicleStatus.ACTIVE
    assert vehicle.current_mileage == 10000


@pytest.mark.asyncio
async def test_create_vehicle_duplicate_registration(async_session: AsyncSession) -> None:
    vehicle_in = VehicleCreate(
        registration_number="B 5678 QWE",
        vehicle_type=VehicleType.VAN,
        brand="Hyundai",
        model="Staria",
        seating_capacity=7,
        fuel_type=FuelType.DIESEL,
    )

    await create_vehicle(async_session, vehicle_in)

    with pytest.raises(ValueError):
        await create_vehicle(async_session, vehicle_in)


@pytest.mark.asyncio
async def test_update_vehicle(async_session: AsyncSession) -> None:
    vehicle = await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 1111 AAA",
            vehicle_type=VehicleType.SEDAN,
            brand="Honda",
            model="Accord",
            year_manufactured=2020,
            seating_capacity=4,
            fuel_type=FuelType.HYBRID,
            current_mileage=5000,
        ),
    )

    updated = await update_vehicle(
        async_session,
        vehicle=vehicle,
        vehicle_update=VehicleUpdate(
            registration_number="B 1111 AAB",
            brand="Honda Updated",
            model="Accord LX",
            seating_capacity=5,
            current_mileage=7500,
            status=VehicleStatus.MAINTENANCE,
            notes="Scheduled maintenance",
        ),
    )

    assert updated.registration_number == "B 1111 AAB"
    assert updated.brand == "Honda Updated"
    assert updated.model == "Accord LX"
    assert updated.seating_capacity == 5
    assert updated.current_mileage == 7500
    assert updated.status == VehicleStatus.MAINTENANCE
    assert updated.notes == "Scheduled maintenance"


@pytest.mark.asyncio
async def test_update_vehicle_duplicate_registration(async_session: AsyncSession) -> None:
    existing = await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 2222 BBB",
            vehicle_type=VehicleType.BUS,
            brand="Mercedes",
            model="Sprinter",
            seating_capacity=12,
            fuel_type=FuelType.DIESEL,
        ),
    )
    target = await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 3333 CCC",
            vehicle_type=VehicleType.PICKUP,
            brand="Ford",
            model="Ranger",
            seating_capacity=4,
            fuel_type=FuelType.DIESEL,
        ),
    )

    with pytest.raises(ValueError):
        await update_vehicle(
            async_session,
            vehicle=target,
            vehicle_update=VehicleUpdate(registration_number=existing.registration_number),
        )


@pytest.mark.asyncio
async def test_list_vehicles_filters(async_session: AsyncSession) -> None:
    await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 4444 DDD",
            vehicle_type=VehicleType.SEDAN,
            brand="Toyota",
            model="Vios",
            seating_capacity=4,
            fuel_type=FuelType.GASOLINE,
            status=VehicleStatus.ACTIVE,
        ),
    )
    await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 5555 EEE",
            vehicle_type=VehicleType.VAN,
            brand="Kia",
            model="Carnival",
            seating_capacity=7,
            fuel_type=FuelType.DIESEL,
            status=VehicleStatus.MAINTENANCE,
        ),
    )
    await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 6666 FFF",
            vehicle_type=VehicleType.SEDAN,
            brand="Tesla",
            model="Model S",
            seating_capacity=5,
            fuel_type=FuelType.ELECTRIC,
            status=VehicleStatus.INACTIVE,
        ),
    )

    sedans = await list_vehicles(async_session, vehicle_type=VehicleType.SEDAN)
    assert {vehicle.registration_number for vehicle in sedans} == {
        "B 4444 DDD",
        "B 6666 FFF",
    }

    maintenance = await list_vehicles(async_session, status=VehicleStatus.MAINTENANCE)
    assert [vehicle.registration_number for vehicle in maintenance] == ["B 5555 EEE"]

    search_results = await list_vehicles(async_session, search="tesla")
    assert [vehicle.registration_number for vehicle in search_results] == ["B 6666 FFF"]


@pytest.mark.asyncio
async def test_delete_vehicle(async_session: AsyncSession) -> None:
    vehicle = await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 7777 GGG",
            vehicle_type=VehicleType.SEDAN,
            brand="Nissan",
            model="Almera",
            seating_capacity=4,
            fuel_type=FuelType.GASOLINE,
        ),
    )

    await delete_vehicle(async_session, vehicle=vehicle)

    fetched = await get_vehicle_by_id(async_session, vehicle.id)
    assert fetched is None


@pytest.mark.asyncio
async def test_update_vehicle_status(async_session: AsyncSession) -> None:
    vehicle = await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 8888 HHH",
            vehicle_type=VehicleType.VAN,
            brand="Toyota",
            model="HiAce",
            seating_capacity=10,
            fuel_type=FuelType.DIESEL,
        ),
    )

    updated = await update_vehicle_status(
        async_session,
        vehicle=vehicle,
        status=VehicleStatus.MAINTENANCE,
    )

    assert updated.status == VehicleStatus.MAINTENANCE


@pytest.mark.asyncio
async def test_get_expiring_vehicle_documents(async_session: AsyncSession) -> None:
    today = date.today()

    vehicle_one = await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 9999 III",
            vehicle_type=VehicleType.SEDAN,
            brand="Mazda",
            model="3",
            seating_capacity=4,
            fuel_type=FuelType.GASOLINE,
            tax_expiry_date=today + timedelta(days=5),
            inspection_expiry_date=today + timedelta(days=7),
        ),
    )

    vehicle_two = await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 0001 JJJ",
            vehicle_type=VehicleType.VAN,
            brand="Hyundai",
            model="H1",
            seating_capacity=7,
            fuel_type=FuelType.DIESEL,
            insurance_expiry_date=today + timedelta(days=1),
        ),
    )

    await create_vehicle(
        async_session,
        VehicleCreate(
            registration_number="B 0002 KKK",
            vehicle_type=VehicleType.SEDAN,
            brand="Honda",
            model="City",
            seating_capacity=4,
            fuel_type=FuelType.GASOLINE,
            tax_expiry_date=today + timedelta(days=20),
        ),
    )

    reminders = await get_expiring_vehicle_documents(async_session, within_days=10)
    assert [
        (reminder.vehicle_id, reminder.document_type, reminder.days_until_expiry)
        for reminder in reminders
    ] == [
        (vehicle_two.id, VehicleDocumentType.INSURANCE, 1),
        (vehicle_one.id, VehicleDocumentType.TAX, 5),
        (vehicle_one.id, VehicleDocumentType.INSPECTION, 7),
    ]

    assert all(reminder.document_path is None for reminder in reminders)


@pytest.mark.asyncio
async def test_get_expiring_vehicle_documents_negative_window(
    async_session: AsyncSession,
) -> None:
    with pytest.raises(ValueError):
        await get_expiring_vehicle_documents(async_session, within_days=-1)
