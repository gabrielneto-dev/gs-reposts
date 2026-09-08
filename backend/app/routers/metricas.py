from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.config import settings
from app.db.base import get_session
from app.db.models import Cliente, Janela, MetricaCliente, SituacaoJanela
from app.schemas.metricas import (
    ClienteMetricasResponse,
    ClienteResumo,
    ClientesResumoResponse,
    JanelaColeta,
    JanelasResponse,
    MetricaJanela,
)

router = APIRouter(prefix="/api/metricas", tags=["Métricas"])

MAX_REGISTROS = 2000


def _inicio_do_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.min, tzinfo=ZoneInfo(settings.scheduler_timezone))


@router.get("/clientes", response_model=ClientesResumoResponse)
async def resumo_clientes(
    limit: int = Query(200, ge=1, le=MAX_REGISTROS, description="Máximo de clientes retornados"),
) -> ClientesResumoResponse:
    """Um cliente por linha: ASR/ACD/PDD da janela mais recente já coletada pelo scheduler, mais
    `volume_dia` (chamadas somadas de todas as janelas coletadas HOJE — não só a última janela).
    Não faz nenhuma chamada ao softswitch. Só aparecem clientes com pelo menos uma coleta feita.
    Ordenado por nome."""

    hoje = datetime.now(ZoneInfo(settings.scheduler_timezone)).date()
    inicio_hoje = _inicio_do_dia(hoje)

    async with get_session() as session:
        ultima_por_cliente = (
            select(MetricaCliente)
            .distinct(MetricaCliente.cliente_id)
            .order_by(MetricaCliente.cliente_id, MetricaCliente.inicio_janela.desc())
            .subquery()
        )
        UltimaMetrica = aliased(MetricaCliente, ultima_por_cliente)

        stmt = (
            select(UltimaMetrica, Cliente.nome)
            .join(Cliente, Cliente.cliente_id == UltimaMetrica.cliente_id)
            .order_by(Cliente.nome.asc().nulls_last())
            .limit(limit)
        )

        linhas = (await session.execute(stmt)).all()

        volume_stmt = (
            select(
                MetricaCliente.cliente_id,
                func.sum(MetricaCliente.total_atendidas + MetricaCliente.total_falhas).label("volume"),
            )
            .where(MetricaCliente.fim_janela >= inicio_hoje)
            .group_by(MetricaCliente.cliente_id)
        )
        volume_por_cliente = {
            linha.cliente_id: linha.volume for linha in (await session.execute(volume_stmt)).all()
        }

    clientes = [
        ClienteResumo(
            cliente_id=metrica.cliente_id,
            nome=nome,
            inicio_janela=metrica.inicio_janela,
            fim_janela=metrica.fim_janela,
            total_atendidas=metrica.total_atendidas,
            total_falhas=metrica.total_falhas,
            asr_percentual=metrica.asr_percentual,
            acd_segundos=metrica.acd_segundos,
            pdd_medio_segundos=metrica.pdd_medio_segundos,
            volume_dia=volume_por_cliente.get(metrica.cliente_id, 0),
        )
        for metrica, nome in linhas
    ]

    return ClientesResumoResponse(registros=len(clientes), clientes=clientes)


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
        cliente = await session.get(Cliente, cliente_id)
        if cliente is None:
            raise HTTPException(404, f"Cliente {cliente_id} não tem nenhuma coleta registrada")

        stmt = select(MetricaCliente).where(MetricaCliente.cliente_id == cliente_id)
        if data_inicio is not None:
            stmt = stmt.where(MetricaCliente.inicio_janela >= _inicio_do_dia(data_inicio))
        if data_fim is not None:
            stmt = stmt.where(MetricaCliente.inicio_janela < _inicio_do_dia(data_fim + timedelta(days=1)))
        stmt = stmt.order_by(MetricaCliente.inicio_janela.asc()).limit(limit + 1)

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
    situacao: SituacaoJanela | None = Query(None, description="Filtra por situação da coleta"),
    data_inicio: date | None = Query(None, description="Só janelas com início >= essa data"),
    data_fim: date | None = Query(None, description="Só janelas com início <= essa data (dia inteiro)"),
    limit: int = Query(100, ge=1, le=MAX_REGISTROS, description="Máximo de janelas retornadas"),
) -> JanelasResponse:
    """Histórico de execuções do scheduler (não os dados de cliente em si) — pra acompanhar se as
    coletas estão rodando e se alguma ficou `parcial`/`falhou`. Ordenado do mais recente pro mais
    antigo."""

    async with get_session() as session:
        stmt = select(Janela)
        if situacao is not None:
            stmt = stmt.where(Janela.situacao == situacao)
        if data_inicio is not None:
            stmt = stmt.where(Janela.inicio_janela >= _inicio_do_dia(data_inicio))
        if data_fim is not None:
            stmt = stmt.where(Janela.inicio_janela < _inicio_do_dia(data_fim + timedelta(days=1)))
        stmt = stmt.order_by(Janela.inicio_janela.desc()).limit(limit)

        linhas = (await session.execute(stmt)).scalars().all()

    return JanelasResponse(
        registros=len(linhas),
        janelas=[JanelaColeta.model_validate(linha) for linha in linhas],
    )
