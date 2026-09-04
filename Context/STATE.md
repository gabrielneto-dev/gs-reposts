# Project State

Last updated: 2026-09-04
Latest checkpoint: `Context/checkpoints/CP-20260904-1500-fastapi-nextrouter-mvp.md`

## Current objective

Maintain/extend the `relatorios` FastAPI reporting API for GS VoIP's NextRouter softswitch. No
specific new task queued as of this checkpoint — session ended with a context save after the MVP
was built and verified.

## Working

8 GET routes, all verified against production (`sip5.gsvoip.com.br`):
`/api/asr`, `/api/acd`, `/api/pdd`, `/api/clientes`, `/api/clientes/busca`,
`/api/clientes/atividade`, `/api/clientes/recorrencia`, `/health`. See
`Context/branches/nextrouter-api/facts/FCT-20260904-route-inventory.md` and `docs/API.md`.

## In progress

Nothing in progress.

## Blockers

None currently.

## Active decisions

- `CTX-DEC-20260904-sampling-with-exact-mode`
- `CTX-DEC-20260904-route-simplification`
- `CTX-DEC-20260904-activity-detection-day-by-day`

## Open critical questions

None open.

## Next likely steps

1. If the user asks for anything new, check `Context/branches/nextrouter-api/_index.md` first —
   several routes (`/api/metricas`, `/api/relatorio-horario`, `/api/serie-diaria`) were already
   built once and deliberately removed; don't rebuild them without confirming the user wants them
   back.
2. No git repository exists yet in this project — if version control comes up, that's new ground.
3. Revisit NextQualify integration only if the company acquires that product (currently: no).
