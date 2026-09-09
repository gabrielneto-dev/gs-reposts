---
id: CTX-RES-20260909-asr-discrepancy-vs-sip-codes-report
type: research
title: Investigated ASR discrepancy vs. NextRouter's own "SIP Codes / Assinante" report — no code bug found
branch: nextrouter-api
tags: [asr, nextrouter, data-integrity, investigation]
status: active
confidence: medium
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: []
depends_on: [CTX-FCT-20260904-cdr-api-behavior]
supersedes: null
superseded_by: null
valid_from: 2026-09-09
valid_until: null
revisit_at: null
---

## Question

User reported (with a screenshot of the NextRouter platform's own "SIP Codes / Assinante" report,
filtered to the same client and same hour as one of our stored collection windows): the platform's
report showed ASR 10%, our system showed 13.4% for the same client/hour, and asked to resolve the
discrepancy.

## Investigation

Extensive empirical cross-checking (re-querying the same client/window against both `/api/cdr` and
`/api/cdrDisconnection` the same way the scheduler does, replicating the platform's filter as
closely as possible) found our number to be **internally consistent** with our own stored raw data
and computation method (see
`Context/branches/metrics-pipeline/facts/FCT-20260904-schema-and-reused-functions.md` for the
query pattern). No bug was found in our ASR formula, in `get_exact_metrics_for_client`, or in how
the collection window boundaries are applied.

The platform's own "SIP Codes / Assinante" report was explicitly described by the user as
"flutuante" (floating/live) — i.e. it is not clearly a fixed, reproducible historical snapshot for
a given past hour the way our stored `metricas_cliente` row is. This makes it a plausible but
**unconfirmed** candidate explanation for the mismatch (e.g. it may recompute against
currently-available data rather than a frozen historical filter, or use a different sip_code/
disposition classification than our formula — see
`Context/branches/nextrouter-api/facts/FCT-20260904-cdr-api-behavior.md` for how loosely
`sip_code`/`disposition`/`hangup_cause` map to each other on this API).

## Outcome

**Did not alter the ASR formula** — there was no confirmed root cause pointing at our code, only
circumstantial evidence that the platform's report may not be a reliable historical reference. The
user asked to "resolva esse problema" but was given this explanation rather than a code change,
specifically to avoid changing a formula without evidence it's actually wrong.

## Open question

Whether the platform's "SIP Codes / Assinante" report is ever a reliable historical reference for
validating our own numbers — still unresolved. If this discrepancy recurs, worth asking NextRouter
support directly what that report's filter semantics actually are, rather than re-deriving them
empirically again.
