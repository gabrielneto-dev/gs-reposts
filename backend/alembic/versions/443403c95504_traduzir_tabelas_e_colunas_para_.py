"""traduzir tabelas e colunas para portugues

Revision ID: 443403c95504
Revises: 62ecd3fd9f03
Create Date: 2026-09-08 09:39:03.471085

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '443403c95504'
down_revision: Union[str, None] = '62ecd3fd9f03'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enum: renomeia o tipo e cada valor
    op.execute("ALTER TYPE window_status RENAME TO situacao_janela")
    op.execute("ALTER TYPE situacao_janela RENAME VALUE 'running' TO 'em_andamento'")
    op.execute("ALTER TYPE situacao_janela RENAME VALUE 'completed' TO 'concluida'")
    op.execute("ALTER TYPE situacao_janela RENAME VALUE 'failed' TO 'falhou'")
    op.execute("ALTER TYPE situacao_janela RENAME VALUE 'partial' TO 'parcial'")

    # clients -> clientes
    op.rename_table("clients", "clientes")
    op.alter_column("clientes", "first_seen_at", new_column_name="visto_pela_primeira_vez_em")
    op.alter_column("clientes", "last_seen_at", new_column_name="visto_pela_ultima_vez_em")
    op.alter_column("clientes", "updated_at", new_column_name="atualizado_em")

    # collection_windows -> janelas_coleta
    op.rename_table("collection_windows", "janelas_coleta")
    op.alter_column("janelas_coleta", "window_start", new_column_name="inicio_janela")
    op.alter_column("janelas_coleta", "window_end", new_column_name="fim_janela")
    op.alter_column("janelas_coleta", "discovery_sample_limit", new_column_name="limite_amostra_descoberta")
    op.alter_column("janelas_coleta", "clients_discovered", new_column_name="clientes_descobertos")
    op.alter_column("janelas_coleta", "clients_processed", new_column_name="clientes_processados")
    op.alter_column("janelas_coleta", "status", new_column_name="situacao")
    op.alter_column("janelas_coleta", "error_message", new_column_name="mensagem_erro")
    op.alter_column("janelas_coleta", "started_at", new_column_name="iniciado_em")
    op.alter_column("janelas_coleta", "finished_at", new_column_name="finalizado_em")
    op.execute(
        "ALTER TABLE janelas_coleta RENAME CONSTRAINT uq_collection_windows_range TO uq_janelas_coleta_intervalo"
    )

    # client_metrics -> metricas_cliente
    op.rename_table("client_metrics", "metricas_cliente")
    op.alter_column("metricas_cliente", "window_id", new_column_name="janela_id")
    op.alter_column("metricas_cliente", "window_start", new_column_name="inicio_janela")
    op.alter_column("metricas_cliente", "window_end", new_column_name="fim_janela")
    op.alter_column("metricas_cliente", "occurrences_discovery", new_column_name="ocorrencias_descoberta")
    op.alter_column("metricas_cliente", "created_at", new_column_name="criado_em")
    op.execute(
        "ALTER TABLE metricas_cliente RENAME CONSTRAINT uq_client_metrics_cliente_janela TO uq_metricas_cliente_janela"
    )
    op.execute("ALTER INDEX idx_client_metrics_cliente_janela RENAME TO idx_metricas_cliente_cliente_janela")
    op.execute("ALTER INDEX idx_client_metrics_janela RENAME TO idx_metricas_cliente_janela")


def downgrade() -> None:
    op.execute("ALTER INDEX idx_metricas_cliente_janela RENAME TO idx_client_metrics_janela")
    op.execute("ALTER INDEX idx_metricas_cliente_cliente_janela RENAME TO idx_client_metrics_cliente_janela")
    op.execute(
        "ALTER TABLE metricas_cliente RENAME CONSTRAINT uq_metricas_cliente_janela TO uq_client_metrics_cliente_janela"
    )
    op.alter_column("metricas_cliente", "criado_em", new_column_name="created_at")
    op.alter_column("metricas_cliente", "ocorrencias_descoberta", new_column_name="occurrences_discovery")
    op.alter_column("metricas_cliente", "fim_janela", new_column_name="window_end")
    op.alter_column("metricas_cliente", "inicio_janela", new_column_name="window_start")
    op.alter_column("metricas_cliente", "janela_id", new_column_name="window_id")
    op.rename_table("metricas_cliente", "client_metrics")

    op.execute(
        "ALTER TABLE janelas_coleta RENAME CONSTRAINT uq_janelas_coleta_intervalo TO uq_collection_windows_range"
    )
    op.alter_column("janelas_coleta", "finalizado_em", new_column_name="finished_at")
    op.alter_column("janelas_coleta", "iniciado_em", new_column_name="started_at")
    op.alter_column("janelas_coleta", "mensagem_erro", new_column_name="error_message")
    op.alter_column("janelas_coleta", "situacao", new_column_name="status")
    op.alter_column("janelas_coleta", "clientes_processados", new_column_name="clients_processed")
    op.alter_column("janelas_coleta", "clientes_descobertos", new_column_name="clients_discovered")
    op.alter_column("janelas_coleta", "limite_amostra_descoberta", new_column_name="discovery_sample_limit")
    op.alter_column("janelas_coleta", "fim_janela", new_column_name="window_end")
    op.alter_column("janelas_coleta", "inicio_janela", new_column_name="window_start")
    op.rename_table("janelas_coleta", "collection_windows")

    op.alter_column("clientes", "atualizado_em", new_column_name="updated_at")
    op.alter_column("clientes", "visto_pela_ultima_vez_em", new_column_name="last_seen_at")
    op.alter_column("clientes", "visto_pela_primeira_vez_em", new_column_name="first_seen_at")
    op.rename_table("clientes", "clients")

    op.execute("ALTER TYPE situacao_janela RENAME VALUE 'em_andamento' TO 'running'")
    op.execute("ALTER TYPE situacao_janela RENAME VALUE 'concluida' TO 'completed'")
    op.execute("ALTER TYPE situacao_janela RENAME VALUE 'falhou' TO 'failed'")
    op.execute("ALTER TYPE situacao_janela RENAME VALUE 'parcial' TO 'partial'")
    op.execute("ALTER TYPE situacao_janela RENAME TO window_status")
