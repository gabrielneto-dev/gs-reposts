"""Grade canônica de janelas de coleta: [00h,07h), hora em hora [07h,20h), [20h,00h) — 15 janelas
por dia. Única fonte de verdade dessa grade — usada pelo scheduler (indiretamente, via
`resolve_window` em `jobs.py`, que resolve só a janela do disparo atual), pelo backfill histórico
e pelo endpoint de status/disparo manual (`GET/POST /api/metricas/janelas/...`)."""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo


def janelas_do_dia(dia: date, tz: ZoneInfo) -> list[tuple[datetime, datetime]]:
    """As 15 janelas canônicas de um dia, na ordem cronológica."""

    janelas = [(datetime.combine(dia, time(0, 0), tzinfo=tz), datetime.combine(dia, time(7, 0), tzinfo=tz))]
    for hora in range(7, 20):
        janelas.append(
            (datetime.combine(dia, time(hora, 0), tzinfo=tz), datetime.combine(dia, time(hora + 1, 0), tzinfo=tz))
        )
    janelas.append(
        (datetime.combine(dia, time(20, 0), tzinfo=tz), datetime.combine(dia + timedelta(days=1), time(0, 0), tzinfo=tz))
    )
    return janelas
