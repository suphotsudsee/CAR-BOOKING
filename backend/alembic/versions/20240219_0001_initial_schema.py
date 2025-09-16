"""Create core booking system tables"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "20240219_0001"
down_revision: str | None = None
branch_labels: tuple[str, ...] | None = None
depends_on: tuple[str, ...] | None = None


def upgrade() -> None:
    """Create initial database schema and seed data."""
    user_role_enum = sa.Enum(
        "requester",
        "manager",
        "fleet_admin",
        "driver",
        "auditor",
        name="userrole",
    )
    vehicle_type_enum = sa.Enum(
        "SEDAN",
        "VAN",
        "PICKUP",
        "BUS",
        "OTHER",
        name="vehicletype",
    )
    vehicle_status_enum = sa.Enum(
        "ACTIVE",
        "MAINTENANCE",
        "INACTIVE",
        name="vehiclestatus",
    )
    fuel_type_enum = sa.Enum(
        "GASOLINE",
        "DIESEL",
        "HYBRID",
        "ELECTRIC",
        name="fueltype",
    )
    driver_status_enum = sa.Enum(
        "ACTIVE",
        "INACTIVE",
        "ON_LEAVE",
        name="driverstatus",
    )
    booking_status_enum = sa.Enum(
        "DRAFT",
        "REQUESTED",
        "APPROVED",
        "REJECTED",
        "ASSIGNED",
        "IN_PROGRESS",
        "COMPLETED",
        "CANCELLED",
        name="bookingstatus",
    )
    vehicle_preference_enum = sa.Enum(
        "ANY",
        "SEDAN",
        "VAN",
        "PICKUP",
        "BUS",
        "OTHER",
        name="vehiclepreference",
    )
    approval_decision_enum = sa.Enum(
        "APPROVED",
        "REJECTED",
        name="approvaldecision",
    )
    job_run_status_enum = sa.Enum(
        "SCHEDULED",
        "IN_PROGRESS",
        "COMPLETED",
        "CANCELLED",
        name="jobrunstatus",
    )

    bind = op.get_bind()
    is_postgresql = bind.dialect.name == "postgresql"

    if is_postgresql:
        for enum in [
            user_role_enum,
            vehicle_type_enum,
            vehicle_status_enum,
            fuel_type_enum,
            driver_status_enum,
            booking_status_enum,
            vehicle_preference_enum,
            approval_decision_enum,
            job_run_status_enum,
        ]:
            enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(length=50), nullable=False, unique=True),
        sa.Column("email", sa.String(length=100), nullable=False, unique=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "two_fa_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            mysql_on_update=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_users_role", "users", ["role"], unique=False)

    op.create_table(
        "vehicles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "registration_number", sa.String(length=20), nullable=False, unique=True
        ),
        sa.Column("vehicle_type", vehicle_type_enum, nullable=False),
        sa.Column("brand", sa.String(length=60), nullable=False),
        sa.Column("model", sa.String(length=60), nullable=False),
        sa.Column("year_manufactured", sa.Integer(), nullable=True),
        sa.Column("seating_capacity", sa.Integer(), nullable=False),
        sa.Column(
            "fuel_type",
            fuel_type_enum,
            nullable=False,
            server_default=sa.text("'GASOLINE'"),
        ),
        sa.Column(
            "status",
            vehicle_status_enum,
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
        sa.Column(
            "current_mileage",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("tax_expiry_date", sa.Date(), nullable=True),
        sa.Column("insurance_expiry_date", sa.Date(), nullable=True),
        sa.Column("inspection_expiry_date", sa.Date(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            mysql_on_update=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_vehicles_vehicle_type", "vehicles", ["vehicle_type"], unique=False
    )
    op.create_index("ix_vehicles_status", "vehicles", ["status"], unique=False)
    op.create_index(
        "ix_vehicles_tax_expiry_date", "vehicles", ["tax_expiry_date"], unique=False
    )
    op.create_index(
        "ix_vehicles_insurance_expiry_date",
        "vehicles",
        ["insurance_expiry_date"],
        unique=False,
    )
    op.create_index(
        "ix_vehicles_inspection_expiry_date",
        "vehicles",
        ["inspection_expiry_date"],
        unique=False,
    )

    op.create_table(
        "drivers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "employee_code", sa.String(length=30), nullable=False, unique=True
        ),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("phone_number", sa.String(length=30), nullable=True),
        sa.Column("license_number", sa.String(length=60), nullable=False),
        sa.Column(
            "license_type",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'B'"),
        ),
        sa.Column("license_expiry_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            driver_status_enum,
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),
        sa.Column("availability_schedule", sa.JSON(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            mysql_on_update=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_drivers_user_id", "drivers", ["user_id"], unique=False)
    op.create_index(
        "ix_drivers_license_number", "drivers", ["license_number"], unique=False
    )
    op.create_index(
        "ix_drivers_license_expiry_date",
        "drivers",
        ["license_expiry_date"],
        unique=False,
    )
    op.create_index("ix_drivers_status", "drivers", ["status"], unique=False)

    op.create_table(
        "booking_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "requester_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("purpose", sa.String(length=500), nullable=False),
        sa.Column(
            "passenger_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("pickup_location", sa.String(length=500), nullable=False),
        sa.Column("dropoff_location", sa.String(length=500), nullable=False),
        sa.Column(
            "vehicle_preference",
            vehicle_preference_enum,
            nullable=False,
            server_default=sa.text("'ANY'"),
        ),
        sa.Column("special_requirements", sa.Text(), nullable=True),
        sa.Column(
            "status",
            booking_status_enum,
            nullable=False,
            server_default=sa.text("'DRAFT'"),
        ),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            mysql_on_update=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_booking_requests_requester_id",
        "booking_requests",
        ["requester_id"],
        unique=False,
    )
    op.create_index(
        "ix_booking_requests_start_datetime",
        "booking_requests",
        ["start_datetime"],
        unique=False,
    )
    op.create_index(
        "ix_booking_requests_end_datetime",
        "booking_requests",
        ["end_datetime"],
        unique=False,
    )
    op.create_index(
        "ix_booking_requests_status",
        "booking_requests",
        ["status"],
        unique=False,
    )

    op.create_table(
        "approvals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "booking_request_id",
            sa.Integer(),
            sa.ForeignKey("booking_requests.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "approver_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False
        ),
        sa.Column(
            "approval_level",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column("decision", approval_decision_enum, nullable=False),
        sa.Column("reason", sa.String(length=500), nullable=True),
        sa.Column(
            "decided_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_approvals_booking_request_id",
        "approvals",
        ["booking_request_id"],
        unique=False,
    )
    op.create_index(
        "ix_approvals_approver_id",
        "approvals",
        ["approver_id"],
        unique=False,
    )

    op.create_table(
        "assignments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "booking_request_id",
            sa.Integer(),
            sa.ForeignKey("booking_requests.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("vehicle_id", sa.Integer(), sa.ForeignKey("vehicles.id"), nullable=False),
        sa.Column("driver_id", sa.Integer(), sa.ForeignKey("drivers.id"), nullable=False),
        sa.Column("assigned_by", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_assignments_vehicle_id", "assignments", ["vehicle_id"], unique=False
    )
    op.create_index(
        "ix_assignments_driver_id", "assignments", ["driver_id"], unique=False
    )
    op.create_index(
        "ix_assignments_assigned_by",
        "assignments",
        ["assigned_by"],
        unique=False,
    )

    op.create_table(
        "job_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "booking_request_id",
            sa.Integer(),
            sa.ForeignKey("booking_requests.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("checkin_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checkin_mileage", sa.Integer(), nullable=True),
        sa.Column("checkin_images", sa.JSON(), nullable=True),
        sa.Column("checkin_location", sa.String(length=500), nullable=True),
        sa.Column("checkout_datetime", sa.DateTime(timezone=True), nullable=True),
        sa.Column("checkout_mileage", sa.Integer(), nullable=True),
        sa.Column("checkout_images", sa.JSON(), nullable=True),
        sa.Column("checkout_location", sa.String(length=500), nullable=True),
        sa.Column(
            "fuel_cost",
            sa.DECIMAL(precision=10, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
        sa.Column(
            "toll_cost",
            sa.DECIMAL(precision=10, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
        sa.Column(
            "other_expenses",
            sa.DECIMAL(precision=10, scale=2),
            nullable=False,
            server_default=sa.text("0.00"),
        ),
        sa.Column("expense_receipts", sa.JSON(), nullable=True),
        sa.Column("incident_report", sa.Text(), nullable=True),
        sa.Column("incident_images", sa.JSON(), nullable=True),
        sa.Column(
            "status",
            job_run_status_enum,
            nullable=False,
            server_default=sa.text("'SCHEDULED'"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            mysql_on_update=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_job_runs_status", "job_runs", ["status"], unique=False)

    # Seed data for initial environment
    users_table = sa.table(
        "users",
        sa.column("id", sa.Integer()),
        sa.column("username", sa.String()),
        sa.column("email", sa.String()),
        sa.column("full_name", sa.String()),
        sa.column("department", sa.String()),
        sa.column("role", sa.String()),
        sa.column("is_active", sa.Boolean()),
        sa.column("two_fa_enabled", sa.Boolean()),
        sa.column("password_hash", sa.Text()),
    )
    op.bulk_insert(
        users_table,
        [
            {
                "id": 1,
                "username": "fleet_admin",
                "email": "fleet.admin@example.com",
                "full_name": "Fleet Administrator",
                "department": "Operations",
                "role": "fleet_admin",
                "is_active": True,
                "two_fa_enabled": False,
                "password_hash": "$2b$12$uG2cL5YqL1R9z8d7X6Vw5uJh3pQ3kVq9bb9Xx0YlKkV8VwJ4KM8Qu",
            },
            {
                "id": 2,
                "username": "operations_manager",
                "email": "operations.manager@example.com",
                "full_name": "Operations Manager",
                "department": "Operations",
                "role": "manager",
                "is_active": True,
                "two_fa_enabled": True,
                "password_hash": "$2b$12$5X8cC8eYwV8u1zQ9sE5XaO1mN8cC9dK1lD7sF5gH8jK2lM3nO4PQ.",
            },
            {
                "id": 3,
                "username": "john.requester",
                "email": "john.requester@example.com",
                "full_name": "John Requester",
                "department": "Sales",
                "role": "requester",
                "is_active": True,
                "two_fa_enabled": False,
                "password_hash": "$2b$12$D5w1uYp8nR4sL8fX2bK0ueG6sP9dT1vX0cM3nQ5rT8vW2yZ4aBDe",
            },
            {
                "id": 4,
                "username": "jane.driver",
                "email": "jane.driver@example.com",
                "full_name": "Jane Driver",
                "department": "Logistics",
                "role": "driver",
                "is_active": True,
                "two_fa_enabled": False,
                "password_hash": "$2b$12$F1aS9dL4kP7mN2vB6xC8tO3rQ5wE7uY1iL4pO6xR8tC2vB5nH7kL",
            },
            {
                "id": 5,
                "username": "auditor.user",
                "email": "auditor.user@example.com",
                "full_name": "Alicia Auditor",
                "department": "Compliance",
                "role": "auditor",
                "is_active": True,
                "two_fa_enabled": False,
                "password_hash": "$2b$12$M8nB2vC5xZ7lQ1pD4sF6tH9kL2mN5vB8cX1zL4pT7wR0yU3iO5aS",
            },
        ],
    )

    vehicles_table = sa.table(
        "vehicles",
        sa.column("id", sa.Integer()),
        sa.column("registration_number", sa.String()),
        sa.column("vehicle_type", sa.String()),
        sa.column("brand", sa.String()),
        sa.column("model", sa.String()),
        sa.column("year_manufactured", sa.Integer()),
        sa.column("seating_capacity", sa.Integer()),
        sa.column("fuel_type", sa.String()),
        sa.column("status", sa.String()),
        sa.column("current_mileage", sa.Integer()),
        sa.column("tax_expiry_date", sa.Date()),
        sa.column("insurance_expiry_date", sa.Date()),
        sa.column("inspection_expiry_date", sa.Date()),
        sa.column("notes", sa.Text()),
    )
    op.bulk_insert(
        vehicles_table,
        [
            {
                "id": 1,
                "registration_number": "B 1234 XYZ",
                "vehicle_type": "SEDAN",
                "brand": "Toyota",
                "model": "Camry",
                "year_manufactured": 2021,
                "seating_capacity": 4,
                "fuel_type": "GASOLINE",
                "status": "ACTIVE",
                "current_mileage": 35800,
                "tax_expiry_date": date(2024, 12, 31),
                "insurance_expiry_date": date(2024, 11, 30),
                "inspection_expiry_date": date(2024, 10, 31),
                "notes": "Primary executive sedan",
            },
            {
                "id": 2,
                "registration_number": "B 5678 QWE",
                "vehicle_type": "VAN",
                "brand": "Hyundai",
                "model": "Staria",
                "year_manufactured": 2022,
                "seating_capacity": 7,
                "fuel_type": "DIESEL",
                "status": "MAINTENANCE",
                "current_mileage": 22150,
                "tax_expiry_date": date(2025, 3, 31),
                "insurance_expiry_date": date(2025, 3, 31),
                "inspection_expiry_date": date(2025, 3, 31),
                "notes": "Scheduled for maintenance next week",
            },
        ],
    )

    drivers_table = sa.table(
        "drivers",
        sa.column("id", sa.Integer()),
        sa.column("employee_code", sa.String()),
        sa.column("user_id", sa.Integer()),
        sa.column("full_name", sa.String()),
        sa.column("phone_number", sa.String()),
        sa.column("license_number", sa.String()),
        sa.column("license_type", sa.String()),
        sa.column("license_expiry_date", sa.Date()),
        sa.column("status", sa.String()),
        sa.column("availability_schedule", sa.JSON()),
    )
    op.bulk_insert(
        drivers_table,
        [
            {
                "id": 1,
                "employee_code": "DRV-001",
                "user_id": 4,
                "full_name": "Jane Driver",
                "phone_number": "+62-811-0001",
                "license_number": "DL1234567",
                "license_type": "B",
                "license_expiry_date": date(2026, 5, 31),
                "status": "ACTIVE",
                "availability_schedule": {
                    "monday": {"start": "08:00", "end": "17:00", "available": True},
                    "tuesday": {
                        "start": "08:00",
                        "end": "17:00",
                        "available": True,
                    },
                    "wednesday": {
                        "start": "08:00",
                        "end": "17:00",
                        "available": True,
                    },
                    "thursday": {
                        "start": "08:00",
                        "end": "17:00",
                        "available": True,
                    },
                    "friday": {"start": "08:00", "end": "15:00", "available": True},
                },
            },
            {
                "id": 2,
                "employee_code": "DRV-002",
                "user_id": None,
                "full_name": "Mark Standby",
                "phone_number": "+62-811-0002",
                "license_number": "DL7654321",
                "license_type": "C",
                "license_expiry_date": date(2025, 8, 15),
                "status": "INACTIVE",
                "availability_schedule": None,
            },
        ],
    )

    booking_requests_table = sa.table(
        "booking_requests",
        sa.column("id", sa.Integer()),
        sa.column("requester_id", sa.Integer()),
        sa.column("department", sa.String()),
        sa.column("purpose", sa.String()),
        sa.column("passenger_count", sa.Integer()),
        sa.column("start_datetime", sa.DateTime()),
        sa.column("end_datetime", sa.DateTime()),
        sa.column("pickup_location", sa.String()),
        sa.column("dropoff_location", sa.String()),
        sa.column("vehicle_preference", sa.String()),
        sa.column("special_requirements", sa.Text()),
        sa.column("status", sa.String()),
        sa.column("submitted_at", sa.DateTime()),
    )
    op.bulk_insert(
        booking_requests_table,
        [
            {
                "id": 1,
                "requester_id": 3,
                "department": "Sales",
                "purpose": "Client meeting in downtown Jakarta",
                "passenger_count": 2,
                "start_datetime": datetime(2024, 1, 15, 9, 0, 0),
                "end_datetime": datetime(2024, 1, 15, 14, 0, 0),
                "pickup_location": "Head Office",
                "dropoff_location": "Downtown Client Office",
                "vehicle_preference": "SEDAN",
                "special_requirements": "Child seat required for VIP guest",
                "status": "COMPLETED",
                "submitted_at": datetime(2024, 1, 10, 8, 30, 0),
            },
            {
                "id": 2,
                "requester_id": 3,
                "department": "Sales",
                "purpose": "Airport pickup for visiting leadership team",
                "passenger_count": 5,
                "start_datetime": datetime(2024, 2, 5, 6, 0, 0),
                "end_datetime": datetime(2024, 2, 5, 11, 0, 0),
                "pickup_location": "Head Office",
                "dropoff_location": "Soekarno-Hatta International Airport",
                "vehicle_preference": "VAN",
                "special_requirements": "Flight GA-832 arrival monitoring",
                "status": "REQUESTED",
                "submitted_at": datetime(2024, 1, 30, 9, 15, 0),
            },
        ],
    )

    approvals_table = sa.table(
        "approvals",
        sa.column("id", sa.Integer()),
        sa.column("booking_request_id", sa.Integer()),
        sa.column("approver_id", sa.Integer()),
        sa.column("approval_level", sa.Integer()),
        sa.column("decision", sa.String()),
        sa.column("reason", sa.String()),
        sa.column("decided_at", sa.DateTime()),
    )
    op.bulk_insert(
        approvals_table,
        [
            {
                "id": 1,
                "booking_request_id": 1,
                "approver_id": 2,
                "approval_level": 1,
                "decision": "APPROVED",
                "reason": "Approved for client relationship meeting",
                "decided_at": datetime(2024, 1, 10, 9, 0, 0),
            },
            {
                "id": 2,
                "booking_request_id": 2,
                "approver_id": 2,
                "approval_level": 1,
                "decision": "APPROVED",
                "reason": "Airport transfer approved to support leadership visit",
                "decided_at": datetime(2024, 1, 30, 10, 0, 0),
            },
        ],
    )

    assignments_table = sa.table(
        "assignments",
        sa.column("id", sa.Integer()),
        sa.column("booking_request_id", sa.Integer()),
        sa.column("vehicle_id", sa.Integer()),
        sa.column("driver_id", sa.Integer()),
        sa.column("assigned_by", sa.Integer()),
        sa.column("assigned_at", sa.DateTime()),
        sa.column("notes", sa.Text()),
    )
    op.bulk_insert(
        assignments_table,
        [
            {
                "id": 1,
                "booking_request_id": 1,
                "vehicle_id": 1,
                "driver_id": 1,
                "assigned_by": 1,
                "assigned_at": datetime(2024, 1, 11, 10, 0, 0),
                "notes": "Assigned sedan with Jane Driver for VIP client visit",
            }
        ],
    )

    job_runs_table = sa.table(
        "job_runs",
        sa.column("id", sa.Integer()),
        sa.column("booking_request_id", sa.Integer()),
        sa.column("checkin_datetime", sa.DateTime()),
        sa.column("checkin_mileage", sa.Integer()),
        sa.column("checkin_images", sa.JSON()),
        sa.column("checkin_location", sa.String()),
        sa.column("checkout_datetime", sa.DateTime()),
        sa.column("checkout_mileage", sa.Integer()),
        sa.column("checkout_images", sa.JSON()),
        sa.column("checkout_location", sa.String()),
        sa.column("fuel_cost", sa.DECIMAL()),
        sa.column("toll_cost", sa.DECIMAL()),
        sa.column("other_expenses", sa.DECIMAL()),
        sa.column("expense_receipts", sa.JSON()),
        sa.column("incident_report", sa.Text()),
        sa.column("incident_images", sa.JSON()),
        sa.column("status", sa.String()),
    )
    op.bulk_insert(
        job_runs_table,
        [
            {
                "id": 1,
                "booking_request_id": 1,
                "checkin_datetime": datetime(2024, 1, 15, 8, 30, 0),
                "checkin_mileage": 35810,
                "checkin_images": [
                    "https://cdn.example.com/job-runs/1/checkin-1.jpg"
                ],
                "checkin_location": "Head Office Garage",
                "checkout_datetime": datetime(2024, 1, 15, 14, 30, 0),
                "checkout_mileage": 35940,
                "checkout_images": [
                    "https://cdn.example.com/job-runs/1/checkout-1.jpg"
                ],
                "checkout_location": "Head Office Garage",
                "fuel_cost": Decimal("45.50"),
                "toll_cost": Decimal("8.75"),
                "other_expenses": Decimal("12.00"),
                "expense_receipts": [
                    "https://cdn.example.com/job-runs/1/receipt-1.jpg"
                ],
                "incident_report": None,
                "incident_images": None,
                "status": "COMPLETED",
            }
        ],
    )


def downgrade() -> None:
    """Drop database schema for core booking system."""
    op.drop_index("ix_job_runs_status", table_name="job_runs")
    op.drop_table("job_runs")

    op.drop_index("ix_assignments_assigned_by", table_name="assignments")
    op.drop_index("ix_assignments_driver_id", table_name="assignments")
    op.drop_index("ix_assignments_vehicle_id", table_name="assignments")
    op.drop_table("assignments")

    op.drop_index("ix_approvals_approver_id", table_name="approvals")
    op.drop_index("ix_approvals_booking_request_id", table_name="approvals")
    op.drop_table("approvals")

    op.drop_index("ix_booking_requests_status", table_name="booking_requests")
    op.drop_index(
        "ix_booking_requests_end_datetime", table_name="booking_requests"
    )
    op.drop_index(
        "ix_booking_requests_start_datetime", table_name="booking_requests"
    )
    op.drop_index(
        "ix_booking_requests_requester_id", table_name="booking_requests"
    )
    op.drop_table("booking_requests")

    op.drop_index("ix_drivers_status", table_name="drivers")
    op.drop_index("ix_drivers_license_expiry_date", table_name="drivers")
    op.drop_index("ix_drivers_license_number", table_name="drivers")
    op.drop_index("ix_drivers_user_id", table_name="drivers")
    op.drop_table("drivers")

    op.drop_index("ix_vehicles_inspection_expiry_date", table_name="vehicles")
    op.drop_index("ix_vehicles_insurance_expiry_date", table_name="vehicles")
    op.drop_index("ix_vehicles_tax_expiry_date", table_name="vehicles")
    op.drop_index("ix_vehicles_status", table_name="vehicles")
    op.drop_index("ix_vehicles_vehicle_type", table_name="vehicles")
    op.drop_table("vehicles")

    op.drop_index("ix_users_role", table_name="users")
    op.drop_table("users")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        for enum_name in [
            "jobrunstatus",
            "approvaldecision",
            "vehiclepreference",
            "bookingstatus",
            "driverstatus",
            "fueltype",
            "vehiclestatus",
            "vehicletype",
            "userrole",
        ]:
            op.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}"))
