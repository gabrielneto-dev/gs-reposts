# Branch: nextrouter-api

## Purpose

Everything related to the FastAPI reporting service that queries the NextRouter C4 SoftSwitch
(NextBilling IP Solutions) to expose telephony metrics (ASR, ACD, PDD) and client lookups for
"relatorios" — a VoIP company (GS VoIP, softswitch at `sip5.gsvoip.com.br`).

## Scope

- The FastAPI app under `backend/app/` (config, clients, routers, schemas, utils) — moved here
  from the repo root on 2026-09-04, see `Context/global/decisions/DEC-20260904-monorepo-restructure.md`
- How the NextRouter API actually behaves (vs. what its Confluence docs claim)
- Design decisions about sampling, exact modes, and production-load safety
- The final route inventory and what each returns

## Current state

Working MVP: 8 GET routes, tested against production with real client data. See
`facts/FCT-20260904-route-inventory.md` for the exact list. Documented for external consumers in
`backend/docs/API.md` (not in Context — it's a deliverable, not project memory). Lives in the
`backend/` half of the monorepo — see `Context/branches/frontend-nextjs-prisma/` for the other half.

## Core concepts

- **ASR / ACD / PDD** — see `Context/core/glossary.md`.
- **Sampled vs. exact**: several metrics (PDD, per-code ASR breakdown, "who's active") have no
  aggregate endpoint on this NextRouter instance, so they're computed from a bounded sample by
  default, with an opt-in exact/full-scan mode. See `decisions/DEC-20260904-sampling-with-exact-mode.md`.
- **NextRouter API quirks** discovered empirically — see `facts/FCT-20260904-cdr-api-behavior.md`.
- A fuzzy client-name-search bug (false positives from arbitrary substring matching) was found and
  fixed during this work — see the "Problems solved" section of
  `Context/checkpoints/CP-20260904-1500-fastapi-nextrouter-mvp.md`; the fix lives in
  `backend/app/utils/fuzzy.py`.

## Key records

- `facts/FCT-20260904-project-purpose-confirmed.md`
- `facts/FCT-20260904-route-inventory.md`
- `facts/FCT-20260904-cdr-api-behavior.md`
- `decisions/DEC-20260904-sampling-with-exact-mode.md`
- `decisions/DEC-20260904-route-simplification.md`
- `decisions/DEC-20260904-activity-detection-day-by-day.md`
- `research/RES-20260904-asr-aggregate-endpoint-search.md`
- `risks/RSK-20260904-missing-date-fim-runaway-query.md`

## Active decisions

See the `decisions/` records above — all still active as of 2026-09-04.

## Open questions

None currently open in this branch.

## Risks

- `risks/RSK-20260904-missing-date-fim-runaway-query.md` — omitting `data_fim` lets the softswitch
  API default to "today" dynamically, which can silently balloon a query's scope.
- **Production caution**: `sip5.gsvoip.com.br` is the company's real production softswitch. Every
  request this API makes is a real request against it — no staging/sandbox exists. Keep read-only
  (GET only, never call the `DELETE /api/onlineCalls/.../{id}` hangup endpoint or any `manage*`
  write endpoint) and mind query cost (see the sampling decision).

## Relations to other branches

- `frontend-nextjs-prisma` — the other half of the monorepo. Will eventually call this backend's
  HTTP endpoints for softswitch data; no integration code exists yet.
