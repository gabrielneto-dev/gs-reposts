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

Working end-to-end, verified against production on 2026-09-04: migration applied, a manual run of
the collection job for a real 1-hour window discovered 72 active clients and stored exact
ASR/ACD/PDD for 70 of them (2 failed on a transient network error, handled gracefully — see
`risks/RSK-20260904-transient-network-failures-during-collection.md`). The scheduler starts/stops
cleanly with FastAPI's `lifespan` and will fire on its own once the app runs continuously.

Not yet done: no automated tests, no retry-on-transient-failure, no backfill tool for missed
windows, no frontend consumption of this data (frontend has no code calling `backend/` yet).

## Core concepts

- **Collection window schedule**: 07:00-20:00 hourly (`[07:00,08:00)` ... `[19:00,20:00)`) plus one
  overnight window `[20:00, 07:00 next day)`. See
  `decisions/DEC-20260904-collection-window-schedule.md`.
- **Discovery is sampled, per-client metrics are exact** — a deliberate asymmetry, see
  `decisions/DEC-20260904-sampled-discovery-exact-client-metrics.md`.
- **`get_exact_metrics_for_client`** (`backend/app/clients/nextrouter.py`) composes the same
  low-level calls the existing `exato=true` routes use (`get_cdr_aggregate` +
  `get_disconnection_full`) into one exact ASR+ACD+PDD result for one client in one window — the
  single reused building block between the HTTP routes and the scheduler job.
- **`resolve_window(now)`** (`backend/app/scheduler/jobs.py`) turns "the cron fired at hour H" into
  the actual window to process — the overnight-vs-hourly branching logic lives here, nowhere else.

## Key records

- `decisions/DEC-20260904-collection-window-schedule.md`
- `decisions/DEC-20260904-sampled-discovery-exact-client-metrics.md`
- `facts/FCT-20260904-schema-and-reused-functions.md`
- `facts/FCT-20260904-sqlalchemy-postgres-enum-gotchas.md`
- `risks/RSK-20260904-transient-network-failures-during-collection.md`

## Active decisions

See the `decisions/` records above — both active as of 2026-09-04.

## Open questions

- None open yet — no frontend consumption designed, so no schema changes have been requested from
  that side.

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
