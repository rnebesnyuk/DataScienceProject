"""Add ParkingLot

Revision ID: 80c2f2b2ed37
Revises: 12f3ae017524
Create Date: 2024-08-19 22:57:24.102133

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '80c2f2b2ed37'
down_revision: Union[str, None] = '12f3ae017524'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
