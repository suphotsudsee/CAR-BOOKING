"""Add email notification tracking table"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20240501_0003"
down_revision = "20240401_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    email_status_enum = sa.Enum(
        "PENDING",
        "SENDING",
        "SENT",
        "RETRYING",
        "FAILED",
        name="email_delivery_status",
    )

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        email_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "email_notifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("to_email", sa.String(length=320), nullable=False),
        sa.Column("cc", sa.JSON(), nullable=True),
        sa.Column("bcc", sa.JSON(), nullable=True),
        sa.Column("reply_to", sa.String(length=320), nullable=True),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("template_name", sa.String(length=255), nullable=False),
        sa.Column("context", sa.JSON(), nullable=False),
        sa.Column("status", email_status_enum, nullable=False, server_default="PENDING"),
        sa.Column("message_id", sa.String(length=255), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "attempt_count",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
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
        "ix_email_notifications_status",
        "email_notifications",
        ["status"],
        unique=False,
    )
    op.create_index(
        "ix_email_notifications_created_at",
        "email_notifications",
        ["created_at"],
        unique=False,
    )
    op.create_index(
        "ix_email_notifications_message_id",
        "email_notifications",
        ["message_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_email_notifications_message_id", table_name="email_notifications")
    op.drop_index("ix_email_notifications_created_at", table_name="email_notifications")
    op.drop_index("ix_email_notifications_status", table_name="email_notifications")
    op.drop_table("email_notifications")

    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        email_status_enum = sa.Enum(name="email_delivery_status")
        email_status_enum.drop(bind, checkfirst=True)