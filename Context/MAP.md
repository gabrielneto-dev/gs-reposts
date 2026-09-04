# Context Map

Routing layer only. See `Context/README.md` for how to use this, and `Context/STATE.md` for current status. Do not put detailed knowledge here.

## Project

- Overview: `core/overview.md`
- Goals: `core/goals.md`
- Constraints: `core/constraints.md`
- Glossary: `core/glossary.md`
- Current state: `STATE.md`

## Branches

- `nextrouter-api` — the FastAPI adapter (`backend/`) fronting the NextRouter C4 SoftSwitch. See
  `branches/nextrouter-api/_index.md`.
- `metrics-pipeline` — the Postgres storage + scheduler (`backend/app/db/`, `backend/app/scheduler/`)
  that periodically collects ASR/ACD/PDD per client. `backend/` is now the system of record. See
  `branches/metrics-pipeline/_index.md`.
- `frontend-nextjs-prisma` — the Next.js frontend (`frontend/`). No database/ORM anymore (Prisma
  removed 2026-09-04) — a pure consumer of `backend/`'s API. See
  `branches/frontend-nextjs-prisma/_index.md`.

## Global (cross-cutting)

- Open questions: `global/questions/` — none currently open.
- Assumptions: `global/assumptions/`
  - `ASM-20260903-project-domain-reports.md` — superseded, see
    `branches/nextrouter-api/facts/FCT-20260904-project-purpose-confirmed.md`.
- Decisions: `global/decisions/`
  - `DEC-20260904-monorepo-restructure.md` — backend/frontend split.
  - `DEC-20260904-backend-owns-storage-and-scheduler.md` — amends the above: backend also owns
    storage/scheduling now; frontend has no database.
- Plans: `global/plans/` — none yet.
- Risks: `global/risks/` — none global; see each branch's `risks/`/`_index.md` for branch-scoped risks.

## Checkpoints

- Latest: `checkpoints/CP-20260904-1800-metrics-storage-and-scheduler.md`
- Prior: `checkpoints/CP-20260904-1700-monorepo-and-frontend-scaffold.md`,
  `checkpoints/CP-20260904-1500-fastapi-nextrouter-mvp.md`,
  `checkpoints/CP-20260903-0000-bootstrap.md`
