"""Create TopTenUG evidence-first core domain.

Revision ID: 0001_core_domain
Revises:
"""
from alembic import op

from app.domain.models import Base
import app.domain.models  # noqa: F401

revision = "0001_core_domain"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
