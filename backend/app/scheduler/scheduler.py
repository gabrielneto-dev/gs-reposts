import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.scheduler.jobs import resolve_window, run_collection_window

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=settings.scheduler_timezone)

JOB_ID = "collect_metrics_window"


async def _job() -> None:
    now = datetime.now(ZoneInfo(settings.scheduler_timezone)).replace(minute=0, second=0, microsecond=0)
    window_start, window_end = resolve_window(now)
    logger.info("Disparo do scheduler às %s: coletando janela %s -> %s", now, window_start, window_end)
    await run_collection_window(window_start, window_end)


def start_scheduler() -> None:
    """Liga o job de coleta (7h-20h em ponto, hora local). `SCHEDULER_ENABLED=false` desliga sem
    remover o resto da app — útil pra rodar a API localmente sem martelar a produção sem querer."""

    if not settings.scheduler_enabled:
        logger.info("Scheduler desabilitado (SCHEDULER_ENABLED=false)")
        return

    scheduler.add_job(
        _job,
        trigger=CronTrigger(hour="7-20", minute=0, timezone=settings.scheduler_timezone),
        id=JOB_ID,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )
    scheduler.start()
    logger.info("Scheduler iniciado: coleta às 7h-20h em ponto (%s)", settings.scheduler_timezone)


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown(wait=False)
