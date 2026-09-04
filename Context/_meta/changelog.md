# Context System Changelog

Structural changes to the memory system itself (schema, taxonomy, branch creation/removal, migrations). Not a log of project work — see `checkpoints/` for that.

## 2026-09-03 — Bootstrap

- Installed the context engineering system (`AGENTS.md`, `CLAUDE.md`, `Context/`) into an empty project directory.
- No branches created yet — no domain exists in the project to branch on.
- Opened `CTX-QUE-20260903-project-purpose` and `CTX-ASM-20260903-project-domain-reports` pending clarification of project scope.

## 2026-09-04 — First real branch: nextrouter-api

- Project purpose established: a FastAPI reporting API fronting a NextRouter C4 SoftSwitch for a
  VoIP telephony company (GS VoIP). Closed `CTX-QUE-20260903-project-purpose` (answered),
  superseded `CTX-ASM-20260903-project-domain-reports`.
- Created `Context/branches/nextrouter-api/` with `facts/`, `decisions/`, `research/`, `risks/`
  records covering the built API's route surface, the NextRouter API's real (undocumented)
  behavior, and the sampling/exact-mode design.
- Added a `domain` tag group to `_meta/taxonomy.yaml` (fastapi, nextrouter, softswitch, telephony,
  asr, acd, pdd, cdr, clients, api-design, api-quirks, sampling, production-safety, nextqualify,
  incident, research).
- Rewrote `core/overview.md`, `core/goals.md`, `core/constraints.md`, `core/glossary.md` from
  bootstrap placeholders to real content.
- First non-bootstrap checkpoint: `CTX-CP-20260904-1500-fastapi-nextrouter-mvp`.
