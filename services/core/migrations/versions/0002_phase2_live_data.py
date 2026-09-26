"""Add Phase 2 live-data candidate and ranking-run state.

Revision ID: 0002_phase2_live_data
Revises: 0001_core_domain
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

from app.domain.models import CandidateRecord

revision = "0002_phase2_live_data"
down_revision = "0001_core_domain"
branch_labels = None
depends_on = None


def _ranking_run_columns() -> set[str]:
    return {column["name"] for column in inspect(op.get_bind()).get_columns("ranking_runs")}


def upgrade() -> None:
    bind = op.get_bind()

    # Existing MVP databases already have the PostgreSQL enum without PROVISIONAL.
    # Fresh databases may receive the current enum through the legacy 0001 metadata
    # bootstrap, so this statement must be idempotent.
    op.execute("ALTER TYPE rankingrunstatus ADD VALUE IF NOT EXISTS 'PROVISIONAL'")

    CandidateRecord.__table__.create(bind=bind, checkfirst=True)

    columns = _ranking_run_columns()
    if "cutoff_at" not in columns:
        op.add_column("ranking_runs", sa.Column("cutoff_at", sa.DateTime(timezone=True), nullable=True))
    if "candidate_count" not in columns:
        op.add_column(
            "ranking_runs",
            sa.Column("candidate_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        )
    if "validation_details" not in columns:
        op.add_column(
            "ranking_runs",
            sa.Column(
                "validation_details",
                sa.JSON(),
                server_default=sa.text("'{}'::json"),
                nullable=False,
            ),
        )

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade() -> None:
    bind = op.get_bind()
    CandidateRecord.__table__.drop(bind=bind, checkfirst=True)

    columns = _ranking_run_columns()
    if "validation_details" in columns:
        op.drop_column("ranking_runs", "validation_details")
    if "candidate_count" in columns:
        op.drop_column("ranking_runs", "candidate_count")
    if "cutoff_at" in columns:
        op.drop_column("ranking_runs", "cutoff_at")

    # PostgreSQL enum-value removal requires rebuilding the enum type and can break
    # rows using newer values. Leave PROVISIONAL available on downgrade; the 0001
    # application model does not depend on the value being absent.
    # The vector extension is also intentionally retained because it may be shared.
