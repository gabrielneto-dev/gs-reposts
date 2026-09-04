---
id: CTX-FCT-20260904-route-inventory
type: fact
title: Final route inventory of the relatorios FastAPI app (8 GET routes)
branch: nextrouter-api
tags: [fastapi, api-design, asr, acd, pdd, clients]
status: active
confidence: verified
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-DEC-20260904-route-simplification, CTX-DEC-20260904-monorepo-restructure]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-04
valid_until: null
revisit_at: null
---

## Fact

As of 2026-09-04 the app exposes exactly 8 GET routes (all read-only). Full parameter/response
docs live in `backend/docs/API.md` — this record is a pointer + summary, not a duplicate of that
doc (avoid re-deriving; read it directly for details).

**Path note**: the service moved from the repo root into `backend/` on 2026-09-04 (see
`CTX-DEC-20260904-monorepo-restructure`) — paths below are relative to `backend/`, not the repo
root.

| Route | File | Purpose |
|---|---|---|
| `GET /api/asr` | `app/routers/asr.py` | ASR + per-SIP-code breakdown ("pizza"), sampled by default, `exato=true` for full scan |
| `GET /api/acd` | `app/routers/acd.py` | Average call duration, always exact |
| `GET /api/pdd` | `app/routers/pdd.py` | Post-dial-delay average, sampled by default, `exato=true` for full scan |
| `GET /api/clientes` | `app/routers/clientes.py` | Raw paginated client registry listing |
| `GET /api/clientes/busca` | same file | Fuzzy name search |
| `GET /api/clientes/atividade` | same file | Clients active in one date/time window (sampled discovery) |
| `GET /api/clientes/recorrencia` | same file | Clients active on >= N distinct days within a window; day-by-day; exact+cheap when `cliente_id` given, sampled discovery otherwise |
| `GET /health` | `app/main.py` | App-only healthcheck, does not call NextRouter |

## Prior, now-removed routes (do not resurrect without checking why they were cut)

`/api/metricas` (combined ACD+PDD), `/api/relatorio-horario` (bulk hourly report across
auto-detected active clients), `/api/serie-diaria` (flexible day-by-day time series) were built,
tested working against production, then explicitly removed by the user in favor of the leaner
4-resource shape (clientes/asr/acd/pdd) above. See `CTX-DEC-20260904-route-simplification`.

## Verification

All 8 routes were exercised against the real production NextRouter (`sip5.gsvoip.com.br`) with
real client data (e.g. client id 256 = Setra Soluções em Atendimento, id 254 = Sendwork) during
this session, not just unit-tested.
