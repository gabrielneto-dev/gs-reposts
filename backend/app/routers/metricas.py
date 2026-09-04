from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.config import settings
from app.db.base import get_session
from app.db.models import Client, ClientMetric, CollectionWindow, WindowStatus
from app.schemas.metricas import ClienteMetricasResponse, JanelaColeta, JanelasResponse, MetricaJanela

router = APIRouter(prefix="/api/metricas", tags=["Métricas"])

MAX_REGISTROS = 2000


def _inicio_do_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.min, tzinfo=ZoneInfo(settings.scheduler_timezone))


@router.get("/clientes/{cliente_id}", response_model=ClienteMetricasResponse)
async def historico_cliente(
    cliente_id: int,
    data_inicio: date | None = Query(None, description="Só janelas com início >= essa data"),
    data_fim: date | None = Query(None, description="Só janelas com início <= essa data (dia inteiro)"),
    limit: int = Query(500, ge=1, le=MAX_REGISTROS, description="Máximo de janelas retornadas"),
) -> ClienteMetricasResponse:
    """ASR/ACD/PDD exatos de UM cliente, por janela já coletada pelo scheduler — vem do banco
    próprio do backend (`metrics-pipeline`), não faz nenhuma chamada ao softswitch. Ordenado do
    mais antigo pro mais recente (pronto pra plotar como série temporal)."""

    async with get_session() as session:
        cliente = await session.get(Client, cliente_id)
        if cliente is None:
            raise HTTPException(404, f"Cliente {cliente_id} não tem nenhuma coleta registrada")

        stmt = select(ClientMetric).where(ClientMetric.cliente_id == cliente_id)
        if data_inicio is not None:
            stmt = stmt.where(ClientMetric.window_start >= _inicio_do_dia(data_inicio))
        if data_fim is not None:
            stmt = stmt.where(ClientMetric.window_start < _inicio_do_dia(data_fim + timedelta(days=1)))
        stmt = stmt.order_by(ClientMetric.window_start.asc()).limit(limit + 1)

        linhas = (await session.execute(stmt)).scalars().all()

    truncado = len(linhas) > limit
    linhas = linhas[:limit]

    return ClienteMetricasResponse(
        cliente_id=cliente_id,
        nome=cliente.nome,
        registros=len(linhas),
        metricas=[MetricaJanela.model_validate(linha) for linha in linhas],
        aviso=(
            f"Mais de {limit} janelas no período — resultado truncado no mais antigo. "
            "Estreite data_inicio/data_fim ou aumente `limit`."
            if truncado
            else None
        ),
    )


@router.get("/janelas", response_model=JanelasResponse)
async def listar_janelas(
    status: WindowStatus | None = Query(None, description="Filtra por status da coleta"),
    data_inicio: date | None = Query(None, description="Só janelas com início >= essa data"),
    data_fim: date | None = Query(None, description="Só janelas com início <= essa data (dia inteiro)"),
    limit: int = Query(100, ge=1, le=MAX_REGISTROS, description="Máximo de janelas retornadas"),
) -> JanelasResponse:
    """Histórico de execuções do scheduler (não os dados de cliente em si) — pra acompanhar se as
    coletas estão rodando e se alguma ficou `partial`/`failed`. Ordenado do mais recente pro mais
    antigo."""

    async with get_session() as session:
        stmt = select(CollectionWindow)
        if status is not None:
            stmt = stmt.where(CollectionWindow.status == status)
        if data_inicio is not None:
            stmt = stmt.where(CollectionWindow.window_start >= _inicio_do_dia(data_inicio))
        if data_fim is not None:
            stmt = stmt.where(CollectionWindow.window_start < _inicio_do_dia(data_fim + timedelta(days=1)))
        stmt = stmt.order_by(CollectionWindow.window_start.desc()).limit(limit)

        linhas = (await session.execute(stmt)).scalars().all()

    return JanelasResponse(
        registros=len(linhas),
        janelas=[JanelaColeta.model_validate(linha) for linha in linhas],
    )
