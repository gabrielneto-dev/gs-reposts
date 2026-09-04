---
id: CTX-FCT-20260904-scaffold
type: fact
title: frontend/ stack and initial structure
branch: frontend-nextjs-prisma
tags: [nextjs, monorepo, api-design]
status: active
confidence: verified
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-DEC-20260904-orm-not-composer, CTX-DEC-20260904-monorepo-restructure]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-04
valid_until: null
revisit_at: null
---

## Fact

> **Update 2026-09-04**: Prisma was removed entirely (see
> `CTX-DEC-20260904-backend-owns-storage-and-scheduler`) — `src/prisma/`, `prisma.config.ts`,
> `migrations/`, and `DATABASE_URL` no longer exist. Everything below about the Next.js
> App Router/Tailwind/TypeScript scaffold itself is still accurate; only the Prisma-related
> paths are gone.

`frontend/` is a Next.js 16 app (App Router, TypeScript, Tailwind CSS v4, Turbopack, npm, `src/`
directory, `@/*` import alias) scaffolded with `create-next-app@latest`, plus Prisma 8
("Prisma Next", see `FCT-20260904-prisma8-cli-behavior`) as the ORM.

Key paths:

- `frontend/src/app/` — Next.js App Router pages (only the default starter page exists so far)
- `frontend/src/prisma/contract.prisma` — the Prisma data contract (schema); starter `User`/`Post`
  models only, not yet the project's real data model
- `frontend/src/prisma/db.ts` — the typed database client (`import { db } from '.../prisma/db'`)
- `frontend/prisma.config.ts` — CLI config (contract path + `DATABASE_URL` wiring)
- `frontend/.env` (git-ignored, real local `DATABASE_URL`) / `frontend/.env.example` (committed
  template — note: the project's `.gitignore` had a blanket `.env*` rule that accidentally also
  ignored `.env.example`; fixed with an explicit `!.env.example` negation, needed again if similar
  blanket env-ignore rules are added elsewhere)
- `frontend/migrations/` — Prisma Next's migration-state tracking (snapshots + applied-hash refs),
  committed like a classic `migrations/` folder would be

Next.js auto-generates `frontend/AGENTS.md` (rewritten by `next dev`/build tooling itself — commit
it as-is, don't hand-edit; it explains itself) and `frontend/CLAUDE.md` (`@AGENTS.md` import) —
these are distinct from and layered under the repo-root `AGENTS.md`/`CLAUDE.md`.

## Verification

`npx tsc --noEmit` clean; `npm run dev` boots and serves 200 on `/`; a real create/read/delete
round trip through the Prisma client against a local Postgres succeeded (see
`FCT-20260904-local-postgres`).
