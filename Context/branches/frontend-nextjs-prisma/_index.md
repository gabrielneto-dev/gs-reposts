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
- No integration code calling `backend/` exists yet — that's the next real piece of work here

## Current state

Next.js 16 scaffold only (App Router, TypeScript, Tailwind v4) — no database, no Prisma, no real
pages/components beyond the default starter page. `npm run build` verified clean after the Prisma
removal on 2026-09-04 (had to also delete a leftover `prisma.config.ts` that `npm run build`'s
typecheck caught referencing removed packages).

## Core concepts

None currently — the Prisma-specific concepts that used to live here (Prisma Next vs. Composer,
the "data contract" file, the `db.orm.<namespace>.<Model>` query API) are historical only, see the
superseded records below.

## Key records

- `facts/FCT-20260904-scaffold.md` (still mostly accurate — Prisma-specific parts flagged inline)
- `facts/FCT-20260904-prisma8-cli-behavior.md` — **superseded**
- `facts/FCT-20260904-local-postgres.md` — **superseded** (the Postgres-17-as-a-service part is
  still true and reused by `metrics-pipeline`; the role/database part is not)
- `decisions/DEC-20260904-orm-not-composer.md` — **superseded**
- `decisions/DEC-20260904-dedicated-db-role.md` — **superseded** (principle reapplied in
  `metrics-pipeline`)

## Active decisions

None active in this branch as of 2026-09-04 — see
`Context/global/decisions/DEC-20260904-backend-owns-storage-and-scheduler.md` instead.

## Open questions

- No real data model defined yet for whatever UI/pages the frontend will eventually need.
- Auth strategy for the frontend not yet decided.
- How the frontend will fetch/display `backend/`'s reporting data (`metrics-pipeline`) — not yet
  designed; no fetch layer exists.

## Risks

None specific to this branch right now (the Prisma-RC risk is moot since Prisma was removed).

## Relations to other branches

- `nextrouter-api` — `frontend/` will eventually consume `backend/`'s HTTP endpoints for
  softswitch data; no actual integration code exists yet.
- `metrics-pipeline` — the reason this branch lost its database; the reporting data `frontend/`
  will eventually display lives there.
