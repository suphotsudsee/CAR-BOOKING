"""Add expense workflow metadata to job runs"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20240401_0002"
down_revision = "20240219_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("job_runs") as batch_op:
        batch_op.add_column(
            sa.Column(
                "expense_status",
                sa.String(length=32),
                nullable=False,
                server_default="NOT_SUBMITTED",
            )
        )
        batch_op.add_column(
            sa.Column("expense_reviewed_by_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("expense_reviewed_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(sa.Column("expense_review_notes", sa.Text(), nullable=True))
        batch_op.create_index(
            "ix_job_runs_expense_status", ["expense_status"], unique=False
        )
        batch_op.create_index(
            "ix_job_runs_expense_reviewed_by_id",
            ["expense_reviewed_by_id"],
            unique=False,
        )
        batch_op.create_foreign_key(
            "fk_job_runs_expense_reviewed_by_id_users",
            "users",
            ["expense_reviewed_by_id"],
            ["id"],
            ondelete="SET NULL",
        )

    op.execute(
        "UPDATE job_runs SET expense_status='PENDING_REVIEW' WHERE status='COMPLETED'"
    )
    op.execute(
        "UPDATE job_runs SET expense_status='NOT_SUBMITTED' WHERE expense_status IS NULL"
    )

    with op.batch_alter_table("job_runs") as batch_op:
        batch_op.alter_column("expense_status", server_default=None)


def downgrade() -> None:
    with op.batch_alter_table("job_runs") as batch_op:
        batch_op.drop_constraint(
            "fk_job_runs_expense_reviewed_by_id_users", type_="foreignkey"
        )
        batch_op.drop_index("ix_job_runs_expense_reviewed_by_id")
        batch_op.drop_index("ix_job_runs_expense_status")
        batch_op.drop_column("expense_review_notes")
        batch_op.drop_column("expense_reviewed_at")
        batch_op.drop_column("expense_reviewed_by_id")
        batch_op.drop_column("expense_status")
