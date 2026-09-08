import asyncio
import logging
from datetime import datetime, time, timedelta
from typing import Any

from app.clients.nextrouter import (
    NextRouterAPIError,
    get_exact_metrics_for_client,
    periodo_params,
    scan_active_customer_ids,
)
from app.config import settings
from app.db.base import get_session
from app.db.models import Cliente, Janela, MetricaCliente, SituacaoJanela
from app.routers.clientes import _buscar_clientes_por_id

logger = logging.getLogger(__name__)


def resolve_window(now: datetime) -> tuple[datetime, datetime]:
    """Traduz o horário do disparo (sempre em ponto: 00h, e 07h-20h) na janela a processar:
    - disparo às 00h -> janela da noite anterior, 20:00 de ontem -> 00:00 de hoje
    - disparo às 07h -> janela da madrugada de hoje, 00:00 -> 07:00
    - disparo às H (08h-20h) -> hora cheia anterior, [H-1, H)
    """

    hoje = now.date()
    if now.hour == 0:
        window_start = datetime.combine(hoje - timedelta(days=1), time(20, 0), tzinfo=now.tzinfo)
        window_end = datetime.combine(hoje, time(0, 0), tzinfo=now.tzinfo)
    elif now.hour == 7:
        window_start = datetime.combine(hoje, time(0, 0), tzinfo=now.tzinfo)
        window_end = datetime.combine(hoje, time(7, 0), tzinfo=now.tzinfo)
    else:
        window_start = datetime.combine(hoje, time(now.hour - 1, 0), tzinfo=now.tzinfo)
        window_end = datetime.combine(hoje, time(now.hour, 0), tzinfo=now.tzinfo)
    return window_start, window_end


def _periodo_da_janela(window_start: datetime, window_end: datetime) -> dict[str, Any]:
    return periodo_params(window_start.date(), window_end.date(), window_start.time(), window_end.time())


async def _buscar_metricas_do_cliente(
    cliente_id: int, occurrences: int, periodo: dict[str, Any], semaforo: asyncio.Semaphore
) -> tuple[int, int, dict[str, Any] | None]:
    """Só a parte de rede (concorrente, sob semáforo) — sem tocar a sessão do banco, que não é
    segura pra uso concorrente por múltiplas coroutines."""

    async with semaforo:
        try:
            metricas = await get_exact_metrics_for_client(cliente_id=cliente_id, periodo=periodo)
        except NextRouterAPIError as exc:
            logger.error("Falha ao buscar métricas do cliente %s: %s", cliente_id, exc.message)
            return cliente_id, occurrences, None

    return cliente_id, occurrences, metricas


async def run_collection_window(window_start: datetime, window_end: datetime) -> None:
    """Fluxo completo de uma janela: descobre quem esteve ativo (amostrado), busca ASR/ACD/PDD
    exatos de cada um (filtrado por cliente_id, concorrência limitada) e persiste tudo."""

    periodo = _periodo_da_janela(window_start, window_end)
    scan_limit = settings.scheduler_scan_limit
    agora = datetime.now(window_start.tzinfo)

    async with get_session() as session:
        janela = Janela(
            inicio_janela=window_start,
            fim_janela=window_end,
            limite_amostra_descoberta=scan_limit,
            situacao=SituacaoJanela.EM_ANDAMENTO,
        )
        session.add(janela)
        await session.flush()

        try:
            ranking = await scan_active_customer_ids(periodo=periodo, limite_scan=scan_limit)
        except NextRouterAPIError as exc:
            janela.situacao = SituacaoJanela.FALHOU
            janela.mensagem_erro = f"Falha na descoberta de clientes ativos: {exc.message}"
            janela.finalizado_em = datetime.now(window_start.tzinfo)
            await session.commit()
            logger.error("Coleta da janela %s -> %s falhou na descoberta: %s", window_start, window_end, exc.message)
            return

        janela.clientes_descobertos = len(ranking)

        if not ranking:
            janela.situacao = SituacaoJanela.CONCLUIDA
            janela.finalizado_em = datetime.now(window_start.tzinfo)
            await session.commit()
            return

        try:
            itens_por_id = await _buscar_clientes_por_id({cid for cid, _ in ranking})
        except NextRouterAPIError as exc:
            itens_por_id = {}
            logger.warning("Falha ao buscar nomes dos clientes da janela %s -> %s: %s", window_start, window_end, exc.message)

        semaforo = asyncio.Semaphore(settings.scheduler_client_concurrency)
        resultados = await asyncio.gather(
            *[_buscar_metricas_do_cliente(cid, occ, periodo, semaforo) for cid, occ in ranking]
        )

        houve_erro = False
        for cliente_id, occurrences, metricas in resultados:
            if metricas is None:
                houve_erro = True
                continue

            nome = None
            item = itens_por_id.get(cliente_id)
            if item:
                nome = item.get("nome_fantasia") or item.get("razao_social")

            cliente_existente = await session.get(Cliente, cliente_id)
            if cliente_existente is None:
                session.add(
                    Cliente(
                        cliente_id=cliente_id,
                        nome=nome,
                        visto_pela_primeira_vez_em=agora,
                        visto_pela_ultima_vez_em=agora,
                        atualizado_em=agora,
                    )
                )
            else:
                cliente_existente.nome = nome or cliente_existente.nome
                cliente_existente.visto_pela_ultima_vez_em = agora
                cliente_existente.atualizado_em = agora

            session.add(
                MetricaCliente(
                    janela_id=janela.id,
                    inicio_janela=window_start,
                    fim_janela=window_end,
                    cliente_id=cliente_id,
                    total_atendidas=metricas["total_atendidas"],
                    total_falhas=metricas["total_falhas"],
                    asr_percentual=metricas["asr_percentual"],
                    acd_segundos=metricas["acd_segundos"],
                    pdd_medio_segundos=metricas["pdd_medio_segundos"],
                    ocorrencias_descoberta=occurrences,
                    truncado=metricas["truncado"],
                )
            )
            janela.clientes_processados += 1

        janela.situacao = SituacaoJanela.PARCIAL if houve_erro else SituacaoJanela.CONCLUIDA
        janela.finalizado_em = datetime.now(window_start.tzinfo)
        await session.commit()

        logger.info(
            "Coleta da janela %s -> %s concluída (%s): %s/%s clientes processados",
            window_start, window_end, janela.situacao.value, janela.clientes_processados, janela.clientes_descobertos,
        )
