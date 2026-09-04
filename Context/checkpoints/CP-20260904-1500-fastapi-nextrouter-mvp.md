---
id: CTX-CP-20260904-1500-fastapi-nextrouter-mvp
type: checkpoint
title: FastAPI NextRouter reporting MVP built and verified against production
status: active
created_at: 2026-09-04
updated_at: 2026-09-04
tags: [fastapi, nextrouter, asr, acd, pdd, clients]
---

# Session Checkpoint

## Objective

Build a reporting API for GS VoIP (telephony company) that fronts their NextRouter C4 SoftSwitch
and exposes ASR/ACD/PDD metrics and client lookups, starting from a completely empty project.

## What changed

- Project purpose established (was fully unknown at bootstrap) — see
  `CTX-FCT-20260904-project-purpose-confirmed`.
- Built a working FastAPI app (`app/`) with `.env`-based config (`app/config.py`, pydantic-settings),
  an async httpx client wrapper for the NextRouter API (`app/clients/nextrouter.py`), and 8 GET
  routes across `app/routers/{asr,acd,pdd,clientes}.py` + `/health` in `app/main.py`.
- Iterated the route surface significantly: built and verified `/api/metricas`,
  `/api/relatorio-horario`, `/api/serie-diaria`, then removed all three at the user's request in
  favor of a leaner `clientes`/`asr`/`acd`/`pdd` shape (see
  `CTX-DEC-20260904-route-simplification`). `/api/clientes` itself was later split from one
  multi-mode endpoint into 4 dedicated ones (`/api/clientes`, `/busca`, `/atividade`,
  `/recorrencia`).
- Added `docs/API.md` (project root) — full external-facing route documentation with real
  examples, not duplicated here in Context (Context holds the *why*, not the consumer docs).

## Decisions

- `CTX-DEC-20260904-sampling-with-exact-mode` — sampled by default, `exato=true` opt-in for
  metrics with no API aggregate (PDD, ASR-by-code breakdown, activity discovery).
- `CTX-DEC-20260904-route-simplification` — 4 focused resources instead of combined/bulk routes.
- `CTX-DEC-20260904-activity-detection-day-by-day` — exact+cheap `limit=1` checks when a specific
  `cliente_id` is known; sampled discovery scan otherwise, done per-day for multi-day windows.

## Discoveries

- `CTX-FCT-20260904-cdr-api-behavior` — the NextRouter API's real (undocumented) behavior: 10,000
  hard cap on `limit`, multi-day `time_ini`/`time_end` only bounds the first/last day, no
  server-side disposition/sip_code filter, `date_end` defaults to "today" dynamically if omitted,
  PDD/sip_code/disposition only exist on failed-call records.
- `CTX-RES-20260904-asr-aggregate-endpoint-search` — a ready aggregate ASR-by-code endpoint
  (`graph-pizza`) exists, but on a different product (NextQualify) the company doesn't use;
  confirmed the NextRouter-native "ready" report endpoints (`RelatorioASR*`) 404 on this specific
  instance even though Confluence documents them.
- The company's Confluence (`nextbilling.atlassian.net`) allows anonymous read access to most of
  the NextRouter/NextBilling/NextQualify documentation spaces — useful for future research without
  needing login credentials.

## Problems solved

- A naive "fuzzy" name-matching implementation for `/api/clientes/busca` produced false positives
  (e.g. "Setra" scoring 80% against "Administradora..." because of a coincidental "astra" inside
  "cadastrais") by comparing against arbitrary substrings of the full name. Fixed by comparing the
  search term against each *word* of the name individually (`app/utils/fuzzy.py`) — substring
  match still short-circuits to 100%, but fuzzy scoring no longer matches on accidental
  cross-word character runs. Verified before/after with real production client names.

## Failed approaches worth remembering

- Do not trust Confluence "ready-made report" endpoint docs for this product family without
  testing live first — two documented endpoints (`RelatorioASR`, `RelatorioASRAssinantes`) don't
  exist on this company's actual deployed instance.
- Don't compute "who was active over N days" from a single unfiltered sample spanning the whole N
  days — the sample is biased toward whatever the API's default ordering surfaces first (appears
  chronological), effectively only covering the start of the range. Must sample per-day instead.
- See `CTX-RSK-20260904-missing-date-fim-runaway-query` for the incident where omitting
  `date_fim` in an ad hoc test caused a query to balloon in scope and run for 2+ minutes against
  production; killing the client-side `curl` did not stop it — had to restart the local uvicorn
  server to actually cancel the in-flight requests to the softswitch.

## Current state

Working MVP, 8 GET routes, all verified against live production data (client examples used
throughout testing: id 256 = Setra Soluções em Atendimento — active weekdays only; id 254 =
Sendwork Serviços Digitais — active every day; id 588 = a low/no-traffic client, useful as a
negative test case). Server run via `uvicorn app.main:app --reload`; deps in `requirements.txt`;
credentials in `.env` (git-ignored). No git repository exists in the project yet.

## Open questions

None currently open.

## Next steps

Nothing specifically queued by the user as of this checkpoint. Natural candidates if the user
returns to this: initialize git (currently absent), add automated tests, consider
deployment/hosting, revisit NextQualify integration if the company acquires it later (see
`CTX-RES-20260904-asr-aggregate-endpoint-search`).

## Files or artifacts affected

`app/` (whole tree), `requirements.txt`, `.env`/`.gitignore`, `docs/API.md`.

## Context records created or updated

Created: `CTX-FCT-20260904-project-purpose-confirmed`, `CTX-FCT-20260904-route-inventory`,
`CTX-FCT-20260904-cdr-api-behavior`, `CTX-DEC-20260904-sampling-with-exact-mode`,
`CTX-DEC-20260904-route-simplification`, `CTX-DEC-20260904-activity-detection-day-by-day`,
`CTX-RES-20260904-asr-aggregate-endpoint-search`, `CTX-RSK-20260904-missing-date-fim-runaway-query`,
`branches/nextrouter-api/_index.md`.

Updated (closed/superseded): `CTX-QUE-20260903-project-purpose` (-> answered),
`CTX-ASM-20260903-project-domain-reports` (-> superseded).

Rewritten: `Context/core/overview.md`, `goals.md`, `constraints.md`, `glossary.md`,
`Context/STATE.md`, `Context/MAP.md`. Updated: `Context/_meta/taxonomy.yaml`,
`Context/_meta/catalog.jsonl`, `Context/_meta/changelog.md`.
