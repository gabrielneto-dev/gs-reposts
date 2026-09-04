import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class WindowStatus(str, enum.Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


class Client(Base):
    """Dimensão simples: um cliente NextRouter (`customer_id`), visto em pelo menos uma janela."""

    __tablename__ = "clients"

    cliente_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str | None] = mapped_column(Text)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    metrics: Mapped[list["ClientMetric"]] = relationship(back_populates="client")


class CollectionWindow(Base):
    """Uma execução do scheduler: a janela de tempo processada e o resultado do job."""

    __tablename__ = "collection_windows"
    __table_args__ = (UniqueConstraint("window_start", "window_end", name="uq_collection_windows_range"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    discovery_sample_limit: Mapped[int] = mapped_column(Integer, nullable=False)
    clients_discovered: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clients_processed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[WindowStatus] = mapped_column(
        Enum(WindowStatus, name="window_status", native_enum=True, values_callable=lambda enum_cls: [member.value for member in enum_cls]),
        nullable=False,
        default=WindowStatus.RUNNING,
    )
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    metrics: Mapped[list["ClientMetric"]] = relationship(back_populates="window", cascade="all, delete-orphan")


class ClientMetric(Base):
    """ASR/ACD/PDD exatos de um cliente numa janela coletada."""

    __tablename__ = "client_metrics"
    __table_args__ = (
        UniqueConstraint("cliente_id", "window_start", "window_end", name="uq_client_metrics_cliente_janela"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    window_id: Mapped[int] = mapped_column(ForeignKey("collection_windows.id", ondelete="CASCADE"), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clients.cliente_id"), nullable=False)

    total_atendidas: Mapped[int] = mapped_column(Integer, nullable=False)
    total_falhas: Mapped[int] = mapped_column(Integer, nullable=False)
    asr_percentual: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    acd_segundos: Mapped[float | None] = mapped_column(Numeric(10, 2))
    pdd_medio_segundos: Mapped[float | None] = mapped_column(Numeric(10, 3))
    occurrences_discovery: Mapped[int] = mapped_column(Integer, nullable=False)
    truncado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    window: Mapped["CollectionWindow"] = relationship(back_populates="metrics")
    client: Mapped["Client"] = relationship(back_populates="metrics")
