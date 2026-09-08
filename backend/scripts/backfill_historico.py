"""Backfill histórico: roda `run_collection_window` pra cada janela de coleta que o scheduler já
usa (00h-07h, hora em hora 07h-20h, 20h-00h), retroativo por N dias — pra popular
`metricas_cliente` com histórico suficiente pras médias de referência dos gatilhos
(ontem/semanal/mensal).

Uso (a partir de backend/):
    PYTHONPATH=. .venv/Scripts/python.exe scripts/backfill_historico.py --dias 30

Idempotente: pula qualquer janela que já exista (mesma chave única inicio_janela/fim_janela que o
scheduler usa), então dá pra interromper (Ctrl+C) e rodar de novo sem duplicar nada.

CUIDADO: isso faz uma descoberta + busca de métricas exatas por cliente pra CADA janela contra o
NextRouter de PRODUÇÃO real (mesmo custo de uma coleta ao vivo, só que ~15x/dia comprimido numa
sessão só). Só GET, mas é bastante volume de chamadas — por isso o `--pausa` entre janelas.
"""

import argparse
import asyncio
import logging
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.db.base import get_session
from app.db.models import Janela
from app.scheduler.jobs import run_collection_window

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("backfill")

TZ = ZoneInfo("America/Sao_Paulo")


def janelas_do_dia(dia: date) -> list[tuple[datetime, datetime]]:
    """Mesma grade do scheduler (ver `resolve_window` em app/scheduler/jobs.py):
    [00h,07h), hora em hora [07h,20h), [20h,00h) — 15 janelas por dia."""

    janelas = [(datetime.combine(dia, time(0, 0), tzinfo=TZ), datetime.combine(dia, time(7, 0), tzinfo=TZ))]
    for hora in range(7, 20):
        janelas.append(
            (datetime.combine(dia, time(hora, 0), tzinfo=TZ), datetime.combine(dia, time(hora + 1, 0), tzinfo=TZ))
        )
    janelas.append(
        (datetime.combine(dia, time(20, 0), tzinfo=TZ), datetime.combine(dia + timedelta(days=1), time(0, 0), tzinfo=TZ))
    )
    return janelas


async def janela_ja_existe(window_start: datetime, window_end: datetime) -> bool:
    async with get_session() as session:
        stmt = select(Janela.id).where(Janela.inicio_janela == window_start, Janela.fim_janela == window_end)
        return (await session.execute(stmt)).scalar_one_or_none() is not None


async def main(dias: int, pausa_segundos: float, dia_especifico: date | None) -> None:
    agora = datetime.now(TZ)
    hoje = agora.date()

    if dia_especifico is not None:
        dias_a_processar = [dia_especifico]
    else:
        dias_a_processar = [hoje - timedelta(days=i) for i in range(dias, -1, -1)]  # mais antigo -> mais recente

    todas_janelas = [
        (window_start, window_end)
        for dia in dias_a_processar
        for window_start, window_end in janelas_do_dia(dia)
        if window_end <= agora
    ]

    total = len(todas_janelas)
    logger.info("Backfill: %s janela(s) a processar (%s dia(s): %s)", total, len(dias_a_processar), dias_a_processar)

    processadas = puladas = falhas = 0
    for indice, (window_start, window_end) in enumerate(todas_janelas, start=1):
        if await janela_ja_existe(window_start, window_end):
            puladas += 1
            logger.info("[%s/%s] já existe, pulando: %s -> %s", indice, total, window_start, window_end)
            continue

        try:
            await run_collection_window(window_start, window_end)
            processadas += 1
            logger.info("[%s/%s] ok: %s -> %s", indice, total, window_start, window_end)
        except Exception:
            falhas += 1
            logger.exception("[%s/%s] falhou: %s -> %s", indice, total, window_start, window_end)

        if pausa_segundos > 0:
            await asyncio.sleep(pausa_segundos)

    logger.info(
        "Backfill concluído: %s processada(s), %s pulada(s) (já existiam), %s falharam, de %s no total",
        processadas, puladas, falhas, total,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill histórico de métricas (até N dias atrás, ou um dia específico)")
    parser.add_argument("--dias", type=int, default=30, help="Quantos dias atrás, além de hoje (default: 30)")
    parser.add_argument("--pausa", type=float, default=2.0, help="Pausa em segundos entre janelas (default: 2.0)")
    parser.add_argument(
        "--dia", type=date.fromisoformat, default=None,
        help="Processa só esse dia (YYYY-MM-DD), ignorando --dias",
    )
    args = parser.parse_args()
    asyncio.run(main(args.dias, args.pausa, args.dia))
