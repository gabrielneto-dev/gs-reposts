# Goals

**Status: established** (2026-09-04).

## Goals

- Provide accurate, cheap-by-default (sampled) telephony metrics (ASR/ACD/PDD) per client and
  period, with an opt-in exact mode for auditable numbers.
- Provide client lookup/discovery: by raw listing, by name (fuzzy), by activity in a period, and
  by recurrence (active on >= N of the last M days).
- Keep the route surface small and predictable: one endpoint per concern with its own response
  shape, rather than combined/mode-switching endpoints. See
  `Context/branches/nextrouter-api/decisions/DEC-20260904-route-simplification.md`.
- Be safe against the fact that every call this API makes is a real call against the company's
  production softswitch — no staging environment exists.

## Non-goals

- Write/mutating operations against the softswitch (billing changes, hanging up calls, editing
  customers) — this project is read-only by design.
- Reproducing NextQualify's `graph-pizza` aggregate — the company doesn't have that product; see
  `Context/branches/nextrouter-api/research/RES-20260904-asr-aggregate-endpoint-search.md`.

## Success criteria

- Each route verified against the real production API with real client data, not just unit-tested
  in isolation (this has been the practice throughout — see the branch's fact/decision records).
