---
id: CTX-DEC-20260904-route-simplification
type: decision
title: Collapse the API to 4 focused resources (clientes/asr/acd/pdd) instead of broader combined/bulk routes
branch: nextrouter-api
tags: [api-design, fastapi]
status: active
confidence: high
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-FCT-20260904-route-inventory]
depends_on: []
supersedes: null
superseded_by: null
---

# Decision

## Context

Earlier in the session, in response to a request for an hourly-cron-friendly view ("who's active
right now, with their ASR/ACD/PDD"), three broader routes were built and verified working against
production: `/api/metricas` (combined ACD+PDD), `/api/relatorio-horario` (bulk report over
auto-detected active clients for one hour window), `/api/serie-diaria` (day-by-day time series
for an arbitrary period with a resummarized total).

## Decision

The user explicitly asked to revert to a simpler shape: separate `/api/acd` and `/api/pdd`
routes (no combined metrics route), and to drop `/api/relatorio-horario` and `/api/serie-diaria`
entirely, keeping only `clientes` (later split further into 4 sub-resources — see
`CTX-DEC-20260904-activity-detection-day-by-day`), `asr`, `acd`, `pdd`, plus `/health`.

## Rationale

User preference for a narrower, more predictable surface area over a small number of
general-purpose combined routes carrying lots of optional/mode-switching parameters. Later in the
session this same principle was applied again: `/api/clientes`'s 4 modes (raw listing, fuzzy
search, single-window activity, N-of-M-day recurrence) were split into 4 distinct endpoints
(`/api/clientes`, `/busca`, `/atividade`, `/recorrencia`) with per-mode response schemas, instead
of one endpoint switching behavior based on which optional params were set.

## Consequences

- Don't resurrect `/api/metricas`, `/api/relatorio-horario`, `/api/serie-diaria` without checking
  with the user first — they were deliberately cut, not abandoned due to a bug. Their logic
  (active-client scanning, day-by-day looping with bounded concurrency) is still useful reference
  if similar functionality is requested again — note there is no git repo in this project, so the
  removed files' content only exists in this conversation's transcript, not on disk.
- General pattern established for this project: prefer one endpoint per concern, with its own
  response schema, over one endpoint with several optional-parameter-triggered modes.

## Related records

`CTX-FCT-20260904-route-inventory`.
