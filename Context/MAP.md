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
- `frontend-nextjs-prisma` — the Next.js + Prisma 8 + Postgres frontend (`frontend/`), the
  project's system of record. See `branches/frontend-nextjs-prisma/_index.md`.

## Global (cross-cutting)

- Open questions: `global/questions/` — none currently open.
- Assumptions: `global/assumptions/`
  - `ASM-20260903-project-domain-reports.md` — superseded, see
    `branches/nextrouter-api/facts/FCT-20260904-project-purpose-confirmed.md`.
- Decisions: `global/decisions/`
  - `DEC-20260904-monorepo-restructure.md` — backend/frontend split.
- Plans: `global/plans/` — none yet.
- Risks: `global/risks/` — none global; see each branch's `risks/`/`_index.md` for branch-scoped risks.

## Checkpoints

- Latest: `checkpoints/CP-20260904-1700-monorepo-and-frontend-scaffold.md`
- Prior: `checkpoints/CP-20260904-1500-fastapi-nextrouter-mvp.md`,
  `checkpoints/CP-20260903-0000-bootstrap.md`
