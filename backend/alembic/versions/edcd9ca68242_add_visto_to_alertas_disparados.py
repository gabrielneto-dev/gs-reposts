"""add visto to alertas_disparados

Revision ID: edcd9ca68242
Revises: fa5834948681
Create Date: 2026-09-08 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'edcd9ca68242'
down_revision: Union[str, None] = 'fa5834948681'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "alertas_disparados",
        sa.Column("visto", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column(
        "alertas_disparados",
        sa.Column("visto_em", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_alertas_disparados_visto", "alertas_disparados", ["visto"])


def downgrade() -> None:
    op.drop_index("idx_alertas_disparados_visto", table_name="alertas_disparados")
    op.drop_column("alertas_disparados", "visto_em")
    op.drop_column("alertas_disparados", "visto")
