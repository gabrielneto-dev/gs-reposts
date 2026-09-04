---
id: CTX-DEC-20260904-monorepo-restructure
type: decision
title: Restructure into a monorepo — backend/ (FastAPI adapter) + frontend/ (Next.js, owns the database)
branch: global
tags: [monorepo, fastapi, nextjs, api-design]
status: active
confidence: high
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-FCT-20260904-project-purpose-confirmed, CTX-FCT-20260904-route-inventory]
depends_on: []
supersedes: null
superseded_by: null
---

# Decision

## Context

The FastAPI service (see `branches/nextrouter-api/`) was originally the whole project, living at
the repo root. The user then pushed the repo to GitHub
(`https://github.com/gabrielneto-dev/gs-reposts.git`, branch `main`) and announced the next phase:
a user-facing frontend with its own database.

## Decision

Restructured the repo root into:

- `backend/` — the existing FastAPI service, moved here via `git mv` (history preserved). Framed
  explicitly as an **adapter/integration layer** for the NextRouter softswitch API: no database of
  its own, not the system of record.
- `frontend/` — new. Owns its own database and is the actual **system of record**; consumes
  `backend/`'s endpoints for softswitch data (ASR/ACD/PDD/clients). See
  `branches/frontend-nextjs-prisma/`.
- `Context/`, `AGENTS.md`, `CLAUDE.md`, and the root `README.md` stay at the repo root — they
  apply to the whole monorepo, not to one side.

## Rationale

Directly requested by the user ("esse backend (FastAPI) é apenas um adapter"). Matches the actual
architecture: the FastAPI service translates a quirky third-party API into clean REST and holds no
state of its own; the frontend is where the product's real data model, users, and business logic
will live.

## Consequences

- Moving `.venv` broke it (Windows venvs embed absolute paths) — had to delete and recreate it
  inside `backend/` after the move. If any future move/rename happens again, expect the same and
  just recreate the venv rather than debugging it.
- `backend/docs/API.md` and `frontend/README.md` both got a short blurb on the adapter/system-of-record
  split so a reader of either side alone still gets the architecture.
- Root `README.md` is the map of the monorepo — check it first in a new session before assuming
  the old flat (pre-monorepo) layout.

## Related records

`CTX-FCT-20260904-route-inventory` (paths now live under `backend/app/...`, not `app/...`),
`branches/frontend-nextjs-prisma/_index.md`.
