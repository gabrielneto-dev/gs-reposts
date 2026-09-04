---
id: CTX-FCT-20260904-cdr-api-behavior
type: fact
title: How the NextRouter CDR endpoints actually behave (undocumented quirks found empirically)
branch: nextrouter-api
tags: [nextrouter, softswitch, api-quirks, cdr]
status: active
confidence: verified
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-RES-20260904-asr-aggregate-endpoint-search, CTX-RSK-20260904-missing-date-fim-runaway-query]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-04
valid_until: null
revisit_at: null
---

## Fact

The company's NextRouter instance (`sip5.gsvoip.com.br`) is an older/NR5-generation deployment.
Two Confluence-documented "ready-made" report endpoints from the newer "NextRouter C4 SoftSwitch"
docs space — `/api/RelatorioASR/{token}/{key}` and `/api/RelatorioASRAssinantes/{token}/{key}` —
return 404 on this instance (confirmed live, not a credentials problem — `/api/getCustomerBalance`
and other NR5-era endpoints work fine with the same token/key). Do not assume Confluence docs for
this product family reflect what a given customer's instance actually has deployed — always
verify live before building against a new endpoint.

The two endpoints actually usable for metrics on this instance are both NR5-era CDR listings:

- `GET /api/cdr/{token}/{key}(/{cliente_id})` — **answered/billed calls only**. Aggregate fields
  `total_records`/`total_time` (with `limit=1`) are exact and cheap. Per-record fields do **not**
  include `pdd`, `sip_code`, or `disposition` — those simply aren't tracked for successful calls
  in this schema.
- `GET /api/cdrDisconnection/{token}/{key}(/{cliente_id})` — **failed calls only** ("disconnection
  report"). `total_records` is exact and cheap even with `limit=1`. Per-record fields include
  `pdd` (seconds), `sip_code` (e.g. "487", "480", "503"...), `disposition` (categorical: CONGESTION,
  CANCEL, NOANSWER, PDD, BUSY, NOTFOUND), `customer_id`, `trunk_id`.
- Both together give ASR: `atendidas.total_records / (atendidas.total_records + falhas.total_records) * 100`.
- `GET /api/contacts/{token}/{key}` — client registry (name, contact, address). No usage/activity
  data, no per-id filter — must be paginated and scanned client-side to look up specific ids.
- `GET /api/onlineCalls/{token}/{key}(/{cliente_id})` — live in-progress calls. Supports filtering
  by client id in the path, but per-record data has **no `customer_id` field** — can't reverse-map
  a call to a client from the unfiltered listing. Also exposes `DELETE /api/onlineCalls/{token}/{key}/{id}`
  which **hangs up a live call** — never call this; GET-only usage in this project.

## Undocumented API quirks (found by live testing, not in Confluence)

1. **`limit` hard cap at 10,000** on `/api/cdr` and `/api/cdrDisconnection`: values up to 10,000
   are honored; anything above (tested 20,000/50,000/100,000) is silently reduced to `limit: 200`
   in the response, without an error. Any "fetch everything" pagination logic must page in chunks
   of <=10,000 (`app/clients/nextrouter.py::TAMANHO_PAGINA_EXATO`).
2. **Multi-day `time_ini`/`time_end` only bound the edges, not every day**: querying
   `date_ini=D1&date_end=D2&time_ini=14:00&time_end=15:00` where D2 > D1 does NOT restrict every
   day in `[D1, D2]` to 14:00-15:00 — it only applies `time_ini` to D1 and `time_end` to D2; all
   days in between are unrestricted (full day). Confirmed by comparing total call counts with and
   without the hour filter over a 7-day span (barely changed). To get "same hour every day across
   N days," you must loop day-by-day, one single-day request per day.
3. **No server-side filter by `disposition` or `sip_code`**: passing `disposition=CONGESTION` or
   `sip_code=487` as query params is silently ignored (totals unchanged). There's also no
   aggregate-by-code endpoint. Any per-code breakdown (the ASR "pizza") must come from inspecting
   individual `cdrDisconnection` records — hence sampling (see
   `CTX-DEC-20260904-sampling-with-exact-mode`).
4. **Omitting `date_end` defaults to "today," evaluated dynamically at request time** — see
   `CTX-RSK-20260904-missing-date-fim-runaway-query` for the incident this caused.
5. Answered-call `duration` is billing-rounded (seen: `real_duration: 7` sec vs `duration: 30`
   sec for the same call) — the ACD calculation in this project intentionally uses the aggregate
   `total_time` (sum of billed `duration`), matching what the platform itself reports, not
   `real_duration`.
