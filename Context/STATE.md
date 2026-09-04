# Project State

Last updated: 2026-09-04
Latest checkpoint: `Context/checkpoints/CP-20260904-1700-monorepo-and-frontend-scaffold.md`

## Current objective

Build out `frontend/` (Next.js + Prisma 8 + Postgres) — the system of record — on top of the
existing `backend/` (FastAPI adapter for the NextRouter softswitch). No specific new task queued
as of this checkpoint.

## Working

- `backend/`: 8 GET routes, all verified against production. See
  `Context/branches/nextrouter-api/facts/FCT-20260904-route-inventory.md` and `backend/docs/API.md`.
- `frontend/`: Next.js 16 + Prisma 8 scaffold, connected to a real local Postgres, verified with an
  actual create/read/delete round trip. No real data model or pages beyond the starter yet. See
  `Context/branches/frontend-nextjs-prisma/_index.md`.
- Repo is on GitHub: `https://github.com/gabrielneto-dev/gs-reposts.git` (branch `main`).

## In progress

Nothing in progress.

## Blockers

None currently.

## Active decisions

- `CTX-DEC-20260904-monorepo-restructure` (global)
- `CTX-DEC-20260904-sampling-with-exact-mode`, `CTX-DEC-20260904-route-simplification`,
  `CTX-DEC-20260904-activity-detection-day-by-day` (nextrouter-api)
- `CTX-DEC-20260904-orm-not-composer`, `CTX-DEC-20260904-dedicated-db-role` (frontend-nextjs-prisma)

## Open critical questions

- Frontend data model — not yet defined (only the Next.js/Prisma starter `User`/`Post` example
  exists).
- Frontend auth strategy — not yet decided.

## Next likely steps

1. If the user asks for anything in `backend/`, check `Context/branches/nextrouter-api/_index.md`
   first — several routes were already built once and deliberately removed; don't rebuild without
   confirming.
2. If the user asks for anything in `frontend/`, check
   `Context/branches/frontend-nextjs-prisma/_index.md` first — especially the Composer-vs-ORM
   trap and the real query API shape before writing Prisma code.
3. Design the real Prisma schema when the user is ready to move past the `User`/`Post` starter.
