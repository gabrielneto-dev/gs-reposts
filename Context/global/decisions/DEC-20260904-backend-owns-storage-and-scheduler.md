---
id: CTX-DEC-20260904-backend-owns-storage-and-scheduler
type: decision
title: backend/ now owns a Postgres metrics store and the collection scheduler; frontend/ drops Prisma entirely
branch: global
tags: [monorepo, api-design, postgres, scheduler, production-safety]
status: active
confidence: high
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-DEC-20260904-monorepo-restructure, CTX-DEC-20260904-route-simplification]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-04
valid_until: null
revisit_at: null
---

# Decision

## Context

`CTX-DEC-20260904-monorepo-restructure` framed `backend/` as a stateless adapter (no DB) and
`frontend/` as the system of record (Prisma 8 + its own Postgres). The user then asked for
scheduled, recurring collection of ASR/ACD/PDD per client (fixed time windows, see below), stored
for later reporting. That's a background process independent of any user request — it doesn't fit
Next.js's request/response model — and `backend/` already holds all the NextRouter integration
logic (sampling, exact-mode fetches, safety caps).

## Decision

- `backend/` now owns a **dedicated Postgres database** (`gs_reposts_metrics`, role
  `gs_reposts_backend` — separate from the frontend's old `gs_reposts`/`gs_reposts_app`) and an
  in-process **APScheduler** (`AsyncIOScheduler`) wired into FastAPI's `lifespan`.
- `frontend/` **no longer has a database or Prisma at all** — `src/prisma/`, `prisma.config.ts`,
  the Prisma deps/scripts in `package.json`, and `DATABASE_URL` were all removed. It's now a pure
  HTTP consumer of `backend/`'s API (no integration code written yet).
- This **amends** (does not fully supersede) `CTX-DEC-20260904-monorepo-restructure`: the
  backend/frontend directory split still stands, but "backend has no database, is not the system
  of record" is no longer true. `Context/core/overview.md` was rewritten to reflect this.
- See `branches/metrics-pipeline/` for the schema, collection-window schedule, and scheduler
  design this decision produced.

## Rationale

The scheduler needs to run 24/7 regardless of HTTP traffic — that's inherently backend/service
work, not frontend work. Consolidating storage in the service that already has all the softswitch
integration logic (client fetch functions, safety caps, concurrency limits) avoids a second
data-access layer and keeps the "who talks to the softswitch" surface in one place.

## Consequences

- The frontend's old Prisma-specific knowledge (`branches/frontend-nextjs-prisma/`'s Prisma 8 CLI
  behavior, ORM-vs-Composer decision, dedicated-role decision) is now **superseded** — marked as
  such in that branch rather than deleted, since it's still valid history of what was tried.
- The frontend's old `gs_reposts`/`gs_reposts_app` Postgres role/database were left in place
  (not dropped) — they're just unused now. Safe to clean up later if desired.
- Any future frontend UI work will need a fetch layer against `backend/`'s API — none exists yet.
- The "GET-only, mind production load" constraint in `Context/core/constraints.md` now also
  applies to the scheduler's job loop, not just the HTTP routes.

## Related records

`CTX-DEC-20260904-monorepo-restructure`, `branches/metrics-pipeline/_index.md`,
`branches/frontend-nextjs-prisma/_index.md`.
