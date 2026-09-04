---
id: CTX-DEC-20260904-sampled-discovery-exact-client-metrics
type: decision
title: Discover active clients by sampling, but fetch each discovered client's ASR/ACD/PDD exactly
branch: metrics-pipeline
tags: [sampling, production-safety, asr, pdd, api-design]
status: active
confidence: high
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-DEC-20260904-sampling-with-exact-mode, CTX-DEC-20260904-activity-detection-day-by-day]
depends_on: []
supersedes: null
superseded_by: null
---

# Decision

## Context

The collection job has two phases per window: (1) find which clients had any traffic (unknown
target, needs a scan), (2) fetch ASR/ACD/PDD for each one found (known target, one client at a
time). `nextrouter-api`'s existing pattern (`CTX-DEC-20260904-sampling-with-exact-mode`,
`CTX-DEC-20260904-activity-detection-day-by-day`) already draws exactly this discovery-vs-
verification distinction for the HTTP routes — this decision applies the same split here, with one
change: discovery uses a bigger sample since the job isn't blocking a user request.

## Decision

- **Discovery**: `scan_active_customer_ids(periodo, limite_scan)` — unfiltered sample of both
  `/api/cdr` and `/api/cdrDisconnection`, same function the `/api/clientes/atividade` route uses.
  `limite_scan` defaults to `SCHEDULER_SCAN_LIMIT=10000` (the API's real per-request cap) instead
  of the route's interactive default of 3000, since a background job can afford the extra cost.
- **Per-client metrics**: `get_exact_metrics_for_client(cliente_id, periodo)` — filtered by
  `cliente_id`, narrow window (1h or the 11h overnight window), exact (pages ALL matching
  `cdrDisconnection` records via `get_disconnection_full`, uses `get_cdr_aggregate`'s exact
  `total_records`/`total_time`). No sampling here at all.
- Bounded concurrency across clients: `asyncio.Semaphore(SCHEDULER_CLIENT_CONCURRENCY=5)`, same
  style as `routers/clientes.py`'s day-fan-out semaphore.
- Every stored row keeps `occurrences_discovery` (how many times that client showed up in the
  discovery sample) for transparency, mirroring the `aviso`/`exato` transparency fields the
  existing routes already carry.

## Rationale

Exact-per-client is only expensive when it's *unfiltered* or spans a *wide date range* — neither
is true here (always one client, always ≤11h). So there was no real cost tradeoff to sampling the
per-client fetch; only the "who's active" scan (which genuinely has to look at the whole unfiltered
firehose) still needs sampling.

## Consequences

- If total traffic within a single window exceeds `limite_scan` before a low-volume client's
  records appear in the unfiltered sample, that client can be missed entirely for that window —
  not just under-counted. Verified live on 2026-09-04: a 1-hour window with `limite_scan=10000`
  found 72 clients and stored exact metrics for 70 (2 failed on network, not on discovery) — no
  evidence of missed clients at this traffic level, but this hasn't been stress-tested at a busier
  hour.
- Every stored metric row is exact, not an estimate — this pipeline's numbers can be trusted as-is
  for reporting, unlike the sampled `disposicoes` breakdown in `/api/asr`'s default mode.

## Related records

`CTX-DEC-20260904-sampling-with-exact-mode`, `CTX-DEC-20260904-activity-detection-day-by-day`,
`facts/FCT-20260904-schema-and-reused-functions.md`.
