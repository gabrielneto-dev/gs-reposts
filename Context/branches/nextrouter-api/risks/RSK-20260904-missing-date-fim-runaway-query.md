---
id: CTX-RSK-20260904-missing-date-fim-runaway-query
type: risk
title: Omitting date_fim lets the NextRouter API default to "today" dynamically, which can silently balloon a query
branch: nextrouter-api
tags: [production-safety, api-quirks, incident]
status: active
confidence: verified
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-FCT-20260904-cdr-api-behavior, CTX-DEC-20260904-sampling-with-exact-mode]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-04
valid_until: null
revisit_at: null
---

## Risk

**Description**: If a caller (or a test/debug script) omits `date_end` when querying
`/api/cdr` or `/api/cdrDisconnection`, the NextRouter API defaults it to "today," evaluated
dynamically **at request time on the softswitch's own clock** — not the date implied by whatever
`date_ini` was passed. Over a long-running session/process, "today" can silently drift later than
what the caller intended, turning what was meant to be a narrow window (e.g. 15 minutes) into a
much wider one (observed: 15-minute intent became a multi-day span, ~18x more failure records
than expected).

**Impact**: A follow-up query with `exato=true` (full pagination) inherited the same missing
parameter and ran for 2+ minutes against production before being caught and stopped by killing
the local server process (which forcibly drops the in-flight HTTP connections to the softswitch —
killing the local `curl` client alone does *not* stop server-side work already in progress, since
FastAPI/uvicorn does not cancel a handler just because the client disconnected).

**Likelihood**: Medium — easy mistake to make ad hoc (e.g. via curl/Bruno) even though the FastAPI
routes in this project always require explicit params where it matters; the risk is in manual
testing and in any future direct API exploration, not in the shipped routes themselves.

**Mitigation**:
1. Always pass `date_ini`/`date_end` (or the FastAPI routes' `data_inicio`/`data_fim`) explicitly
   when testing or scripting against the NextRouter API directly — never rely on its default.
2. Where "last N days" is a legitimate need (`/api/clientes/recorrencia`'s `janela_dias`), resolve
   the date range in **this app's own code** using Python's `date.today()` at request time, and
   pass fully explicit dates to the softswitch — never lean on the softswitch's own default.
3. If a long-running/expensive query needs to be aborted, restarting the local uvicorn process is
   the reliable way to stop it — don't assume killing a client-side test tool is sufficient.

## Related records

`CTX-FCT-20260904-cdr-api-behavior` (point 4), `CTX-DEC-20260904-sampling-with-exact-mode`.
