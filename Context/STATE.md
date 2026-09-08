# Project State

Last updated: 2026-09-08
Latest checkpoint: `Context/checkpoints/CP-20260908-1600-live-refresh-and-datetime-filter.md`

## Current objective

No specific new task queued as of this checkpoint. The user's own stated next topic (from before
the webhook/date-filter work started) is "gatilhos" (business-rule triggers) on top of the clients
table — mentioned twice, not yet specified.

## Working

- `backend/`: `GET /api/metricas/clientes` filters by an explicit `inicio`/`fim` datetime period
  (default: today in full) instead of always showing each client's all-time-latest window — see
  `Context/branches/metrics-pipeline/decisions/DEC-20260908-clientes-resumo-period-filter.md`.
  `volume_dia` renamed `volume_periodo`.
- `backend/`: scheduler POSTs a best-effort webhook (`FRONTEND_WEBHOOK_URL`, optional) after every
  collection window — see
  `Context/branches/metrics-pipeline/decisions/DEC-20260908-frontend-webhook-notification.md`.
- `backend/`: scheduler still fires 15x/day — `[00:00,07:00)`, hourly 07:00-20:00, `[20:00,00:00)`
  — unchanged since the last checkpoint. Verified running unattended (90+ distinct clients
  accumulated by 2026-09-08).
- `frontend/`: clients-overview table at `/` now live-refreshes (SSE via this app's own
  `/api/eventos` + `/api/webhook/metricas-atualizadas` — its first API routes) and has an
  Airbnb-style datetime range filter (two-month calendar, per-side time input, presets,
  Anterior/Próximo). See
  `Context/branches/frontend-nextjs-prisma/facts/FCT-20260908-clientes-overview-page.md` and
  `Context/branches/frontend-nextjs-prisma/decisions/DEC-20260908-sse-same-origin-live-refresh.md`.
  Still no database, no auth, no other pages.
- Repo on GitHub: `https://github.com/gabrielneto-dev/gs-reposts.git` (branch `main`). Two commits
  made this session (`8ad89ec`, `e128e72`) — **not yet pushed** to `origin` as of this checkpoint.

## In progress

Nothing in progress.

## Blockers

None currently. See `Context/core/constraints.md` for two recurring environment quirks worth
knowing about before assuming something is broken: the harness's classifier occasionally blocking
ordinary commands (retry once), and connection-reset-shaped errors on this Windows machine during
concurrent async I/O that can be transient rather than a real config/credentials problem. New this
session: Turbopack dev-mode Fast Refresh can produce transient, non-representative console errors
in an already-open browser tab while files are actively being edited — always re-verify with a
fresh navigation before treating one as a real bug.

## Active decisions

- `CTX-DEC-20260904-monorepo-restructure`, `CTX-DEC-20260904-backend-owns-storage-and-scheduler`,
  `CTX-DEC-20260908-portuguese-schema-naming` (global)
- `CTX-DEC-20260904-sampling-with-exact-mode`, `CTX-DEC-20260904-route-simplification`,
  `CTX-DEC-20260904-activity-detection-day-by-day` (nextrouter-api)
- `CTX-DEC-20260908-collection-window-00h-split` (supersedes `DEC-20260904-collection-window-schedule`),
  `CTX-DEC-20260904-sampled-discovery-exact-client-metrics`,
  `CTX-DEC-20260908-clientes-resumo-period-filter`,
  `CTX-DEC-20260908-frontend-webhook-notification` (metrics-pipeline)
- `CTX-DEC-20260908-sse-same-origin-live-refresh`, plus the fetch-strategy choice in
  `FCT-20260908-clientes-overview-page` (frontend-nextjs-prisma)

## Open critical questions

- Frontend data model (beyond consuming `backend/`) and auth strategy — not yet decided.
- What "gatilhos"/business-rule triggers the user wants on top of the clients table — mentioned
  twice, not yet specified. Likely the next real topic.
- Whether the transient-network-failure risk in `metrics-pipeline` needs a retry — needs more
  unattended run time before deciding.
- If the frontend is ever scaled to multiple processes, the live-refresh event bus (in-memory,
  single-process) needs a real pub/sub backend — not urgent today.

## Next likely steps

1. If the user asks for anything in `backend/`'s live routes, check
   `Context/branches/nextrouter-api/_index.md` first — several routes were already built once and
   deliberately removed; don't rebuild without confirming.
2. If the user asks for anything about stored metrics/scheduling/schema/the webhook, check
   `Context/branches/metrics-pipeline/_index.md` first — and remember all naming there is
   Portuguese now (`Context/global/decisions/DEC-20260908-portuguese-schema-naming.md`).
3. If the user asks for new frontend pages/business rules/UI, check
   `Context/branches/frontend-nextjs-prisma/facts/FCT-20260908-clientes-overview-page.md` first —
   it explains the existing page's architecture (Server Component, no CORS, SSE live-refresh,
   the datetime range filter) so new work stays consistent with it.
4. Any new DB table/column or API field must be named in Portuguese — see the `AGENTS.md`
   Conventions section.
5. The "gatilhos" conversation was explicitly deferred twice by the user in favor of other work —
   good candidate to raise proactively if no other task is given.
