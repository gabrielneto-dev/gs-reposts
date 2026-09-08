---
id: CTX-DEC-20260908-sse-same-origin-live-refresh
type: decision
title: Live-refresh the clients page via same-origin SSE, not a direct browser connection to backend/
branch: frontend-nextjs-prisma
tags: [nextjs, realtime, api-design]
status: active
confidence: high
created_at: 2026-09-08
updated_at: 2026-09-08
source_ids: []
related: [CTX-FCT-20260908-clientes-overview-page, CTX-DEC-20260908-frontend-webhook-notification]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-08
valid_until: null
revisit_at: null
---

# Decision

## Context

`backend/`'s scheduler now POSTs a webhook after every collection window (see
`branches/metrics-pipeline/decisions/DEC-20260908-frontend-webhook-notification.md`). The
clients-overview page needed a way to react to that and refresh itself without a manual reload —
but the existing fetch-strategy decision in `facts/FCT-20260908-clientes-overview-page.md`
deliberately avoids client-side calls to `backend/` specifically to keep `backend/` CORS-free and
its address out of the browser bundle. A naive implementation (browser opens a WebSocket/SSE
straight to `backend/`) would have undone that.

## Decision

Two new Next.js Route Handlers — the app's first API routes — keep everything same-origin:

- `POST /api/webhook/metricas-atualizadas` (`frontend/src/app/api/webhook/metricas-atualizadas/route.ts`)
  — receives `backend/`'s webhook call (server-to-server, not a browser request, so no CORS
  question even arises) and publishes onto an in-memory event bus.
- `GET /api/eventos` (`frontend/src/app/api/eventos/route.ts`) — a `ReadableStream`-based SSE
  endpoint the browser connects to (same-origin); relays whatever the webhook route publishes,
  plus a 25s heartbeat comment to keep the connection alive.
- `frontend/src/lib/metricas-event-bus.ts` — a plain Node `EventEmitter`, module-level singleton,
  the glue between the two routes.
- `frontend/src/components/live-refresher.tsx` — invisible client component, mounted once in
  `app/layout.tsx`, opens an `EventSource` to `/api/eventos` and calls `router.refresh()` on every
  event (re-runs the Server Component fetch, no full page reload).

## Rationale

Preserves the existing no-CORS, backend-address-never-in-the-browser architecture from
`facts/FCT-20260908-clientes-overview-page.md` while still getting a real push-based UI update —
the browser only ever talks to its own origin. SSE (not WebSocket) because the data flow is
one-directional (server → browser); no library needed, Web Streams API is enough.

## Consequences

- The event bus is **in-memory, single-process**. It works correctly for today's single Next.js
  server instance; if the frontend is ever run as multiple replicas, only the instance that
  received the webhook would relay the update to its own connected browsers — the others would
  need a manual reload until this is revisited (e.g. Redis pub/sub or similar).
- `router.refresh()` re-fetches with whatever `searchParams` (date/time filter) the tab currently
  has — see `facts/FCT-20260908-clientes-overview-page.md`'s date-range-filter section. Viewing a
  past period is unaffected by new windows landing; only "today" views visibly update.

## Related records

`CTX-FCT-20260908-clientes-overview-page`,
`branches/metrics-pipeline/decisions/DEC-20260908-frontend-webhook-notification.md`,
`branches/frontend-nextjs-prisma/_index.md`.
