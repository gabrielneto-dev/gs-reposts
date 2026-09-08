"""create gatilhos tables

Revision ID: fa5834948681
Revises: 443403c95504
Create Date: 2026-09-08 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'fa5834948681'
down_revision: Union[str, None] = '443403c95504'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    combinador_type = postgresql.ENUM("e", "ou", name="combinador_condicoes")
    combinador_type.create(op.get_bind(), checkfirst=True)
    combinador_column = postgresql.ENUM("e", "ou", name="combinador_condicoes", create_type=False)

    metrica_type = postgresql.ENUM(
        "asr_percentual", "acd_segundos", "pdd_medio_segundos", name="metrica_gatilho"
    )
    metrica_type.create(op.get_bind(), checkfirst=True)
    metrica_column = postgresql.ENUM(
        "asr_percentual", "acd_segundos", "pdd_medio_segundos", name="metrica_gatilho", create_type=False
    )

    periodo_type = postgresql.ENUM(
        "media_ontem", "media_semanal", "media_mensal", name="periodo_referencia_gatilho"
    )
    periodo_type.create(op.get_bind(), checkfirst=True)
    periodo_column = postgresql.ENUM(
        "media_ontem", "media_semanal", "media_mensal", name="periodo_referencia_gatilho", create_type=False
    )

    direcao_type = postgresql.ENUM("aumento", "queda", "qualquer", name="direcao_gatilho")
    direcao_type.create(op.get_bind(), checkfirst=True)
    direcao_column = postgresql.ENUM("aumento", "queda", "qualquer", name="direcao_gatilho", create_type=False)

    op.create_table(
        "gatilhos",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("nome", sa.Text(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.cliente_id"), nullable=True),
        sa.Column("combinador", combinador_column, nullable=False, server_default="e"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "atualizado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("idx_gatilhos_cliente_id", "gatilhos", ["cliente_id"])

    op.create_table(
        "condicoes_gatilho",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("gatilho_id", sa.BigInteger(), sa.ForeignKey("gatilhos.id", ondelete="CASCADE"), nullable=False),
        sa.Column("metrica", metrica_column, nullable=False),
        sa.Column("periodo_referencia", periodo_column, nullable=False),
        sa.Column("direcao", direcao_column, nullable=False),
        sa.Column("percentual_limite", sa.Numeric(6, 2), nullable=False),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_condicoes_gatilho_gatilho_id", "condicoes_gatilho", ["gatilho_id"])

    op.create_table(
        "alertas_disparados",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("gatilho_id", sa.BigInteger(), sa.ForeignKey("gatilhos.id"), nullable=False),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clientes.cliente_id"), nullable=False),
        sa.Column(
            "janela_id", sa.BigInteger(), sa.ForeignKey("janelas_coleta.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("metricas_avaliadas", postgresql.JSONB(), nullable=False),
        sa.Column("disparado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint(
            "gatilho_id", "janela_id", "cliente_id", name="uq_alertas_disparados_gatilho_janela_cliente"
        ),
    )
    op.create_index("idx_alertas_disparados_cliente_id", "alertas_disparados", ["cliente_id"])
    op.create_index("idx_alertas_disparados_disparado_em", "alertas_disparados", ["disparado_em"])


def downgrade() -> None:
    op.drop_index("idx_alertas_disparados_disparado_em", table_name="alertas_disparados")
    op.drop_index("idx_alertas_disparados_cliente_id", table_name="alertas_disparados")
    op.drop_table("alertas_disparados")

    op.drop_index("idx_condicoes_gatilho_gatilho_id", table_name="condicoes_gatilho")
    op.drop_table("condicoes_gatilho")

    op.drop_index("idx_gatilhos_cliente_id", table_name="gatilhos")
    op.drop_table("gatilhos")

    postgresql.ENUM(name="direcao_gatilho").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="periodo_referencia_gatilho").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="metrica_gatilho").drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(name="combinador_condicoes").drop(op.get_bind(), checkfirst=True)
