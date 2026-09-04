---
id: CTX-DEC-20260904-activity-detection-day-by-day
type: decision
title: Detect "which clients were active" via sampled unfiltered scans; use exact per-day limit=1 checks when a specific client_id is given
branch: nextrouter-api
tags: [sampling, api-design, clients, production-safety]
status: active
confidence: high
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-FCT-20260904-cdr-api-behavior, CTX-DEC-20260904-sampling-with-exact-mode]
depends_on: []
supersedes: null
superseded_by: null
---

# Decision

## Context

The NextRouter API has no "distinct customer_id in period X" endpoint and no `customer_id` field
on the one endpoint (`/api/onlineCalls`) that shows current in-progress calls. Two different needs
came up: (a) "who's active right now / in this window" (discovery, unknown target), and (b) "did
*this specific* client use the service on *these* days" (verification, known target).

## Decision

Two different strategies depending on whether `cliente_id` is known:

- **Discovery** (`/api/clientes/atividade`, `/api/clientes/recorrencia` without `cliente_id`):
  fetch an unfiltered sample (`limite_scan`, default 3000, max 10000) from both `/api/cdr` and
  `/api/cdrDisconnection` for the window, count `customer_id` occurrences client-side, rank by
  volume. For the multi-day recurrence case, this sample is taken **once per day** (not once for
  the whole range) to avoid the "sample biased toward the start of a long period" problem — see
  `CTX-FCT-20260904-cdr-api-behavior` point 2. Day-by-day fan-out is bounded by
  `asyncio.Semaphore(CONCORRENCIA_MAXIMA_DIAS=5)`, and the whole date range is capped at
  `MAX_DIAS_RECORRENCIA=31` days per request.
- **Verification** (`/api/clientes/recorrencia?cliente_id=...`): skip sampling entirely. For each
  day, issue two `limit=1` requests (one per endpoint, filtered to that `cliente_id`) and just
  check whether `total_records > 0` for either. This is **exact, not sampled**, and cheap (no
  records downloaded, just two tiny aggregate reads per day).
- `/api/clientes/recorrencia` also accepts a `janela_dias` shortcut (last N days ending today,
  computed with Python's own `date.today()` at request time — not by omitting `date_end` and
  relying on the softswitch's own "today," to avoid the failure mode in
  `CTX-RSK-20260904-missing-date-fim-runaway-query`) as an alternative to explicit
  `data_inicio`/`data_fim`.

## Rationale

Directly requested by the user after they pointed out that if you already know which client you
care about, you shouldn't need to pull "all the calls" just to answer a yes/no activity question.
Verified live: the exact per-client-per-day path ran in ~6-18s for a 7-day window (varies with
concurrency/network), matching results already established via the (heavier) discovery path for
the same clients (Setra id=256: active 5/7 days, missing the weekend; Sendwork id=254: active
7/7 days).

## Consequences

- Discovery-mode results always carry an `aviso` warning about sampling bias, especially for
  windows > 1 day.
- If a caller already knows the `cliente_id`s they care about, always prefer passing `cliente_id`
  to `/recorrencia` — it's strictly cheaper and exact, not just more convenient.

## Related records

`CTX-FCT-20260904-cdr-api-behavior`, `CTX-DEC-20260904-sampling-with-exact-mode`.
