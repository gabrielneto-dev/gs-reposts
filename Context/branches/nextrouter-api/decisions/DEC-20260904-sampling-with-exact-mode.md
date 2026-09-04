---
id: CTX-DEC-20260904-sampling-with-exact-mode
type: decision
title: Use bounded sampling by default for metrics with no API aggregate, with an opt-in exact/full-scan mode
branch: nextrouter-api
tags: [sampling, production-safety, asr, pdd, api-design]
status: active
confidence: high
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-FCT-20260904-cdr-api-behavior, CTX-FCT-20260904-route-inventory]
depends_on: []
supersedes: null
superseded_by: null
---

# Decision

## Context

Several metrics have no aggregate endpoint on the NextRouter API (see
`CTX-FCT-20260904-cdr-api-behavior`): the per-code ASR breakdown, the PDD average, and "which
clients had activity in period X" all require inspecting individual `cdrDisconnection` records,
and failure volumes can be enormous (hundreds of thousands to millions of records per
client/period).

## Problem

Downloading every failure record to compute an exact number can take minutes and puts real load
on the customer's production softswitch (this was explicitly flagged as a concern by the user).
But an estimate is often good enough for monitoring, while some use cases (billing disputes,
incident postmortems) need an auditable exact number.

## Options considered

1. Always sample (fast, cheap, never exact) — rejected, no way to get a trustworthy number when needed.
2. Always fetch everything (exact, simple) — rejected, too slow/heavy by default (a single query
   once took 2+ minutes and had to be killed mid-flight during testing — see the runaway-query risk).
3. Sample by default, opt-in exact mode via a query param — **chosen**.

## Decision

- Default: take a bounded sample (`limit` param, e.g. `amostra_falhas`/`amostra`, default 1000,
  user-adjustable up to 5000) from `/api/cdrDisconnection` and compute the metric from that.
- Opt-in: `exato=true` ignores the sample size and paginates through **all** matching records in
  pages of `TAMANHO_PAGINA_EXATO=10000` (the API's real max — see the quirks fact), sequentially
  (not parallel, to avoid hammering the softswitch), capped at `MAX_PAGINAS_EXATO=100` pages
  (1,000,000 records) as a safety net, with a `truncado: true` flag if that cap is hit.
- Every response that used sampling/exact carries transparency fields (`exato`, `tamanho_amostra*`,
  `aviso`) so the caller always knows whether a number is exact or estimated.
- The overall ASR percentage itself (`total_atendidas`/`total_falhas`/`asr_percentual`) is always
  exact regardless of mode — only the *breakdown* is sampled, because `total_records` is a cheap
  aggregate on both `/api/cdr` and `/api/cdrDisconnection` even with `limit=1`.

## Rationale

Matches how the user actually wants to work: fast/cheap for routine monitoring, exact on demand
for cases that need an auditable number, with the cost tradeoff always visible rather than hidden.

## Consequences

- Sample-based numbers can meaningfully misrepresent the true distribution in a single narrow
  sample — demonstrated live: a 1000-record sample showed SIP 403 as the top failure code (40.7%),
  while the exact full scan showed 487 (39%) and 503 (37.5%) actually dominating. Document this
  caveat wherever sampling is used; don't treat sample proportions as precise.
- `exato=true` timing measured live: ~3s per 10,000-record page. A single client-hour with ~92k
  failures took ~20-30s exact; a full day for a busy client could take minutes — communicate this
  to callers before they flip the flag on a wide date range.

## Related records

`CTX-FCT-20260904-cdr-api-behavior`, `CTX-RSK-20260904-missing-date-fim-runaway-query`.
