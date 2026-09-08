import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SituacaoJanela(str, enum.Enum):
    EM_ANDAMENTO = "em_andamento"
    CONCLUIDA = "concluida"
    FALHOU = "falhou"
    PARCIAL = "parcial"


class CombinadorCondicoes(str, enum.Enum):
    E = "e"
    OU = "ou"


class MetricaGatilho(str, enum.Enum):
    ASR_PERCENTUAL = "asr_percentual"
    ACD_SEGUNDOS = "acd_segundos"
    PDD_MEDIO_SEGUNDOS = "pdd_medio_segundos"


class PeriodoReferenciaGatilho(str, enum.Enum):
    MEDIA_ONTEM = "media_ontem"
    MEDIA_SEMANAL = "media_semanal"
    MEDIA_MENSAL = "media_mensal"


class DirecaoGatilho(str, enum.Enum):
    AUMENTO = "aumento"
    QUEDA = "queda"
    QUALQUER = "qualquer"


class SeveridadeGatilho(str, enum.Enum):
    """Ordem crescente de gravidade — usada tanto pra exibir a cor quanto pra ordenar a central de
    alertas (mais grave primeiro)."""

    ATENCAO = "atencao"
    MEDIO = "medio"
    CRITICO = "critico"
    URGENTE = "urgente"


SEVERIDADE_ORDEM = {
    SeveridadeGatilho.ATENCAO: 1,
    SeveridadeGatilho.MEDIO: 2,
    SeveridadeGatilho.CRITICO: 3,
    SeveridadeGatilho.URGENTE: 4,
}


def _enum_column(enum_cls: type[enum.Enum], name: str) -> Enum:
    """Mesmo gotcha do `situacao_janela`: sem `values_callable`, o SQLAlchemy manda o *nome* do
    membro Python (ex. "AUMENTO") pro Postgres em vez do `.value` (ex. "aumento")."""

    return Enum(enum_cls, name=name, native_enum=True, values_callable=lambda cls: [m.value for m in cls])


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
    gatilhos: Mapped[list["Gatilho"]] = relationship(back_populates="cliente")


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


class Gatilho(Base):
    """Uma regra de alerta: um conjunto de condições (combinadas por `combinador`) avaliadas a
    cada janela de coleta. `cliente_id` nulo = regra global (vale pra todo cliente); preenchido =
    regra individual daquele cliente. Globais e individuais são sempre avaliadas juntas."""

    __tablename__ = "gatilhos"
    __table_args__ = (Index("idx_gatilhos_cliente_id", "cliente_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(Text, nullable=False)
    cliente_id: Mapped[int | None] = mapped_column(ForeignKey("clientes.cliente_id"), nullable=True)
    combinador: Mapped[CombinadorCondicoes] = mapped_column(
        _enum_column(CombinadorCondicoes, "combinador_condicoes"),
        nullable=False,
        default=CombinadorCondicoes.E,
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    severidade: Mapped[SeveridadeGatilho] = mapped_column(
        _enum_column(SeveridadeGatilho, "severidade_gatilho"),
        nullable=False,
        default=SeveridadeGatilho.ATENCAO,
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    cliente: Mapped["Cliente | None"] = relationship(back_populates="gatilhos")
    condicoes: Mapped[list["CondicaoGatilho"]] = relationship(
        back_populates="gatilho", cascade="all, delete-orphan"
    )


class CondicaoGatilho(Base):
    """Uma comparação dentro de um gatilho: métrica atual vs. média de referência de um período
    anterior, variação percentual numa direção, acima de um limite."""

    __tablename__ = "condicoes_gatilho"
    __table_args__ = (Index("idx_condicoes_gatilho_gatilho_id", "gatilho_id"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    gatilho_id: Mapped[int] = mapped_column(ForeignKey("gatilhos.id", ondelete="CASCADE"), nullable=False)
    metrica: Mapped[MetricaGatilho] = mapped_column(_enum_column(MetricaGatilho, "metrica_gatilho"), nullable=False)
    periodo_referencia: Mapped[PeriodoReferenciaGatilho] = mapped_column(
        _enum_column(PeriodoReferenciaGatilho, "periodo_referencia_gatilho"), nullable=False
    )
    direcao: Mapped[DirecaoGatilho] = mapped_column(_enum_column(DirecaoGatilho, "direcao_gatilho"), nullable=False)
    percentual_limite: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    gatilho: Mapped["Gatilho"] = relationship(back_populates="condicoes")


class AlertaDisparado(Base):
    """Histórico: uma linha por disparo de um gatilho pra um cliente numa janela. `gatilho_id` não
    tem `ondelete` — apagar uma regra que já disparou fica bloqueado por FK de propósito, pra não
    perder histórico em silêncio (ver rota de exclusão de gatilho, que faz soft-delete)."""

    __tablename__ = "alertas_disparados"
    __table_args__ = (
        UniqueConstraint("gatilho_id", "janela_id", "cliente_id", name="uq_alertas_disparados_gatilho_janela_cliente"),
        Index("idx_alertas_disparados_cliente_id", "cliente_id"),
        Index("idx_alertas_disparados_disparado_em", "disparado_em"),
        Index("idx_alertas_disparados_visto", "visto"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    gatilho_id: Mapped[int] = mapped_column(ForeignKey("gatilhos.id"), nullable=False)
    cliente_id: Mapped[int] = mapped_column(ForeignKey("clientes.cliente_id"), nullable=False)
    janela_id: Mapped[int] = mapped_column(ForeignKey("janelas_coleta.id", ondelete="CASCADE"), nullable=False)
    metricas_avaliadas: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    # Cópia da severidade do gatilho no momento do disparo — não muda se a regra for editada
    # depois, pra o histórico continuar refletindo o que era grave naquela hora.
    severidade: Mapped[SeveridadeGatilho] = mapped_column(
        _enum_column(SeveridadeGatilho, "severidade_gatilho"), nullable=False
    )
    disparado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    visto: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    visto_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    gatilho: Mapped["Gatilho"] = relationship()
    cliente: Mapped["Cliente"] = relationship()
    janela: Mapped["Janela"] = relationship()
