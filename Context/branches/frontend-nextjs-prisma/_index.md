# Branch: frontend-nextjs-prisma

## Purpose

The user-facing application — `frontend/` in the monorepo (see
`Context/global/decisions/DEC-20260904-monorepo-restructure.md`). Owns its own database; is the
system of record for the project, unlike `backend/` (a stateless adapter — see
`Context/branches/nextrouter-api/`).

## Scope

- The Next.js app under `frontend/`
- Prisma 8 ("Prisma Next", still a release candidate) as the ORM, targeting PostgreSQL
- How Prisma 8's CLI actually behaves (it changed a lot from prior Prisma versions)
- The local PostgreSQL setup used for development

## Current state

Freshly scaffolded and verified end-to-end against a real local database (create/read/delete
round trip through `db.orm.public.User`). No real data model yet — the schema at
`frontend/src/prisma/contract.prisma` still has only the Next.js/Prisma starter's example
`User`/`Post` models. No pages/components beyond the Next.js default starter page exist yet.

## Core concepts

- **"Prisma Next"** is this project's name for classic-style Prisma ORM usage in v8 (schema file +
  typed client), reached via `prisma orm init` — see
  `decisions/DEC-20260904-orm-not-composer.md`. Don't confuse it with **Prisma Composer**
  (`@prisma/composer`), a different, much heavier product for building "Prisma Apps" (RPC
  services, Modules, deploy to Prisma Cloud) that this project does NOT use.
- The schema file is called the **data contract** (`contract.prisma`, not `schema.prisma`), and
  `prisma contract emit` regenerates its companion `contract.json`/`contract.d.ts` — all three are
  committed.
- Query API is `db.orm.<namespace>.<Model>` (e.g. `db.orm.public.User`), fluent
  `.where(...).select(...).first()/.all()`, not Prisma Client's classic `.findUnique()`-style API.
  Full reference lives in `frontend/.claude/skills/prisma-8/` (synced from the installed package —
  read it before writing non-trivial queries; the API is genuinely different from Prisma 5/6/7).

## Key records

- `facts/FCT-20260904-scaffold.md`
- `facts/FCT-20260904-prisma8-cli-behavior.md`
- `facts/FCT-20260904-local-postgres.md`
- `decisions/DEC-20260904-orm-not-composer.md`
- `decisions/DEC-20260904-dedicated-db-role.md`

## Active decisions

See `decisions/` above — both active as of 2026-09-04.

## Open questions

- No real data model defined yet — what entities/tables the frontend actually needs is still
  undecided (only the Next.js/Prisma starter `User`/`Post` example exists).
- Auth strategy for the frontend not yet decided.

## Risks

- Prisma 8 is a **release candidate** (`8.0.0-rc.x`), not a final stable release — expect breaking
  changes between RC bumps. `npm view prisma dist-tags` showed `prev: 7.10.0` (last stable) vs.
  `latest: 8.0.0-rc.12` at the time of setup. `.claude/skills/prisma-8/upgrading/` has per-RC
  upgrade instructions if `npm outdated` shows a newer RC.
- No staging database exists — same production-caution posture as `backend/`, just for a local dev
  Postgres instead of the company's real softswitch (lower stakes, but still worth remembering that
  `frontend/.env`'s `DATABASE_URL` points at a real local database, not a mock).

## Relations to other branches

- `nextrouter-api` — `frontend/` will eventually consume `backend/`'s HTTP endpoints for
  softswitch data; no actual integration code exists yet.
