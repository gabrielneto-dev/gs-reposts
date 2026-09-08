"""add severidade to gatilhos and alertas_disparados

Revision ID: 59162df51080
Revises: edcd9ca68242
Create Date: 2026-09-08 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '59162df51080'
down_revision: Union[str, None] = 'edcd9ca68242'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    severidade_type = postgresql.ENUM(
        "atencao", "medio", "critico", "urgente", name="severidade_gatilho"
    )
    severidade_type.create(op.get_bind(), checkfirst=True)
    severidade_column = postgresql.ENUM(
        "atencao", "medio", "critico", "urgente", name="severidade_gatilho", create_type=False
    )

    op.add_column(
        "gatilhos",
        sa.Column("severidade", severidade_column, nullable=False, server_default="atencao"),
    )
    op.add_column(
        "alertas_disparados",
        sa.Column("severidade", severidade_column, nullable=False, server_default="atencao"),
    )


def downgrade() -> None:
    op.drop_column("alertas_disparados", "severidade")
    op.drop_column("gatilhos", "severidade")
    postgresql.ENUM(name="severidade_gatilho").drop(op.get_bind(), checkfirst=True)
