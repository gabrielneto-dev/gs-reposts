---
id: CTX-RSK-20260904-transient-network-failures-during-collection
type: risk
title: Occasional transient connection failures observed on this Windows dev machine during concurrent async I/O
branch: metrics-pipeline
tags: [production-safety, windows, api-quirks]
status: active
confidence: medium
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: []
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-04
valid_until: null
revisit_at: null
---

## Risk

**Description**: Twice during this session, concurrent async network I/O on this Windows dev
machine failed with a low-level connection error that a retry (or running the same call alone,
sequentially) did not reproduce:

1. `asyncpg`/SQLAlchemy async engine: `ConnectionDoesNotExistError: connection was closed in the
   middle of operation` (also seen as a raw `WinError 64` / `ConnectionResetError` from
   `asyncio.windows_events`) when Alembic first tried to connect. This particular instance turned
   out to be a **red herring** — the real cause was a wrong role password (confirmed once by
   getting a clean `password authentication failed` from `psql` instead). But the error's *surface
   shape* (connection reset mid-handshake) looked identical to case 2 below, which was NOT a
   credentials problem.
2. During a real collection job run (5-way concurrent `httpx` clients fetching from
   `sip5.gsvoip.com.br`), 2 of 72 clients failed with `NextRouterAPIError`: "Falha ao conectar com
   a API do softswitch: All connection attempts failed." The exact same call for one of those two
   clients, run alone/sequentially moments later, succeeded immediately.

**Impact**: A `collection_windows` row can end up `status=partial` with 1-2 clients silently
missing their metrics for that window, even though nothing is actually wrong with the softswitch
or the query logic. The job already handles this without crashing (per-client errors are caught,
logged, and reflected in `clients_processed < clients_discovered` + `status=partial`) — but there's
no retry, so a transient blip becomes a permanent gap in that window's data.

**Likelihood**: Low per individual client-fetch, but non-zero every run given ~5-way concurrency,
14 runs/day, and a variable number of discovered clients per window.

**Mitigation**:
1. Don't assume a connection-reset-shaped error is a credentials or config problem — rule out
   "wrong password" (or similar hard failure) with a *sequential, single* retry of the exact same
   operation before spending time on root-causing a transient network layer issue.
2. Not yet implemented: a retry (1-2 attempts, small backoff) around `get_exact_metrics_for_client`
   inside the scheduler job would likely close most of this gap cheaply. Worth adding if `partial`
   windows turn out to be common in practice — check `collection_windows.status`/`error_message`
   after the pipeline has run unattended for a while before deciding whether this is worth the
   added complexity.

## Related records

`branches/metrics-pipeline/facts/FCT-20260904-schema-and-reused-functions.md`.
