# Project State

Last updated: 2026-09-08
Latest checkpoint: `Context/checkpoints/CP-20260908-1000-clientes-page-and-pt-br-rename.md`

## Current objective

No specific new task queued as of this checkpoint. The user mentioned wanting to add business-rule
"gatilhos" (triggers) on top of the clients-overview table next, but nothing concrete requested yet.

## Working

- `backend/`: 8 live GET routes (`nextrouter-api`, unchanged) + 3 DB-only routes under
  `/api/metricas/` (`nextrouter-api`'s routes call the softswitch every request; `metricas`'s
  routes only read `metrics-pipeline`'s Postgres data). All Portuguese-named end to end since
  2026-09-08 — see `Context/global/decisions/DEC-20260908-portuguese-schema-naming.md`.
- `backend/`: scheduler now fires 15x/day — `[00:00,07:00)`, hourly 07:00-20:00, `[20:00,00:00)`.
  See `Context/branches/metrics-pipeline/decisions/DEC-20260908-collection-window-00h-split.md`.
  Verified running unattended across multiple days (77 distinct clients accumulated by 2026-09-08).
- `frontend/`: first real page shipped — a clients-overview table at `/`, Server Component fetch
  against `backend/`'s `/api/metricas/clientes`. See
  `Context/branches/frontend-nextjs-prisma/facts/FCT-20260908-clientes-overview-page.md`. Still no
  database, no auth, no other pages.
- Repo on GitHub: `https://github.com/gabrielneto-dev/gs-reposts.git` (branch `main`), all work
  through this checkpoint committed and pushed (`main` at `549d892` as of this checkpoint).

## In progress

Nothing in progress.

## Blockers

None currently. See `Context/core/constraints.md` for two recurring environment quirks worth
knowing about before assuming something is broken: the harness's classifier occasionally blocking
ordinary commands (retry once), and connection-reset-shaped errors on this Windows machine during
concurrent async I/O that can be transient rather than a real config/credentials problem.

## Active decisions

- `CTX-DEC-20260904-monorepo-restructure`, `CTX-DEC-20260904-backend-owns-storage-and-scheduler`,
  `CTX-DEC-20260908-portuguese-schema-naming` (global)
- `CTX-DEC-20260904-sampling-with-exact-mode`, `CTX-DEC-20260904-route-simplification`,
  `CTX-DEC-20260904-activity-detection-day-by-day` (nextrouter-api)
- `CTX-DEC-20260908-collection-window-00h-split` (supersedes `DEC-20260904-collection-window-schedule`),
  `CTX-DEC-20260904-sampled-discovery-exact-client-metrics` (metrics-pipeline)
- `frontend-nextjs-prisma` has no ORM/DB decisions active (Prisma-era ones superseded); its one
  active choice is the Server Component fetch strategy in `FCT-20260908-clientes-overview-page`.

## Open critical questions

- Frontend data model (beyond consuming `backend/`) and auth strategy — not yet decided.
- What "gatilhos"/business-rule triggers the user wants on top of the clients table — mentioned,
  not yet specified.
- Whether the transient-network-failure risk in `metrics-pipeline` needs a retry — needs more
  unattended run time before deciding.

## Next likely steps

1. If the user asks for anything in `backend/`'s live routes, check
   `Context/branches/nextrouter-api/_index.md` first — several routes were already built once and
   deliberately removed; don't rebuild without confirming.
2. If the user asks for anything about stored metrics/scheduling/schema, check
   `Context/branches/metrics-pipeline/_index.md` first — and remember all naming there is
   Portuguese now (`Context/global/decisions/DEC-20260908-portuguese-schema-naming.md`).
3. If the user asks for new frontend pages/business rules, check
   `Context/branches/frontend-nextjs-prisma/facts/FCT-20260908-clientes-overview-page.md` first —
   it explains the existing page's architecture (Server Component, no CORS) so new work stays
   consistent with it.
4. Any new DB table/column or API field must be named in Portuguese — see the `AGENTS.md`
   Conventions section.
