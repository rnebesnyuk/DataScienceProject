"""parking edit2

Revision ID: 65db85ccd773
Revises: 41e9fa337909
Create Date: 2024-08-25 19:14:56.186210

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '65db85ccd773'
down_revision: Union[str, None] = '41e9fa337909'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('parking_lot', sa.Column('license_plate', sa.String(length=20), nullable=False))
    op.create_index(op.f('ix_parking_lot_license_plate'), 'parking_lot', ['license_plate'], unique=True)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_parking_lot_license_plate'), table_name='parking_lot')
    op.drop_column('parking_lot', 'license_plate')
    # ### end Alembic commands ###
