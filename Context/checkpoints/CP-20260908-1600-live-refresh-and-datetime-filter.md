---
id: CTX-CP-20260908-1600-live-refresh-and-datetime-filter
type: checkpoint
title: Added scheduler-to-frontend live refresh and a full datetime range filter with an Airbnb-style calendar
branch: global
tags: [nextjs, scheduler, api-design, realtime, ui]
status: active
confidence: verified
created_at: 2026-09-08
updated_at: 2026-09-08
source_ids: []
related: [CTX-FCT-20260908-clientes-overview-page, CTX-DEC-20260908-frontend-webhook-notification, CTX-DEC-20260908-sse-same-origin-live-refresh, CTX-DEC-20260908-clientes-resumo-period-filter]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-08
valid_until: null
revisit_at: null
---

## Objective

Two user-driven requests in the same session, both building on the clients-overview page shipped
earlier the same day (`CP-20260908-1000`):

1. Make the automated collection flow "push" the frontend instead of it only ever fetching on
   manual reload.
2. Let the user filter the clients table by date/time period instead of always seeing "whatever
   each client's last known window was" — which turned out to be actively misleading (see
   Discoveries).

## What changed

**Backend (`backend/`)**:
- `scheduler/jobs.py`: `_notificar_frontend()` — best-effort webhook POST after every collection
  window's terminal state (`falhou`/vazia/`concluida`/`parcial`), gated by optional
  `FRONTEND_WEBHOOK_URL`.
- `routers/metricas.py` + `schemas/metricas.py`: `GET /api/metricas/clientes` now takes
  `inicio`/`fim` (`datetime`, both optional, default = today in full) instead of showing each
  client's all-time-latest window. `volume_dia` renamed `volume_periodo`. `400` if `inicio >= fim`.

**Frontend (`frontend/`)**:
- First-ever API routes: `POST /api/webhook/metricas-atualizadas` (receives the backend's webhook)
  and `GET /api/eventos` (SSE relay), glued by `lib/metricas-event-bus.ts` (in-memory
  `EventEmitter`).
- `components/live-refresher.tsx` (mounted in `app/layout.tsx`) — `EventSource` → `router.refresh()`.
- `components/date-range-filter.tsx` — full rewrite, ended as an Airbnb-style two-month range
  calendar with per-side `type="time"` inputs, one-click presets, and duration-preserving
  Anterior/Próximo buttons. `app/page.tsx` now reads `inicio`/`fim` from `searchParams`.

Two commits: `8ad89ec` (webhook + SSE live-refresh) and `e128e72` (datetime range filter + calendar
UI), both on `main`, not yet pushed to `origin` as of this checkpoint.

## Decisions

- `CTX-DEC-20260908-frontend-webhook-notification` — best-effort, optional, non-blocking webhook
  from scheduler to frontend.
- `CTX-DEC-20260908-sse-same-origin-live-refresh` — SSE through the frontend's own routes, not a
  direct browser→backend connection, to preserve the existing no-CORS architecture.
- `CTX-DEC-20260908-clientes-resumo-period-filter` — explicit `inicio`/`fim` datetime filter,
  default today; a client with no activity in the period doesn't appear at all.

## Discoveries

- **Real bug found via a user screenshot**: `/api/metricas/clientes` was showing clients whose
  *last-ever* collected window was from 2026-09-04, indistinguishable from genuinely-active-today
  clients, because there was no period filter at all — "latest row per client" doesn't mean
  "active in any particular period" when clients have irregular activity. This is what motivated
  the period-filter decision above; not something anyone asked for directly, it surfaced from the
  user asking "why are there collections here from day 4?".
- The date filter's final shape (`inicio`/`fim` datetime, hour granularity) only emerged after two
  earlier iterations in the same session (single `data`, then `data_inicio`/`data_fim` day range) —
  each one shipped, tested live, and then superseded within the conversation as the user's actual
  need became clearer (first wanting a date filter, then a range, then hour-level control with
  próxima/anterior paging). The final API/UI shape is what's documented; the intermediate shapes
  are not separately recorded, only mentioned inline in
  `branches/metrics-pipeline/decisions/DEC-20260908-clientes-resumo-period-filter.md`'s Context
  section for history.
- Turbopack dev-mode Fast Refresh produces transient, non-representative console errors in an
  already-open tab while files are being edited (stale module state mid-HMR) — confirmed harmless
  by re-navigating fresh each time before trusting a console error as real. Worth remembering so a
  future session doesn't chase a phantom bug during active iteration.
- `.click()` in a `javascript_tool` browser script does **not** dispatch `mousedown` — only a real
  `MouseEvent('mousedown')` (or an actual pointer interaction) triggers a click-outside-to-close
  handler. Relevant if a future session needs to script-test other click-outside UI.

## Problems solved

- Naive timezone bug avoided (not hit, but deliberately designed around): all datetime arithmetic
  in `date-range-filter.tsx` uses matched manual parse/format helpers instead of `Intl` with an
  explicit `timeZone` or `new Date(naiveIsoString)` — see the "Gotcha worth remembering" paragraph
  in `branches/frontend-nextjs-prisma/facts/FCT-20260908-clientes-overview-page.md`.
- Two separate dev-server instances (backend on `:8000`, frontend on `:3001`, both `--reload`)
  were already running from the user's own `start-dev.ps1` before this session touched anything —
  reused them for live verification instead of spinning up redundant ones; briefly almost started
  a second backend process before catching it (the `uvicorn` invocation failed harmlessly, command
  not on PATH in the sandboxed shell — no duplicate scheduler ended up running against production).

## Current state

Both features verified live via the Browser tool against the user's real dev servers and real
collected data (85-90 clients depending on the period picked). Working tree clean, 2 commits ahead
of `origin/main` (not pushed — not requested).

## Open questions

- Same as before, still open: frontend auth strategy, and what "gatilhos" (business-rule triggers)
  the user wants on top of the clients table — this was the original next-topic before the
  webhook/date-filter side-quests took over the session; still not started.
- New from this session: if the frontend is ever scaled beyond one process, the in-memory event
  bus needs a real pub/sub backend (Redis or similar) — flagged as a risk, not yet a problem.

## Next steps

1. The user's original follow-up intent (from the very first message this session) was still
   "depois vamos discutir os gatilhos e como isso vai se comportar em tela" — pick that up next
   unless redirected.
2. Consider pushing the two local commits to `origin/main` if/when the user asks.

## Affected files/artifacts

`backend/app/scheduler/jobs.py`, `backend/app/config.py`, `backend/.env(.example)`,
`backend/app/routers/metricas.py`, `backend/app/schemas/metricas.py`,
`frontend/src/app/api/webhook/metricas-atualizadas/route.ts` (new),
`frontend/src/app/api/eventos/route.ts` (new), `frontend/src/lib/metricas-event-bus.ts` (new),
`frontend/src/components/live-refresher.tsx` (new), `frontend/src/app/layout.tsx`,
`frontend/src/components/date-range-filter.tsx` (rewritten), `frontend/src/app/page.tsx`,
`frontend/src/components/clientes-table.tsx`, `frontend/src/lib/backend.ts`.

## Records created/updated

Created: `CTX-DEC-20260908-frontend-webhook-notification`,
`CTX-DEC-20260908-sse-same-origin-live-refresh`, `CTX-DEC-20260908-clientes-resumo-period-filter`,
this checkpoint. Updated: `CTX-FCT-20260904-schema-and-reused-functions`,
`CTX-FCT-20260908-clientes-overview-page`, both branch `_index.md` files (`metrics-pipeline`,
`frontend-nextjs-prisma`).
