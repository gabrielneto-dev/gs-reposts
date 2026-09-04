# Context Map

Routing layer only. See `Context/README.md` for how to use this, and `Context/STATE.md` for current status. Do not put detailed knowledge here.

## Project

- Overview: `core/overview.md`
- Goals: `core/goals.md`
- Constraints: `core/constraints.md`
- Glossary: `core/glossary.md`
- Current state: `STATE.md`

## Branches

- `nextrouter-api` — the FastAPI reporting service (ASR/ACD/PDD/clients) fronting the NextRouter
  C4 SoftSwitch. See `branches/nextrouter-api/_index.md`.

## Global (cross-cutting)

- Open questions: `global/questions/` — none currently open (`QUE-20260903-project-purpose.md`
  answered).
- Assumptions: `global/assumptions/`
  - `ASM-20260903-project-domain-reports.md` — superseded, see
    `branches/nextrouter-api/facts/FCT-20260904-project-purpose-confirmed.md`.
- Decisions: `global/decisions/` — none (project-specific decisions live in the `nextrouter-api` branch).
- Plans: `global/plans/` — none yet.
- Risks: `global/risks/` — none global; see `branches/nextrouter-api/risks/` for branch-scoped risks.

## Checkpoints

- Latest: `checkpoints/CP-20260904-1500-fastapi-nextrouter-mvp.md`
- Prior: `checkpoints/CP-20260903-0000-bootstrap.md`
