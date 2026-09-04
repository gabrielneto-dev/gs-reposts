---
id: CTX-CP-20260904-1700-monorepo-and-frontend-scaffold
type: checkpoint
title: Pushed to GitHub, restructured as a monorepo, scaffolded the Next.js + Prisma 8 + Postgres frontend
status: active
created_at: 2026-09-04
updated_at: 2026-09-04
tags: [monorepo, nextjs, prisma, postgres, git]
---

# Session Checkpoint

## Objective

Get the existing FastAPI backend onto GitHub, restructure the repo as a monorepo now that a
frontend is starting, and scaffold that frontend (Next.js + Prisma 8 + PostgreSQL) with a real,
verified database connection.

## What changed

- Initialized git, created 4 commits (scaffold, FastAPI app, docs, `Context/`), pushed to a new
  GitHub repo the user created: `https://github.com/gabrielneto-dev/gs-reposts.git` (branch
  `main`). See `Context/core/constraints.md` for a note on the harness's classifier occasionally
  blocking `git add`/`git push` (resolved by retrying).
- Restructured the repo root into a monorepo: `backend/` (the FastAPI service, `git mv`'d in,
  history preserved) + `frontend/` (new) + `Context/`/`AGENTS.md`/`CLAUDE.md`/root `README.md`
  staying at the repo root. See `CTX-DEC-20260904-monorepo-restructure`.
  - Moving `.venv` broke it (Windows-absolute-path issue) — recreated fresh inside `backend/`.
- Scaffolded `frontend/`: Next.js 16 (App Router, TS, Tailwind, Turbopack) via `create-next-app`,
  then Prisma 8 for Postgres. See `Context/branches/frontend-nextjs-prisma/_index.md`.
- Connected the frontend to a **real local PostgreSQL 17** (found already running as a Windows
  service — didn't need Docker, which failed to finish starting). Created a dedicated
  `gs_reposts_app` role/`gs_reposts` database (not the `postgres` superuser), ran `prisma db init`,
  and verified an actual create/read/delete round trip through the generated client.

## Decisions

- `CTX-DEC-20260904-monorepo-restructure` — backend/frontend split, rationale, what's stale to
  watch for (paths in older Context records now need a `backend/` prefix — already fixed in
  `CTX-FCT-20260904-route-inventory`).
- `CTX-DEC-20260904-orm-not-composer` — Prisma 8's default `prisma init` pushes "Prisma Composer"
  (a heavy RPC/cloud-deploy framework), which is not what "Next.js app with its own Postgres"
  needs; used `prisma orm init --target postgres --authoring psl` instead.
- `CTX-DEC-20260904-dedicated-db-role` — app uses a scoped Postgres role, not the superuser.

## Discoveries

- `CTX-FCT-20260904-prisma8-cli-behavior` — Prisma 8 (still an RC, `8.0.0-rc.x`) restructured the
  CLI substantially: two different products behind one `prisma` command (Composer vs. classic
  ORM), no generic `@prisma/client` for Postgres anymore (it's `@prisma/orm-postgres`), JSON-
  enveloped CLI output, a "data contract" (`contract.prisma`) instead of `schema.prisma`, and a
  new query API (`db.orm.<namespace>.<Model>` with `.where(...).first()/.all()`) that isn't
  Prisma Client's classic shape. The flat `db.orm.User` form did **not** work here — had to use
  `db.orm.public.User`.
- `CTX-FCT-20260904-local-postgres` — a native Postgres 17 Windows-service install existed on the
  dev machine, unrelated to the Docker Desktop install that never finished starting.

## Problems solved

- Fixed a stale path reference: `CTX-FCT-20260904-route-inventory` still said `app/routers/...`
  after the backend moved to `backend/app/routers/...` — updated in this session, but a reminder
  that a monorepo restructure invalidates path references scattered across older Context records;
  grep for the old prefix when doing a big move like this in the future.
- `frontend/.gitignore`'s blanket `.env*` rule accidentally also ignored `.env.example` (meant to
  be committed as a template) — fixed with an explicit `!.env.example` negation.

## Failed approaches worth remembering

- Don't run bare `prisma init` in this project expecting classic ORM scaffolding — it defaults
  toward Prisma Composer. Use `prisma orm init --target postgres --authoring psl`.
- Don't try to move a Python `.venv` directory to a new location and expect it to keep working on
  Windows — delete and recreate it at the new path instead of debugging the breakage.
- Didn't try to guess/brute-force the local Postgres password when connection needed one — asked
  the user directly instead. That's still the right call for any future credential gap.

## Current state

Monorepo live on GitHub. `backend/` unchanged in behavior (just moved + venv recreated), still 8
verified GET routes. `frontend/` is a freshly scaffolded Next.js + Prisma 8 app with a real,
tested local Postgres connection, but **no real data model yet** — only the Next.js/Prisma starter
`User`/`Post` example schema and the default starter page exist. No integration between
`frontend/` and `backend/` has been built.

## Open questions

- What the frontend's actual data model/entities should be (not yet discussed).
- Auth strategy for the frontend (not yet discussed).

## Next steps

Natural candidates when the user returns to `frontend/`: design the real Prisma schema (replacing
the `User`/`Post` starter), decide auth, and wire a first call from a Next.js route to `backend/`'s
API.

## Files or artifacts affected

Repo-root: `README.md` (new), `.git/` (new), `AGENTS.md` (updated with monorepo explanation).
`backend/`: entire FastAPI app moved here (see prior checkpoint for its own history), `.venv`
recreated. `frontend/`: entire new Next.js + Prisma scaffold, `.env`/`.env.example`,
`src/prisma/contract.prisma`, `migrations/`.

## Context records created or updated

Created: `CTX-DEC-20260904-monorepo-restructure` (global), and under the new
`frontend-nextjs-prisma` branch — `_index.md`,
`facts/{FCT-20260904-scaffold, FCT-20260904-prisma8-cli-behavior, FCT-20260904-local-postgres}`,
`decisions/{DEC-20260904-orm-not-composer, DEC-20260904-dedicated-db-role}`.

Updated: `CTX-FCT-20260904-route-inventory` (path prefix fix), `branches/nextrouter-api/_index.md`
(paths + cross-branch relation), `Context/core/overview.md`, `Context/core/constraints.md`,
`Context/STATE.md`, `Context/MAP.md`, `Context/_meta/taxonomy.yaml`, `Context/_meta/catalog.jsonl`,
`Context/_meta/changelog.md`.
