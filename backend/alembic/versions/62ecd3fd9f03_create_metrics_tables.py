"""create metrics tables

Revision ID: 62ecd3fd9f03
Revises:
Create Date: 2026-09-04 17:05:56.838450

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '62ecd3fd9f03'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "clients",
        sa.Column("cliente_id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.Text(), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    window_status_type = postgresql.ENUM("running", "completed", "failed", "partial", name="window_status")
    window_status_type.create(op.get_bind(), checkfirst=True)
    window_status_column = postgresql.ENUM(
        "running", "completed", "failed", "partial", name="window_status", create_type=False
    )

    op.create_table(
        "collection_windows",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("discovery_sample_limit", sa.Integer(), nullable=False),
        sa.Column("clients_discovered", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("clients_processed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", window_status_column, nullable=False, server_default="running"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("window_start", "window_end", name="uq_collection_windows_range"),
    )

    op.create_table(
        "client_metrics",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column(
            "window_id",
            sa.BigInteger(),
            sa.ForeignKey("collection_windows.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("cliente_id", sa.Integer(), sa.ForeignKey("clients.cliente_id"), nullable=False),
        sa.Column("total_atendidas", sa.Integer(), nullable=False),
        sa.Column("total_falhas", sa.Integer(), nullable=False),
        sa.Column("asr_percentual", sa.Numeric(5, 2), nullable=False),
        sa.Column("acd_segundos", sa.Numeric(10, 2), nullable=True),
        sa.Column("pdd_medio_segundos", sa.Numeric(10, 3), nullable=True),
        sa.Column("occurrences_discovery", sa.Integer(), nullable=False),
        sa.Column("truncado", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("cliente_id", "window_start", "window_end", name="uq_client_metrics_cliente_janela"),
    )
    op.create_index("idx_client_metrics_cliente_janela", "client_metrics", ["cliente_id", "window_start"])
    op.create_index("idx_client_metrics_janela", "client_metrics", ["window_start"])


def downgrade() -> None:
    op.drop_index("idx_client_metrics_janela", table_name="client_metrics")
    op.drop_index("idx_client_metrics_cliente_janela", table_name="client_metrics")
    op.drop_table("client_metrics")
    op.drop_table("collection_windows")
    op.drop_table("clients")
    postgresql.ENUM(name="window_status").drop(op.get_bind(), checkfirst=True)
