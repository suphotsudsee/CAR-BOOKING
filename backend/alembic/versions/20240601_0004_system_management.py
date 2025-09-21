"""Add system configuration and audit infrastructure"""

from __future__ import annotations

from datetime import time

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20240601_0004"
down_revision = "20240501_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "system_configurations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "maintenance_mode",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("maintenance_message", sa.String(length=255), nullable=True),
        sa.Column(
            "require_booking_approval",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("1"),
        ),
        sa.Column(
            "max_pending_bookings_per_user",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("3"),
        ),
        sa.Column(
            "max_active_bookings_per_user",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("2"),
        ),
        sa.Column(
            "auto_cancel_pending_hours",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("48"),
        ),
        sa.Column(
            "working_day_start",
            sa.Time(),
            nullable=False,
            server_default=sa.text("'08:00:00'"),
        ),
        sa.Column(
            "working_day_end",
            sa.Time(),
            nullable=False,
            server_default=sa.text("'18:00:00'"),
        ),
        sa.Column("working_days", sa.JSON(), nullable=False),
        sa.Column(
            "approval_escalation_hours",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("24"),
        ),
        sa.Column(
            "booking_lead_time_hours",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("4"),
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
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    op.create_table(
        "system_holidays",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "configuration_id",
            sa.Integer(),
            sa.ForeignKey("system_configurations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
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
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ix_system_holidays_configuration_id",
        "system_holidays",
        ["configuration_id"],
    )
    op.create_index("ix_system_holidays_date", "system_holidays", ["date"], unique=False)

    op.create_table(
        "system_working_hours",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "configuration_id",
            sa.Integer(),
            sa.ForeignKey("system_configurations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("day_of_week", sa.String(length=9), nullable=False),
        sa.Column("start_time", sa.Time(), nullable=False),
        sa.Column("end_time", sa.Time(), nullable=False),
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
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index(
        "ux_system_working_hours_config_day",
        "system_working_hours",
        ["configuration_id", "day_of_week"],
        unique=True,
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource", sa.String(length=255), nullable=False),
        sa.Column(
            "status_code",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("200"),
        ),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("context", sa.JSON(), nullable=True),
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
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.create_index("ix_audit_logs_user_id", "audit_logs", ["user_id"], unique=False)
    op.create_index(
        "ix_audit_logs_resource_created_at",
        "audit_logs",
        ["resource", "created_at"],
        unique=False,
    )

    op.create_table(
        "system_health_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("component", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column(
            "severity",
            sa.String(length=20),
            nullable=False,
            server_default=sa.text("'info'"),
        ),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("extra", sa.JSON(), nullable=True),
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
            server_onupdate=sa.text("CURRENT_TIMESTAMP"),
        ),
    )

    configuration_table = sa.table(
        "system_configurations",
        sa.column("id", sa.Integer()),
        sa.column("maintenance_mode", sa.Boolean()),
        sa.column("maintenance_message", sa.String()),
        sa.column("require_booking_approval", sa.Boolean()),
        sa.column("max_pending_bookings_per_user", sa.Integer()),
        sa.column("max_active_bookings_per_user", sa.Integer()),
        sa.column("auto_cancel_pending_hours", sa.Integer()),
        sa.column("working_day_start", sa.Time()),
        sa.column("working_day_end", sa.Time()),
        sa.column("working_days", sa.JSON()),
        sa.column("approval_escalation_hours", sa.Integer()),
        sa.column("booking_lead_time_hours", sa.Integer()),
    )
    op.bulk_insert(
        configuration_table,
        [
            {
                "id": 1,
                "maintenance_mode": False,
                "maintenance_message": None,
                "require_booking_approval": True,
                "max_pending_bookings_per_user": 3,
                "max_active_bookings_per_user": 2,
                "auto_cancel_pending_hours": 48,
                "working_day_start": time(8, 0),
                "working_day_end": time(18, 0),
                "working_days": [
                    "monday",
                    "tuesday",
                    "wednesday",
                    "thursday",
                    "friday",
                ],
                "approval_escalation_hours": 24,
                "booking_lead_time_hours": 4,
            }
        ],
    )

    working_hours_table = sa.table(
        "system_working_hours",
        sa.column("configuration_id", sa.Integer()),
        sa.column("day_of_week", sa.String()),
        sa.column("start_time", sa.Time()),
        sa.column("end_time", sa.Time()),
    )

    default_hours = [
        ("monday", time(8, 0), time(18, 0)),
        ("tuesday", time(8, 0), time(18, 0)),
        ("wednesday", time(8, 0), time(18, 0)),
        ("thursday", time(8, 0), time(18, 0)),
        ("friday", time(8, 0), time(18, 0)),
    ]
    op.bulk_insert(
        working_hours_table,
        [
            {
                "configuration_id": 1,
                "day_of_week": day,
                "start_time": start,
                "end_time": end,
            }
            for day, start, end in default_hours
        ],
    )


def downgrade() -> None:
    op.drop_table("system_health_records")
    op.drop_index("ix_audit_logs_resource_created_at", table_name="audit_logs")
    op.drop_index("ix_audit_logs_user_id", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ux_system_working_hours_config_day", table_name="system_working_hours")
    op.drop_table("system_working_hours")
    op.drop_index("ix_system_holidays_date", table_name="system_holidays")
    op.drop_index("ix_system_holidays_configuration_id", table_name="system_holidays")
    op.drop_table("system_holidays")
    op.drop_table("system_configurations")
