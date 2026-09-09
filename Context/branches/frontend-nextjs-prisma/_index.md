# Branch: frontend-nextjs-prisma

## Purpose

The user-facing application — `frontend/` in the monorepo (see
`Context/global/decisions/DEC-20260904-monorepo-restructure.md`). Despite the branch name (kept
for stable IDs/history), **it no longer owns a database or uses Prisma** — see
`Context/global/decisions/DEC-20260904-backend-owns-storage-and-scheduler.md` (2026-09-04): the
`backend/` now owns all storage (`Context/branches/metrics-pipeline/`), and `frontend/` is a pure
HTTP consumer of `backend/`'s API.

## Scope

- The Next.js app under `frontend/`
- (Historical, superseded) Prisma 8 as the ORM — see the superseded records below, kept for
  history in case an ORM is reconsidered later
- `frontend/src/lib/backend.ts` — the one place that calls `backend/`'s API (server-side only)

## Current state

Real first feature shipped 2026-09-08: a clients-overview table (originally at `/`, moved to
`/relatorios` on 2026-09-09 — see `facts/FCT-20260909-relatorios-route-move.md`) fed by `backend/`'s
`/api/metricas/clientes` — see `facts/FCT-20260908-clientes-overview-page.md`. Same day, two more
pieces landed on top: live-refresh via SSE (this app's first API routes —
`decisions/DEC-20260908-sse-same-origin-live-refresh.md`) and an Airbnb-style datetime range
filter (calendar picker, presets, Anterior/Próximo — same fact file, "Added later the same day"
section).

As of 2026-09-09 the app is now multi-page and multi-tool: `/gatilhos` + `/alertas`
(`Context/branches/gatilhos-alertas/`) and `/janelas`
(`facts/FCT-20260909-janelas-page.md`) exist alongside `/relatorios`, all reachable through a new
double-sidebar nav (`decisions/DEC-20260909-multi-tool-navigation-architecture.md`) built around a
data-driven `FERRAMENTAS` array so future tools are just new array entries. The app's light
amber/zinc design system is now written down explicitly — see
`Context/global/decisions/DEC-20260909-frontend-design-system-tokens.md` — new pages/tools should
follow it from the start.

Still no database (by design, see `DEC-20260904-backend-owns-storage-and-scheduler`), no auth.
`npm run build`/`npm run lint` verified clean after every change so far.

## Core concepts

None currently — the Prisma-specific concepts that used to live here (Prisma Next vs. Composer,
the "data contract" file, the `db.orm.<namespace>.<Model>` query API) are historical only, see the
superseded records below.

## Key records

- `facts/FCT-20260908-clientes-overview-page.md` — the first real page, architecture, decisions
  (now also covers live-refresh and the datetime range filter, added later the same day)
- `decisions/DEC-20260908-sse-same-origin-live-refresh.md` — why live-refresh goes through this
  app's own `/api/eventos` + `/api/webhook/metricas-atualizadas` instead of the browser talking to
  `backend/` directly
- `decisions/DEC-20260909-multi-tool-navigation-architecture.md` — the double sidebar and its
  data-driven `FERRAMENTAS` array
- `facts/FCT-20260909-janelas-page.md` — the `/janelas` status/manual-trigger page,
  `calendario.ts` extraction
- `facts/FCT-20260909-relatorios-route-move.md` — `/` → `/relatorios`
- `Context/global/decisions/DEC-20260909-frontend-design-system-tokens.md` — the design tokens
  every page/component here should use
- `facts/FCT-20260904-scaffold.md` (still mostly accurate — Prisma-specific parts flagged inline)
- `facts/FCT-20260904-prisma8-cli-behavior.md` — **superseded**
- `facts/FCT-20260904-local-postgres.md` — **superseded** (the Postgres-17-as-a-service part is
  still true and reused by `metrics-pipeline`; the role/database part is not)
- `decisions/DEC-20260904-orm-not-composer.md` — **superseded**
- `decisions/DEC-20260904-dedicated-db-role.md` — **superseded** (principle reapplied in
  `metrics-pipeline`)

## Active decisions

`Context/global/decisions/DEC-20260904-backend-owns-storage-and-scheduler.md` (no DB here) — plus
the fetch-strategy choice in `facts/FCT-20260908-clientes-overview-page.md` (Server Component
fetch, not client-side — chosen specifically to avoid needing CORS on the backend), and
`decisions/DEC-20260908-sse-same-origin-live-refresh.md` (live-refresh stays same-origin for the
same CORS-avoidance reason).

## Open questions

- No real data model defined yet for whatever UI/pages the frontend will eventually need.
- Auth strategy for the frontend not yet decided.
- Whether/when client-side fetching (and therefore backend CORS) will be needed — not yet, only
  Server Components fetch `backend/` so far.

## Risks

- Live-refresh's event bus (`lib/metricas-event-bus.ts`) is in-memory and single-process — see
  `decisions/DEC-20260908-sse-same-origin-live-refresh.md`'s Consequences. Not a problem today
  (one Next.js instance), but would silently under-deliver if the frontend is ever scaled to
  multiple replicas. Low urgency, just don't forget it when that day comes.
- (The Prisma-RC risk is moot since Prisma was removed.)

## Relations to other branches

- `nextrouter-api` — `frontend/` could consume `backend/`'s live NextRouter-adapter routes too;
  no integration code for those exists yet (only `metrics-pipeline`'s stored-data routes are used).
- `metrics-pipeline` — the reason this branch lost its database, and the data source for the
  clients-overview page (`/api/metricas/clientes`). Also now the source of the webhook that drives
  this branch's live-refresh — see `decisions/DEC-20260908-sse-same-origin-live-refresh.md` and
  `branches/metrics-pipeline/decisions/DEC-20260908-frontend-webhook-notification.md`.
- `gatilhos-alertas` — owns the rule-evaluation backend, but its `/gatilhos` and `/alertas` pages
  and components live in this branch's scope (`frontend/`); see
  `Context/branches/gatilhos-alertas/_index.md`.
