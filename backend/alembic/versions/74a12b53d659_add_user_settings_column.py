"""add_user_settings_column

Revision ID: 74a12b53d659
Revises: 8c042065f1ae
Create Date: 2026-07-13 22:17:52.828783

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '74a12b53d659'
down_revision: Union[str, Sequence[str], None] = '8c042065f1ae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("settings", sa.JSON(), nullable=True))
    op.add_column("users", sa.Column("token_version", sa.Integer(), nullable=False, server_default=sa.text("1")))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("users", "token_version")
    op.drop_column("users", "settings")
