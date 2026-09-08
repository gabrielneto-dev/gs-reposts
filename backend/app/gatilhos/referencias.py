from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import MetricaCliente, PeriodoReferenciaGatilho

_DIAS_DO_PERIODO = {
    PeriodoReferenciaGatilho.MEDIA_ONTEM: 1,
    PeriodoReferenciaGatilho.MEDIA_SEMANAL: 7,
    PeriodoReferenciaGatilho.MEDIA_MENSAL: 30,
}


@dataclass
class MediaReferencia:
    """Média de um cliente num período de referência. `amostras == 0` significa "sem histórico
    suficiente" — quem consome isso nunca deve tratar `None` como zero."""

    asr_percentual: float | None
    acd_segundos: float | None
    pdd_medio_segundos: float | None
    amostras: int


def _intervalo_do_periodo(
    periodo: PeriodoReferenciaGatilho, agora: datetime, tz: ZoneInfo
) -> tuple[datetime, datetime]:
    """Janela móvel terminando ontem (exclusive de hoje, que ainda está em andamento):
    - média de ontem: só o dia calendário anterior completo
    - média semanal/mensal: últimos 7/30 dias corridos terminando ontem
    Escolhido deliberadamente em vez de calendário fixo (semana/mês) pra sempre ter uma base de
    comparação, mesmo na segunda-feira ou no dia 1º do mês.

    `agora` sempre chega com tzinfo UTC (é o que o asyncpg devolve pra uma coluna timestamptz,
    não importa em que fuso o valor foi originalmente gravado) — por isso convertemos pro fuso
    operacional antes de calcular o limite do dia; comparar datetimes aware com fusos diferentes
    funciona (Python compara o instante absoluto), mas *qual* dia é "hoje" depende do fuso certo."""

    inicio_hoje = datetime.combine(agora.astimezone(tz).date(), time.min, tzinfo=tz)
    dias = _DIAS_DO_PERIODO[periodo]
    return inicio_hoje - timedelta(days=dias), inicio_hoje


async def calcular_medias_referencia(
    session: AsyncSession,
    periodo: PeriodoReferenciaGatilho,
    cliente_ids: set[int],
    agora: datetime,
) -> dict[int, MediaReferencia]:
    """Uma consulta agregada por período (não uma por cliente/condição) — evita N+1 quando várias
    condições de vários clientes usam o mesmo período de referência na mesma avaliação."""

    if not cliente_ids:
        return {}

    inicio, fim = _intervalo_do_periodo(periodo, agora, ZoneInfo(settings.scheduler_timezone))

    stmt = (
        select(
            MetricaCliente.cliente_id,
            func.avg(MetricaCliente.asr_percentual).label("asr"),
            func.avg(MetricaCliente.acd_segundos).label("acd"),
            func.avg(MetricaCliente.pdd_medio_segundos).label("pdd"),
            func.count().label("amostras"),
        )
        .where(
            MetricaCliente.cliente_id.in_(cliente_ids),
            MetricaCliente.inicio_janela >= inicio,
            MetricaCliente.inicio_janela < fim,
        )
        .group_by(MetricaCliente.cliente_id)
    )

    linhas = (await session.execute(stmt)).all()

    return {
        linha.cliente_id: MediaReferencia(
            asr_percentual=float(linha.asr) if linha.asr is not None else None,
            acd_segundos=float(linha.acd) if linha.acd is not None else None,
            pdd_medio_segundos=float(linha.pdd) if linha.pdd is not None else None,
            amostras=linha.amostras,
        )
        for linha in linhas
    }
