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

Real first feature shipped 2026-09-08: a clients-overview table at `/` fed by `backend/`'s
`/api/metricas/clientes` — see `facts/FCT-20260908-clientes-overview-page.md`. Still no database
(by design, see `DEC-20260904-backend-owns-storage-and-scheduler`), no auth, no other pages.
`npm run build` verified clean after every change so far.

## Core concepts

None currently — the Prisma-specific concepts that used to live here (Prisma Next vs. Composer,
the "data contract" file, the `db.orm.<namespace>.<Model>` query API) are historical only, see the
superseded records below.

## Key records

- `facts/FCT-20260908-clientes-overview-page.md` — the first real page, architecture, decisions
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
fetch, not client-side — chosen specifically to avoid needing CORS on the backend).

## Open questions

- No real data model defined yet for whatever UI/pages the frontend will eventually need.
- Auth strategy for the frontend not yet decided.
- Whether/when client-side fetching (and therefore backend CORS) will be needed — not yet, only
  Server Components fetch `backend/` so far.

## Risks

None specific to this branch right now (the Prisma-RC risk is moot since Prisma was removed).

## Relations to other branches

- `nextrouter-api` — `frontend/` could consume `backend/`'s live NextRouter-adapter routes too;
  no integration code for those exists yet (only `metrics-pipeline`'s stored-data routes are used).
- `metrics-pipeline` — the reason this branch lost its database, and the data source for the
  clients-overview page (`/api/metricas/clientes`).
