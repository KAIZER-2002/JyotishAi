"""add_user_profile_fields

Revision ID: 8c042065f1ae
Revises: 6486952f45e4
Create Date: 2026-07-13 22:00:35.809209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8c042065f1ae'
down_revision: Union[str, Sequence[str], None] = '6486952f45e4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("timezone", sa.String(length=64), nullable=True))
    op.add_column("users", sa.Column("date_of_birth", sa.Date(), nullable=True))
    op.add_column("users", sa.Column("time_of_birth", sa.String(length=8), nullable=True))
    op.add_column("users", sa.Column("birth_place", sa.String(length=200), nullable=True))
    op.add_column("users", sa.Column("latitude", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("longitude", sa.Float(), nullable=True))
    op.add_column("users", sa.Column("ayanamsa", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("avatar_url", sa.String(length=2048), nullable=True))
    op.add_column("users", sa.Column("gender", sa.String(length=20), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "gender")
    op.drop_column("users", "avatar_url")
    op.drop_column("users", "ayanamsa")
    op.drop_column("users", "longitude")
    op.drop_column("users", "latitude")
    op.drop_column("users", "birth_place")
    op.drop_column("users", "time_of_birth")
    op.drop_column("users", "date_of_birth")
    op.drop_column("users", "timezone")
