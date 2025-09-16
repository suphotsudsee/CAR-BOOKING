from datetime import date, timedelta, time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.driver import DriverStatus
from app.models.user import UserRole
from app.schemas import (
    DriverAvailabilitySchedule,
    DriverAvailabilityUpdate,
    DriverCreate,
    DriverStatusUpdate,
    DriverUpdate,
    UserCreate,
)
from app.services import (
    create_driver,
    create_user,
    delete_driver,
    get_expiring_driver_licenses,
    list_drivers,
    update_driver,
    update_driver_availability,
    update_driver_status,
)


@pytest.mark.asyncio
async def test_create_driver(async_session: AsyncSession) -> None:
    availability = DriverAvailabilitySchedule(
        {
            "monday": {"start": time(8, 0), "end": time(17, 0), "available": True},
            "sunday": {"available": False},
        }
    )

    driver_in = DriverCreate(
        employee_code=" drv-001 ",
        full_name="  Jane   Smith  ",
        phone_number="+62 812 3456",
        license_number=" ab 1234 cd ",
        license_type="b",
        license_expiry_date=date.today() + timedelta(days=365),
        availability_schedule=availability,
    )

    driver = await create_driver(async_session, driver_in)

    assert driver.id is not None
    assert driver.employee_code == "DRV-001"
    assert driver.full_name == "Jane Smith"
    assert driver.license_number == "AB 1234 CD"
    assert driver.license_type == "B"
    assert driver.status == DriverStatus.ACTIVE
    assert driver.availability_schedule is not None
    assert driver.availability_schedule["monday"]["start"] == "08:00:00"


@pytest.mark.asyncio
async def test_create_driver_duplicate_constraints(async_session: AsyncSession) -> None:
    driver_in = DriverCreate(
        employee_code="DRV002",
        full_name="Driver One",
        phone_number="081234",
        license_number="LIC001",
        license_type="B",
        license_expiry_date=date.today() + timedelta(days=400),
    )

    await create_driver(async_session, driver_in)

    with pytest.raises(ValueError):
        await create_driver(async_session, driver_in)


@pytest.mark.asyncio
async def test_create_driver_user_link(async_session: AsyncSession) -> None:
    user = await create_user(
        async_session,
        UserCreate(
            username="driveruser",
            email="driver@example.com",
            full_name="Driver User",
            department="Logistics",
            role=UserRole.DRIVER,
            password="Password123",
        ),
    )

    driver = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV100",
            full_name="Driver Linked",
            phone_number="08123456",
            license_number="LIC100",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=200),
            user_id=user.id,
        ),
    )

    assert driver.user_id == user.id

    with pytest.raises(ValueError):
        await create_driver(
            async_session,
            DriverCreate(
                employee_code="DRV101",
                full_name="Driver Linked 2",
                phone_number="08123457",
                license_number="LIC101",
                license_type="B",
                license_expiry_date=date.today() + timedelta(days=200),
                user_id=user.id,
            ),
        )


@pytest.mark.asyncio
async def test_update_driver(async_session: AsyncSession) -> None:
    driver = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV200",
            full_name="Driver Update",
            phone_number="08123458",
            license_number="LIC200",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=300),
        ),
    )

    updated = await update_driver(
        async_session,
        driver=driver,
        driver_update=DriverUpdate(
            full_name="Driver Updated",
            phone_number="+62 81 234 580",
            license_number="LIC201",
            license_type="C",
            license_expiry_date=date.today() + timedelta(days=600),
            availability_schedule=DriverAvailabilitySchedule(
                {"friday": {"start": time(9, 0), "end": time(15, 0), "available": True}}
            ),
        ),
    )

    assert updated.full_name == "Driver Updated"
    assert updated.phone_number == "+62 81 234 580"
    assert updated.license_number == "LIC201"
    assert updated.license_type == "C"
    assert updated.availability_schedule["friday"]["start"] == "09:00:00"


@pytest.mark.asyncio
async def test_update_driver_duplicate_license(async_session: AsyncSession) -> None:
    first = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV300",
            full_name="Driver One",
            phone_number="08123459",
            license_number="LIC300",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=300),
        ),
    )
    second = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV301",
            full_name="Driver Two",
            phone_number="08123460",
            license_number="LIC301",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=300),
        ),
    )

    with pytest.raises(ValueError):
        await update_driver(
            async_session,
            driver=second,
            driver_update=DriverUpdate(license_number=first.license_number),
        )


@pytest.mark.asyncio
async def test_list_drivers_filters(async_session: AsyncSession) -> None:
    await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV400",
            full_name="Alice",
            phone_number="08123461",
            license_number="LIC400",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
            status=DriverStatus.ACTIVE,
        ),
    )
    await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV401",
            full_name="Bob",
            phone_number="08123462",
            license_number="LIC401",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
            status=DriverStatus.ON_LEAVE,
        ),
    )
    await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV402",
            full_name="Charlie",
            phone_number="08123463",
            license_number="LIC402",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
            status=DriverStatus.INACTIVE,
        ),
    )

    active = await list_drivers(async_session, status=DriverStatus.ACTIVE)
    assert [driver.employee_code for driver in active] == ["DRV400"]

    search = await list_drivers(async_session, search="bob")
    assert [driver.employee_code for driver in search] == ["DRV401"]


@pytest.mark.asyncio
async def test_driver_status_and_availability_updates(async_session: AsyncSession) -> None:
    driver = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV500",
            full_name="Status Driver",
            phone_number="08123464",
            license_number="LIC500",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
        ),
    )

    updated_status = await update_driver_status(
        async_session,
        driver=driver,
        status_update=DriverStatusUpdate(status=DriverStatus.INACTIVE),
    )
    assert updated_status.status == DriverStatus.INACTIVE

    availability = await update_driver_availability(
        async_session,
        driver=driver,
        availability_update=DriverAvailabilityUpdate(
            availability_schedule=DriverAvailabilitySchedule(
                {
                    "tuesday": {"start": time(7, 0), "end": time(12, 0), "available": True},
                    "wednesday": {"available": False},
                }
            )
        ),
    )
    assert availability.availability_schedule["tuesday"]["end"] == "12:00:00"


@pytest.mark.asyncio
async def test_get_expiring_driver_licenses(async_session: AsyncSession) -> None:
    await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV600",
            full_name="Expiring Soon",
            phone_number="08123465",
            license_number="LIC600",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=5),
        ),
    )
    await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV601",
            full_name="Expiring Now",
            phone_number="08123466",
            license_number="LIC601",
            license_type="B",
            license_expiry_date=date.today(),
        ),
    )
    await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV602",
            full_name="Far Future",
            phone_number="08123467",
            license_number="LIC602",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=60),
        ),
    )

    reminders = await get_expiring_driver_licenses(async_session, within_days=30)
    assert {reminder.employee_code for reminder in reminders} == {"DRV600", "DRV601"}
    days_until = {reminder.employee_code: reminder.days_until_expiry for reminder in reminders}
    assert days_until["DRV600"] == 5
    assert days_until["DRV601"] == 0

    with pytest.raises(ValueError):
        await get_expiring_driver_licenses(async_session, within_days=-1)


@pytest.mark.asyncio
async def test_delete_driver(async_session: AsyncSession) -> None:
    driver = await create_driver(
        async_session,
        DriverCreate(
            employee_code="DRV700",
            full_name="Delete Driver",
            phone_number="08123468",
            license_number="LIC700",
            license_type="B",
            license_expiry_date=date.today() + timedelta(days=365),
        ),
    )

    await delete_driver(async_session, driver=driver)

    remaining = await list_drivers(async_session)
    assert remaining == []
