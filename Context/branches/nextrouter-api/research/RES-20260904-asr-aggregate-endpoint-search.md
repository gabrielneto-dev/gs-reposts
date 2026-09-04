---
id: CTX-RES-20260904-asr-aggregate-endpoint-search
type: research
title: Search for a ready-made, aggregate ASR-by-code endpoint (the "pizza" breakdown)
branch: nextrouter-api
tags: [nextrouter, nextqualify, asr, research]
status: active
confidence: high
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-FCT-20260904-cdr-api-behavior]
---

## Question investigated

Does an endpoint exist (on this company's stack) that returns an aggregate ASR breakdown by SIP
code/disposition (e.g. "200: 850, 404: 10, 480: 40, 486: 30, 487: 50, 503: 20") without needing to
sample or paginate raw CDR records?

## Scope

Searched the company's Atlassian/Confluence documentation (`nextbilling.atlassian.net`, spaces
`NEXTROUTER - v5` / NR5, `NextRouter C4 SoftSwitch`, `NextQualify`, `NextBilling v3`) and tested
candidate endpoints live against the production softswitch (`sip5.gsvoip.com.br`).

## Findings

- **NextQualify** (a separate NextBilling product — a call-quality/anti-spam classifier, not the
  softswitch itself) has exactly this: `GET /api/reports/asr/customers/graph-pizza` and
  `GET /api/reports/asr/trunks/graph-pizza`, returning `{"data": [{"name": "200 - Atendidas",
  "value": 850, "itemStyle": {...}}, ...]}` — a ready aggregate, no sampling needed. Auth is
  `Authorization: Bearer {access_token}` (JWT via a separate login endpoint), not the
  `api_token`/`api_key`-in-URL pattern used by NextRouter/NextBilling.
- Confirmed live that `graph-pizza` does **not** exist on `sip5.gsvoip.com.br` (404, both with and
  without token/key in the URL) — it is genuinely hosted by a different product/service, not just
  a different path on the same server.
- Asked the user directly: **the company does not have a NextQualify account/instance** — only
  NextRouter. So this endpoint is not usable for this project as things stand.
- Also re-confirmed (see `CTX-FCT-20260904-cdr-api-behavior`) that the NextRouter-native "ready"
  endpoints (`RelatorioASR`, `RelatorioASRAssinantes`) 404 on this instance too.

## Limitations

Only this one company's specific instances were checked. A different NextRouter/NextBilling
customer's deployment could have `RelatorioASR`/`RelatorioASRAssinantes` actually enabled, or a
NextQualify subscription — don't generalize "doesn't exist" beyond this project's environment.

## Confidence

High for "not currently available to this project" — verified live, not just from docs, and
directly confirmed by the user for the NextQualify case.

## Implications

The sampled/exact-opt-in approach in `CTX-DEC-20260904-sampling-with-exact-mode` is the right
solution given current constraints, not a workaround for something that should have been found
instead. Revisit only if the company acquires a NextQualify subscription, or if NextBilling
support confirms `RelatorioASR`/`RelatorioASRAssinantes` can be enabled on this account (ASR-by-code
via a `?disposition=` filter was also tested and does not work either — see the quirks fact).

## Open questions remaining

None — closed by the user's direct answer ("não temos, só uso o NextRouter mesmo").
