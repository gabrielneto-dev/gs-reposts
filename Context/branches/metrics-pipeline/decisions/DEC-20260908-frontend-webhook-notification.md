---
id: CTX-DEC-20260908-frontend-webhook-notification
type: decision
title: Scheduler POSTs a best-effort webhook to the frontend after every collection window
branch: metrics-pipeline
tags: [scheduler, api-design, realtime, nextjs]
status: active
confidence: high
created_at: 2026-09-08
updated_at: 2026-09-08
source_ids: []
related: [CTX-FCT-20260904-schema-and-reused-functions, CTX-DEC-20260908-sse-same-origin-live-refresh]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-08
valid_until: null
revisit_at: null
---

# Decision

## Context

The clients-overview page (`frontend/`) only ever refetched on a manual page reload — a new
collection window landing in Postgres had no way to reach an already-open tab. The user asked for
a flow where, after each collection window, a webhook fires so the frontend can update itself
without polling.

## Decision

- New optional setting `frontend_webhook_url` (`FRONTEND_WEBHOOK_URL` env var, `backend/app/config.py`).
  Unset = feature off, collection job behaves exactly as before.
- `_notificar_frontend(janela)` in `backend/app/scheduler/jobs.py`, called at all three terminal
  points of `run_collection_window` (discovery failure, empty window, normal completion) — so
  `situacao` `falhou`/`concluida`/`parcial` all notify, not just success.
- Fire-and-forget: `httpx.AsyncClient(timeout=5.0)` POST with `{janela_id, inicio_janela,
  fim_janela, situacao, clientes_descobertos, clientes_processados}`; any `httpx.HTTPError` is
  logged as a warning and swallowed — a webhook failure (frontend down, network hiccup) must never
  fail or block the collection job itself.
- The receiving side lives entirely in `frontend/` — see
  `branches/frontend-nextjs-prisma/decisions/DEC-20260908-sse-same-origin-live-refresh.md` for how
  the webhook call turns into a browser-side refresh.

## Rationale

Simplest mechanism that satisfies "notify without polling" without adding new infrastructure
(no message queue, no websocket server) — a single POST the scheduler already has an HTTP client
(`httpx`) available for. Keeping it optional and non-blocking means it can't turn into a new
production-safety risk for the scheduler, which already has to be conservative (see
`Context/core/constraints.md` and this branch's risks).

## Consequences

- Only one webhook target is supported (no fan-out to multiple URLs) — fine for the current
  single-frontend-instance deployment; revisit if that changes.
- No retry on webhook delivery failure — a dropped notification just means that one tab doesn't
  auto-refresh; the data itself is never lost (it's already committed to Postgres before the
  webhook fires), and the next successful window's webhook (or a manual reload) catches it up.
- No authentication on the webhook call — acceptable given both sides run on the same trusted
  local/internal network today; revisit if the frontend is ever exposed publicly.

## Related records

`CTX-FCT-20260904-schema-and-reused-functions`,
`branches/frontend-nextjs-prisma/decisions/DEC-20260908-sse-same-origin-live-refresh.md`,
`branches/metrics-pipeline/_index.md`.
