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


class SituacaoJanela(str, enum.Enum):
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    FALHOU = "falhou"
    PARCIAL = "parcial"


class Cliente(Base):
    """Dimensão simples: um cliente NextRouter (`customer_id`), visto em pelo menos uma janela."""

    __tablename__ = "clientes"

    cliente_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nome: Mapped[str | None] = mapped_column(Text)
    visto_pela_primeira_vez_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    visto_pela_ultima_vez_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    metricas: Mapped[list["MetricaCliente"]] = relationship(back_populates="cliente")


class Janela(Base):
    """Uma execução do scheduler: a janela de tempo processada e o resultado do job."""

    __tablename__ = "janelas_coleta"
    __table_args__ = (UniqueConstraint("inicio_janela", "fim_janela", name="uq_janelas_coleta_intervalo"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    inicio_janela: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fim_janela: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    limite_amostra_descoberta: Mapped[int] = mapped_column(Integer, nullable=False)
    clientes_descobertos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    clientes_processados: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    situacao: Mapped[SituacaoJanela] = mapped_column(
        Enum(
            SituacaoJanela,
            name="situacao_janela",
            native_enum=True,
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=SituacaoJanela.EM_ANDAMENTO,
    )
    mensagem_erro: Mapped[str | None] = mapped_column(Text)
    iniciado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finalizado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    metricas: Mapped[list["MetricaCliente"]] = relationship(back_populates="janela", cascade="all, delete-orphan")


class MetricaCliente(Base):
    """ASR/ACD/PDD exatos de um cliente numa janela coletada."""

    __tablename__ = "metricas_cliente"
    __table_args__ = (
        UniqueConstraint("cliente_id", "inicio_janela", "fim_janela", name="uq_metricas_cliente_janela"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    janela_id: Mapped[int] = mapped_column(ForeignKey("janelas_coleta.id", ondelete="CASCADE"), nullable=False)
    inicio_janela: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fim_janela: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.cliente_id"), nullable=False)

    total_atendidas: Mapped[int] = mapped_column(Integer, nullable=False)
    total_falhas: Mapped[int] = mapped_column(Integer, nullable=False)
    asr_percentual: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    acd_segundos: Mapped[float | None] = mapped_column(Numeric(10, 2))
    pdd_medio_segundos: Mapped[float | None] = mapped_column(Numeric(10, 3))
    ocorrencias_descoberta: Mapped[int] = mapped_column(Integer, nullable=False)
    truncado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    janela: Mapped["Janela"] = relationship(back_populates="metricas")
    cliente: Mapped["Cliente"] = relationship(back_populates="metricas")
