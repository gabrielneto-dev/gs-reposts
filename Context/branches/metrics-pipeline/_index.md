# Branch: metrics-pipeline

## Purpose

The Postgres-backed storage and scheduler that periodically collects ASR/ACD/PDD per client from
the NextRouter softswitch (via `branches/nextrouter-api/`'s client functions) and persists it for
later reporting. Lives inside `backend/` (see
`Context/global/decisions/DEC-20260904-backend-owns-storage-and-scheduler.md` for why it's here and
not in `frontend/`).

## Scope

- `backend/app/db/` — SQLAlchemy 2.0 async models + engine/session (`base.py`, `models.py`)
- `backend/alembic/` — migrations
- `backend/app/scheduler/` — `jobs.py` (window resolution + the collection job), `scheduler.py`
  (APScheduler wiring)
- The `get_exact_metrics_for_client` function added to `backend/app/clients/nextrouter.py` (owned
  by `branches/nextrouter-api/` scope-wise, but exists specifically to serve this job)
- The Postgres database `gs_reposts_metrics` / role `gs_reposts_backend` (local dev instance)

## Current state

Working end-to-end and now consumed by a real frontend page (2026-09-08 — see
`branches/frontend-nextjs-prisma/facts/FCT-20260908-clientes-overview-page.md`). The scheduler has
run unattended across multiple days on the dev machine (real evidence it survives process
restarts/reboots as long as `uvicorn` is running), accumulating 77 distinct clients by 2026-09-08.
All table/column names and the API's JSON fields are Portuguese as of 2026-09-08 — see
`Context/global/decisions/DEC-20260908-portuguese-schema-naming.md`. The window schedule changed
the same day — see `decisions/DEC-20260908-collection-window-00h-split.md`.

Not yet done: no automated tests, no retry-on-transient-failure, no backfill tool for missed
windows.

## Core concepts

- **Collection window schedule**: `[00:00,07:00)`, hourly `[07:00,08:00)` ... `[19:00,20:00)`, and
  `[20:00,00:00)` — 15 fires/day. See `decisions/DEC-20260908-collection-window-00h-split.md`
  (supersedes the original single-overnight-window design).
- **Discovery is sampled, per-client metrics are exact** — a deliberate asymmetry, see
  `decisions/DEC-20260904-sampled-discovery-exact-client-metrics.md`.
- **All naming is Portuguese** (tables, columns, enum values, API fields) — see
  `Context/global/decisions/DEC-20260908-portuguese-schema-naming.md`. Current model names:
  `Cliente`/`clientes`, `Janela`/`janelas_coleta`, `MetricaCliente`/`metricas_cliente`,
  `SituacaoJanela`/`situacao_janela`.
- **`get_exact_metrics_for_client`** (`backend/app/clients/nextrouter.py`) composes the same
  low-level calls the existing `exato=true` routes use (`get_cdr_aggregate` +
  `get_disconnection_full`) into one exact ASR+ACD+PDD result for one client in one window — the
  single reused building block between the HTTP routes and the scheduler job.
- **`resolve_window(now)`** (`backend/app/scheduler/jobs.py`) turns "the cron fired at hour H" into
  the actual window to process — the branching logic lives here, nowhere else.
- **`GET /api/metricas/clientes`** — one row per client for a listing UI, with `volume_dia`
  (today's total calls, summed across windows) alongside the latest window's ASR/ACD/PDD. See
  `facts/FCT-20260904-schema-and-reused-functions.md` for the query pattern.

## Key records

- `decisions/DEC-20260908-collection-window-00h-split.md` (active; supersedes
  `DEC-20260904-collection-window-schedule.md`)
- `decisions/DEC-20260904-sampled-discovery-exact-client-metrics.md`
- `facts/FCT-20260904-schema-and-reused-functions.md` (kept current in place, not superseded)
- `facts/FCT-20260904-sqlalchemy-postgres-enum-gotchas.md`
- `risks/RSK-20260904-transient-network-failures-during-collection.md`
- `Context/global/decisions/DEC-20260908-portuguese-schema-naming.md` (global, but defines this
  branch's naming going forward)

## Active decisions

`decisions/DEC-20260908-collection-window-00h-split.md`,
`decisions/DEC-20260904-sampled-discovery-exact-client-metrics.md`,
`Context/global/decisions/DEC-20260908-portuguese-schema-naming.md`.
`DEC-20260904-collection-window-schedule.md` is superseded — don't treat it as current.

## Open questions

- Whether the transient-failure retry (see the risk record) is worth building — still pending real
  operational data.

## Risks

- `risks/RSK-20260904-transient-network-failures-during-collection.md` — occasional
  connection-level failures observed on this Windows dev machine during concurrent fetches; the
  job already tolerates per-client failures (marks the window `partial`), but there's no retry yet.
- Same production-caution constraint as `nextrouter-api` applies here: the scheduler calls the real
  production softswitch on a fixed schedule, unattended — see `Context/core/constraints.md`.

## Relations to other branches

- `nextrouter-api` — this branch's job is built entirely out of `nextrouter-api`'s client
  functions (`scan_active_customer_ids`, `get_cdr_aggregate`, `get_disconnection_full`,
  `_buscar_clientes_por_id`) and adds one new one (`get_exact_metrics_for_client`) to the same
  file. No routes were added or changed.
- `frontend-nextjs-prisma` — that branch lost its database/ORM as a direct consequence of this one
  existing; see `Context/global/decisions/DEC-20260904-backend-owns-storage-and-scheduler.md`.
