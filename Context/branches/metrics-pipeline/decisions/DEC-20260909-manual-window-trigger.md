---
id: CTX-DEC-20260909-manual-window-trigger
type: decision
title: Manual trigger for missed collection windows, guarded against overlapping the scheduler
branch: metrics-pipeline
tags: [scheduler, janelas, concurrency, backend]
status: active
confidence: high
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: []
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-09
valid_until: null
revisit_at: null
---

## Decision

Added `GET /api/metricas/janelas/grade` (status of the 15 canonical daily slots across a date
range, max 31 days per request) and `POST /api/metricas/janelas/disparar` (manually run one missed
slot) to let the user see and fix gaps where a window never ran automatically.

- The canonical 15-slots-per-day grid (`00:00-07:00`, hourly `07:00-20:00`, `20:00-00:00`) was
  extracted out of `backend/scripts/backfill_historico.py` into
  `backend/app/scheduler/grade.py`'s `janelas_do_dia(dia, tz)` — now the single source of truth,
  reused by the grade endpoint, the trigger endpoint, and the backfill script.
- A slot with no `Janela` row is synthesized as `faltando` (already past, can be triggered) if
  `fim <= agora`, or `futuro` (blocked) otherwise — the grade endpoint never lets you see, let alone
  trigger, a slot that hasn't happened yet.
- The trigger endpoint validates, in order: the window isn't in the future (400) → the
  `(inicio, fim)` pair matches an actual canonical slot (400 — rejects arbitrary ranges) → no
  `Janela` already exists for it (409 — won't double-collect) → the shared `coleta_em_andamento`
  `asyncio.Lock` isn't held (409 — won't run concurrently with either the automatic scheduler or
  another manual trigger). It then runs via `BackgroundTasks` so the HTTP response returns
  immediately; completion still drives the same webhook + SSE live-refresh as an automatic window.
- `coleta_em_andamento` (`backend/app/scheduler/jobs.py`, module-level `asyncio.Lock()`) is now
  acquired by **both** `scheduler.py`'s automatic `_job()` and the manual trigger's background task
  — the same one lock guards both paths.

## Why

User's request: "Blz, quero que crie uma nova página que tem como objetivo ver os status de cada
janela, tendo uma forma de disparar a janela manualmente, para horários posteriores de agora [...]
não é possível" — explicitly wanted future slots blocked, and explicitly worried about it clashing
with the automatic scheduler, hence the shared lock rather than trusting the two code paths not to
race by accident.

## Consequences

- Any future code path that also calls `run_collection_window` directly (bypassing both the
  scheduler and this endpoint) must also acquire `coleta_em_andamento` first, or the overlap
  protection is silently defeated.
- `janelas_do_dia` is now a dependency of three call sites (`grade_janelas`, `disparar_janela`,
  `backfill_historico.py`) — changing the slot boundaries changes all three at once, which is the
  intended behavior, not a risk to guard against.
