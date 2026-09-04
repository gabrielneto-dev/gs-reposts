---
id: CTX-FCT-20260904-prisma8-cli-behavior
type: fact
title: How the Prisma 8 CLI actually works (differs a lot from prior Prisma versions)
branch: frontend-nextjs-prisma
tags: [prisma, api-quirks]
status: active
confidence: verified
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-DEC-20260904-orm-not-composer]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-04
valid_until: null
revisit_at: null
---

## Fact

Prisma 8 (installed version: `8.0.0-rc.12` CLI / `@prisma/orm-postgres@8.0.0-rc.8` at setup time —
still a release candidate, `npm view prisma dist-tags` showed `prev: 7.10.0` as the last stable)
restructured the CLI and package layout significantly versus Prisma 5/6/7:

- **Two very different products share the `prisma` CLI**: **Prisma Composer** (`@prisma/composer`)
  — a framework for "Prisma Apps": `compute()` services, RPC contracts, Modules, deploy to Prisma
  Cloud (`prisma-composer deploy`, needs `PRISMA_SERVICE_TOKEN`) — and classic-style ORM usage
  (internally called **"Prisma Next"**) via the `prisma orm` subcommand. Bare `prisma init`
  defaults toward Composer (scaffolds `prisma.config.ts` with a `skills` block and syncs the
  Composer skill) — **not** what a plain "Next.js app with its own Postgres" needs. Use
  `prisma orm init` instead. See `CTX-DEC-20260904-orm-not-composer`.
- **`prisma orm init` flags**: `--target postgres|mongodb`, `--authoring psl|typescript` (PSL =
  the familiar `.prisma` schema syntax), `--write-env` (writes `.env` from `.env.example`),
  `--probe-db` (optionally verify `DATABASE_URL` connects), `--confirm <token>` (non-interactive
  consent when it would otherwise prompt, e.g. to overwrite an existing `prisma.config.ts`).
- **Package naming changed**: there is no generic `@prisma/client` for a Postgres target anymore
  (its npm `latest` tag is still `7.10.0`, and no matching `8.0.0-rc.x` was ever published for it —
  installing it manually alongside `prisma@8` is a version-mismatch trap). The v8 ORM path installs
  a target-specific package instead: **`@prisma/orm-postgres`** (dependency) +
  **`@prisma/cli-engine`** (dev dependency, used by `prisma.config.ts`).
- **CLI output is structured JSON envelopes** (`{"kind":"result","envelope":{"ok":true,...}}`), not
  plain text — useful for scripting/parsing but means grep-based habits from older Prisma versions
  don't apply.
- **`prisma skills sync`** copies agent-facing skill docs (reference material for Claude Code and
  other coding agents) from whatever Prisma packages are installed into `.claude/skills/` (and, by
  default, `.cursor/`, `.agents/`, `.devin/` too — prune the ones you don't use; this project keeps
  only `.claude/skills/prisma-8/`). It syncs based on installed packages, not just the declared
  target — running it after installing `@prisma/orm-postgres` also pulled in a stale Composer skill
  until manually removed.
- **The schema file is a "data contract"** (`contract.prisma`, in `src/prisma/` by default with
  `--authoring psl`), not `schema.prisma`. Workflow: edit `contract.prisma` → `prisma contract
  emit` (regenerates `contract.json`/`contract.d.ts`) → `prisma db init` (creates tables) /
  `prisma migration plan` for subsequent changes.
- **Query API is new**: `db.orm.<namespace>.<Model>` (e.g. `db.orm.public.User`), not Prisma
  Client's `.findUnique()`/`.create()` classic shape — see
  `frontend/.claude/skills/prisma-8/references/queries-postgres.md` for the actual method names
  (`.where(...).first()/.all()`, `.create(...)`, `.where(...).delete()`, etc.) before guessing.
  The **flat form `db.orm.User` did not work** in this project's single-namespace ("public")
  contract — had to use the namespace-qualified `db.orm.public.User` even though the docs say the
  flat form "works when bare names are unique across all namespaces." Use the qualified form by
  default; don't assume the flat shorthand works without checking `Object.keys(db.orm)` first.

## Confidence

High — all verified by running the actual commands against this project during setup, not just
read from docs (which sometimes disagreed with observed behavior, e.g. the flat-name point above).
