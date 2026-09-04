---
id: CTX-CP-20260904-1800-metrics-storage-and-scheduler
type: checkpoint
title: Built the Postgres metrics store + scheduler in backend/, removed Prisma from frontend/
status: active
created_at: 2026-09-04
updated_at: 2026-09-04
tags: [postgres, scheduler, sqlalchemy, api-design, monorepo, prisma]
---

# Session Checkpoint

## Objective

Decide where scheduled ASR/ACD/PDD-per-client collection and storage should live (backend vs.
frontend), then design and build it: a Postgres schema for time-windowed metrics per client, and a
scheduler that runs the "discover active clients → fetch their metrics" flow on a fixed cadence.

## What changed

- Decided `backend/` owns storage + scheduling (not `frontend/`) — see
  `CTX-DEC-20260904-backend-owns-storage-and-scheduler`. `frontend/`'s Prisma setup was removed
  entirely as a direct consequence.
- Built `backend/app/db/` (SQLAlchemy 2.0 async models + engine/session) and `backend/alembic/`
  (async migrations, one applied: `62ecd3fd9f03`) — 3 tables: `clients`, `collection_windows`,
  `client_metrics`. See `CTX-FCT-20260904-schema-and-reused-functions`.
- Built `backend/app/scheduler/` (`jobs.py`: `resolve_window` + `run_collection_window`;
  `scheduler.py`: `AsyncIOScheduler` wired into FastAPI's `lifespan`). Fires 07:00-20:00 hourly plus
  one overnight window — see `CTX-DEC-20260904-collection-window-schedule`.
- Added `get_exact_metrics_for_client` to `backend/app/clients/nextrouter.py` — the one new
  function, composing existing `get_cdr_aggregate`/`get_disconnection_full` calls. No routers or
  existing routes changed.
- Created a new local Postgres role/database (`gs_reposts_backend`/`gs_reposts_metrics`) — separate
  from the frontend's old `gs_reposts_app`/`gs_reposts`.
- Removed Prisma from `frontend/`: `src/prisma/`, `prisma.config.ts`, package.json deps/scripts,
  `DATABASE_URL`. `npm run build` verified clean.
- New env vars in `backend/.env` (not recorded here, see the file): `DATABASE_URL`,
  `SCHEDULER_ENABLED`, `SCHEDULER_SCAN_LIMIT`, `SCHEDULER_CLIENT_CONCURRENCY`, `SCHEDULER_TIMEZONE`.

## Decisions

- `CTX-DEC-20260904-backend-owns-storage-and-scheduler` (global) — the core architecture call.
- `CTX-DEC-20260904-collection-window-schedule` — hourly 07:00-20:00 + one overnight window,
  `CronTrigger(hour="7-20")` firing at window close.
- `CTX-DEC-20260904-sampled-discovery-exact-client-metrics` — discovery stays sampled (same
  pattern as the existing routes), but every stored per-client metric is exact, because a
  per-client/narrow-window fetch is cheap regardless.

## Discoveries

- `CTX-FCT-20260904-sqlalchemy-postgres-enum-gotchas` — two SQLAlchemy/Postgres native-enum traps:
  generic `sa.Enum` re-triggers `CREATE TYPE` during `CREATE TABLE` even with `create_type=False`
  (fix: use `postgresql.ENUM` directly, not generic `sa.Enum`); and `Enum(PythonEnumClass)` sends
  the member `.name` not `.value` by default (fix: `values_callable`).
- `CTX-RSK-20260904-transient-network-failures-during-collection` — occasional connection-reset-
  shaped failures on this Windows dev machine during concurrent async I/O (both `asyncpg` and
  `httpx`), not reproducible on a sequential retry. One instance was a red herring for a real wrong-
  password bug; the other was genuinely transient during a real collection run (2/72 clients).
- Confirmed via exploration that `frontend/`'s Prisma setup had **zero actual usage** anywhere in
  `frontend/src` before removal — made the removal low-risk.

## Problems solved

- Alembic's async `env.py` template needed wiring to `app.config.settings.database_url` and
  `app.db.base.Base.metadata` — done once in `env.py`, autogenerate-ready for future migrations.
- A leftover `frontend/prisma.config.ts` (outside `src/prisma/`) was missed on first pass and broke
  `npm run build`'s typecheck — found and removed. Lesson: when removing a tool from a JS/TS
  project, grep for its config files at the project root too, not just the obvious source directory.
- Postgres role password mismatch during setup (`gs_reposts_backend` existed but with a different
  password than assumed) produced a confusing `asyncpg` connection-reset-shaped error before a
  plain `psql` connection attempt revealed the real "password authentication failed" cause.

## Failed approaches worth remembering

- Don't reuse a generic `sa.Enum(...)` object as both the explicit `.create()` target and a table
  column's type in the same Alembic migration expecting `create_type=False` to prevent a duplicate
  `CREATE TYPE` — it doesn't reliably work across the dialect adaptation step. Use
  `sqlalchemy.dialects.postgresql.ENUM` directly instead.
- Don't run concurrent per-client DB writes on a single shared `AsyncSession` from multiple
  coroutines (not safe) — the job design here deliberately splits the concurrent phase (NextRouter
  fetch only, under a semaphore) from the DB-write phase (sequential, single coroutine, after
  `asyncio.gather` collects results).

## Current state

`backend/` is now the system of record: 8 verified GET routes (unchanged) plus a working, verified
Postgres store and scheduler for ASR/ACD/PDD per client per time window. `frontend/` is a clean
Next.js scaffold with no database and no integration with `backend/` yet. Changes are on disk, not
yet committed to git (check `git status` in a future session before assuming otherwise).

## Open questions

- How/when the frontend will consume `metrics-pipeline`'s data (no design yet).
- Whether the transient network failures (see the risk record) are common enough in real
  unattended operation to justify adding retry logic.
- Frontend data model and auth strategy — both still undecided, carried over from the prior
  checkpoint.

## Next steps

- Let the scheduler run unattended for a while, then check `collection_windows.status`/
  `error_message` to see how often `partial` happens before deciding whether to add retries.
- Design the frontend's first real page/fetch against `backend/`'s API (either the existing
  NextRouter-adapter routes or the new stored-metrics data — no query endpoints exist yet for the
  latter, only ingestion).
- Consider whether the local `gs_reposts_app`/`gs_reposts` Postgres role/database (frontend's old,
  now-unused setup) should be dropped for cleanliness.

## Files or artifacts affected

`backend/app/db/` (new), `backend/app/scheduler/` (new), `backend/alembic/` (new),
`backend/app/clients/nextrouter.py` (added `get_exact_metrics_for_client`),
`backend/app/config.py`/`backend/app/main.py` (updated), `backend/requirements.txt` (added
sqlalchemy, asyncpg, alembic, apscheduler), `backend/.env`/`backend/.env.example` (new vars).
`frontend/src/prisma/` (deleted), `frontend/prisma.config.ts` (deleted), `frontend/package.json`
(Prisma deps/scripts removed), `frontend/.env`/`.env.example` (cleared).

## Context records created or updated

Created: `CTX-DEC-20260904-backend-owns-storage-and-scheduler` (global); the new
`metrics-pipeline` branch — `_index.md`,
`decisions/{DEC-20260904-collection-window-schedule, DEC-20260904-sampled-discovery-exact-client-metrics}`,
`facts/{FCT-20260904-schema-and-reused-functions, FCT-20260904-sqlalchemy-postgres-enum-gotchas}`,
`risks/RSK-20260904-transient-network-failures-during-collection`.

Updated: `Context/core/overview.md`, `Context/core/constraints.md`, `Context/STATE.md`,
`Context/MAP.md`, `Context/_meta/taxonomy.yaml`, `branches/nextrouter-api/_index.md` (cross-link),
`branches/frontend-nextjs-prisma/_index.md` and 4 of its records (marked superseded:
`FCT-20260904-prisma8-cli-behavior`, `FCT-20260904-local-postgres`,
`DEC-20260904-orm-not-composer`, `DEC-20260904-dedicated-db-role`; annotated but kept active:
`FCT-20260904-scaffold`).
