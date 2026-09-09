import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import aliased

from app.config import settings
from app.db.base import get_session
from app.db.models import Cliente, Janela, MetricaCliente, SituacaoJanela
from app.scheduler.grade import janelas_do_dia
from app.scheduler.jobs import coleta_em_andamento, run_collection_window
from app.schemas.metricas import (
    ClienteMetricasResponse,
    ClienteResumo,
    ClientesResumoResponse,
    DiaGrade,
    DispararJanelaRequest,
    DispararJanelaResponse,
    GradeJanelasResponse,
    JanelaColeta,
    JanelasResponse,
    MetricaJanela,
    SlotJanela,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/metricas", tags=["Métricas"])

MAX_REGISTROS = 2000


def _inicio_do_dia(dia: date) -> datetime:
    return datetime.combine(dia, time.min, tzinfo=ZoneInfo(settings.scheduler_timezone))


def _com_timezone(momento: datetime, tz: ZoneInfo) -> datetime:
    """Datetime vindo de query param pode chegar sem timezone (ex: <input type="datetime-local">
    manda "2026-09-08T12:00" puro) — nesse caso assume o fuso operacional do sistema."""

    return momento if momento.tzinfo is not None else momento.replace(tzinfo=tz)


@router.get("/clientes", response_model=ClientesResumoResponse)
async def resumo_clientes(
    inicio: datetime | None = Query(None, description="Início do período (inclusive); default é o início de hoje"),
    fim: datetime | None = Query(None, description="Fim do período (exclusive); default é o início de amanhã"),
    limit: int = Query(200, ge=1, le=MAX_REGISTROS, description="Máximo de clientes retornados"),
) -> ClientesResumoResponse:
    """Um cliente por linha: ASR/ACD/PDD da janela mais recente coletada NO PERÍODO FILTRADO
    (default: hoje inteiro), mais `volume_periodo` (chamadas somadas de todas as janelas do
    período). Não faz nenhuma chamada ao softswitch. Só aparecem clientes com pelo menos uma
    coleta feita no período — clientes sem chamada nesse intervalo simplesmente não entram na
    lista. Ordenado por nome."""

    tz = ZoneInfo(settings.scheduler_timezone)
    hoje = datetime.now(tz).date()

    inicio_periodo = _com_timezone(inicio, tz) if inicio is not None else _inicio_do_dia(hoje)
    fim_periodo = _com_timezone(fim, tz) if fim is not None else _inicio_do_dia(hoje + timedelta(days=1))

    if inicio_periodo >= fim_periodo:
        raise HTTPException(400, "inicio deve ser antes de fim")

    async with get_session() as session:
        ultima_por_cliente = (
            select(MetricaCliente)
            .where(MetricaCliente.fim_janela >= inicio_periodo, MetricaCliente.fim_janela < fim_periodo)
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
            .where(MetricaCliente.fim_janela >= inicio_periodo, MetricaCliente.fim_janela < fim_periodo)
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
            volume_periodo=volume_por_cliente.get(metrica.cliente_id, 0),
        )
        for metrica, nome in linhas
    ]

    return ClientesResumoResponse(
        inicio=inicio_periodo, fim=fim_periodo, registros=len(clientes), clientes=clientes
    )


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


MAX_DIAS_GRADE = 31


@router.get("/janelas/grade", response_model=GradeJanelasResponse)
async def grade_janelas(
    data_inicio: date = Query(..., description="Primeiro dia do intervalo (inclusive)"),
    data_fim: date = Query(..., description="Último dia do intervalo (inclusive)"),
) -> GradeJanelasResponse:
    """Os 15 slots canônicos de cada dia do intervalo, cruzados com o que já existe no banco.
    Slots sem `Janela` viram `faltando` (já passou, pode disparar) ou `futuro` (ainda não chegou,
    bloqueado) — só assim dá pra enxergar o que nunca rodou, já que `/janelas` só lista o que
    existe de verdade."""

    if data_fim < data_inicio:
        raise HTTPException(400, "data_fim deve ser >= data_inicio")
    if (data_fim - data_inicio).days > MAX_DIAS_GRADE:
        raise HTTPException(400, f"intervalo máximo de {MAX_DIAS_GRADE} dias por consulta")

    tz = ZoneInfo(settings.scheduler_timezone)
    agora = datetime.now(tz)

    async with get_session() as session:
        stmt = select(Janela).where(
            Janela.inicio_janela >= _inicio_do_dia(data_inicio),
            Janela.inicio_janela < _inicio_do_dia(data_fim + timedelta(days=1)),
        )
        existentes = (await session.execute(stmt)).scalars().all()

    por_intervalo = {(j.inicio_janela, j.fim_janela): j for j in existentes}

    dias: list[DiaGrade] = []
    dia_atual = data_inicio
    while dia_atual <= data_fim:
        slots = []
        for inicio, fim in janelas_do_dia(dia_atual, tz):
            existente = por_intervalo.get((inicio, fim))
            if existente is not None:
                slots.append(
                    SlotJanela(
                        inicio_janela=inicio,
                        fim_janela=fim,
                        situacao=existente.situacao.value,
                        janela_id=existente.id,
                        clientes_descobertos=existente.clientes_descobertos,
                        clientes_processados=existente.clientes_processados,
                        mensagem_erro=existente.mensagem_erro,
                        pode_disparar=False,
                    )
                )
            elif fim <= agora:
                slots.append(
                    SlotJanela(inicio_janela=inicio, fim_janela=fim, situacao="faltando", pode_disparar=True)
                )
            else:
                slots.append(
                    SlotJanela(inicio_janela=inicio, fim_janela=fim, situacao="futuro", pode_disparar=False)
                )
        dias.append(DiaGrade(data=dia_atual.isoformat(), janelas=slots))
        dia_atual += timedelta(days=1)

    return GradeJanelasResponse(dias=dias)


@router.post("/janelas/disparar", response_model=DispararJanelaResponse)
async def disparar_janela(dados: DispararJanelaRequest, background_tasks: BackgroundTasks) -> DispararJanelaResponse:
    """Dispara manualmente a coleta de um slot que ficou faltando (só passado — o futuro é
    bloqueado). Roda em background: a resposta volta na hora, e a tela recebe o webhook de
    conclusão igual a uma coleta automática (mesmo mecanismo de live-refresh)."""

    tz = ZoneInfo(settings.scheduler_timezone)
    agora = datetime.now(tz)

    inicio = _com_timezone(dados.inicio_janela, tz)
    fim = _com_timezone(dados.fim_janela, tz)

    if fim > agora:
        raise HTTPException(400, "Não é possível disparar uma janela no futuro")

    slots_validos = set(janelas_do_dia(inicio.date(), tz))
    if (inicio, fim) not in slots_validos:
        raise HTTPException(400, "O intervalo informado não corresponde a uma janela válida da grade")

    async with get_session() as session:
        stmt = select(Janela.id).where(Janela.inicio_janela == inicio, Janela.fim_janela == fim)
        ja_existe = (await session.execute(stmt)).scalar_one_or_none()
    if ja_existe is not None:
        raise HTTPException(409, "Essa janela já foi coletada — veja o histórico")

    if coleta_em_andamento.locked():
        raise HTTPException(409, "Já tem uma coleta em andamento — tente de novo em instantes")

    async def _rodar_em_background() -> None:
        async with coleta_em_andamento:
            try:
                await run_collection_window(inicio, fim)
            except Exception:
                logger.exception("Falha ao disparar manualmente a janela %s -> %s", inicio, fim)

    background_tasks.add_task(_rodar_em_background)

    return DispararJanelaResponse(ok=True, mensagem="Disparado — a tela atualiza sozinha quando terminar")
