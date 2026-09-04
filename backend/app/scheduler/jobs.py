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
from app.db.models import Client, ClientMetric, CollectionWindow, WindowStatus
from app.routers.clientes import _buscar_clientes_por_id

logger = logging.getLogger(__name__)


def resolve_window(now: datetime) -> tuple[datetime, datetime]:
    """Traduz o horário do disparo (sempre em ponto, entre 07h e 20h) na janela a processar:
    overnight (20:00 de ontem -> 07:00 de hoje) quando o disparo é às 07:00, senão a hora cheia
    anterior (disparo às H processa [H-1, H))."""

    hoje = now.date()
    if now.hour == 7:
        window_start = datetime.combine(hoje - timedelta(days=1), time(20, 0), tzinfo=now.tzinfo)
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
        janela = CollectionWindow(
            window_start=window_start,
            window_end=window_end,
            discovery_sample_limit=scan_limit,
            status=WindowStatus.RUNNING,
        )
        session.add(janela)
        await session.flush()

        try:
            ranking = await scan_active_customer_ids(periodo=periodo, limite_scan=scan_limit)
        except NextRouterAPIError as exc:
            janela.status = WindowStatus.FAILED
            janela.error_message = f"Falha na descoberta de clientes ativos: {exc.message}"
            janela.finished_at = datetime.now(window_start.tzinfo)
            await session.commit()
            logger.error("Coleta da janela %s -> %s falhou na descoberta: %s", window_start, window_end, exc.message)
            return

        janela.clients_discovered = len(ranking)

        if not ranking:
            janela.status = WindowStatus.COMPLETED
            janela.finished_at = datetime.now(window_start.tzinfo)
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

            cliente_existente = await session.get(Client, cliente_id)
            if cliente_existente is None:
                session.add(Client(cliente_id=cliente_id, nome=nome, first_seen_at=agora, last_seen_at=agora, updated_at=agora))
            else:
                cliente_existente.nome = nome or cliente_existente.nome
                cliente_existente.last_seen_at = agora
                cliente_existente.updated_at = agora

            session.add(
                ClientMetric(
                    window_id=janela.id,
                    window_start=window_start,
                    window_end=window_end,
                    cliente_id=cliente_id,
                    total_atendidas=metricas["total_atendidas"],
                    total_falhas=metricas["total_falhas"],
                    asr_percentual=metricas["asr_percentual"],
                    acd_segundos=metricas["acd_segundos"],
                    pdd_medio_segundos=metricas["pdd_medio_segundos"],
                    occurrences_discovery=occurrences,
                    truncado=metricas["truncado"],
                )
            )
            janela.clients_processed += 1

        janela.status = WindowStatus.PARTIAL if houve_erro else WindowStatus.COMPLETED
        janela.finished_at = datetime.now(window_start.tzinfo)
        await session.commit()

        logger.info(
            "Coleta da janela %s -> %s concluída (%s): %s/%s clientes processados",
            window_start, window_end, janela.status.value, janela.clients_processed, janela.clients_discovered,
        )
