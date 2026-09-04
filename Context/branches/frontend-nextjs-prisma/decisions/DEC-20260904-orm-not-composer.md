---
id: CTX-DEC-20260904-orm-not-composer
type: decision
title: Use `prisma orm init` (classic ORM) instead of the default `prisma init` (Prisma Composer)
branch: frontend-nextjs-prisma
tags: [prisma, api-design]
status: active
confidence: high
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-FCT-20260904-prisma8-cli-behavior]
depends_on: []
supersedes: null
superseded_by: null
---

# Decision

## Context

The user asked for "Next.js com Prisma 8 com Postgres." Running the bare `prisma init` (as one
naturally would from prior Prisma versions' muscle memory) scaffolded `prisma.config.ts` with a
`skills` block and synced a **Prisma Composer** skill (`@prisma/composer`) — a framework for
building "Prisma Apps" out of RPC services and Modules, deployed to Prisma Cloud. No
`schema.prisma`, no local database wiring, nothing resembling classic Prisma ORM usage came out of
it.

## Problem

Prisma Composer is a fundamentally different, much heavier product: it wants the app's services
declared as `compute()` nodes wired through a root `module.ts`, deployed with
`prisma-composer deploy` to Prisma Cloud's managed compute + managed Postgres, authenticated via
`PRISMA_SERVICE_TOKEN`/`PRISMA_WORKSPACE_ID`. Building the frontend that way would mean adopting
Prisma's cloud platform and a services/RPC architecture the user never asked for, instead of "a
Next.js app talking to a Postgres database I control."

## Decision

Used `prisma orm init --target postgres --authoring psl --write-env` instead (had to pass
`--confirm frontend` non-interactively to consent to overwriting the Composer-flavored
`prisma.config.ts` from the earlier `prisma init` run). This is Prisma's classic-style ORM path —
internally named "Prisma Next" — schema file + typed client, no cloud platform involved. Also
manually pruned the Composer skill and the unused Cursor/opencode/Devin skill copies that
`prisma skills sync` adds by default, keeping only `.claude/skills/prisma-8/`.

## Rationale

Matches what was actually asked for. Composer is a legitimate product for a different kind of
project (a multi-service app deployed on Prisma's own cloud) — worth knowing it exists (see
`CTX-FCT-20260904-prisma8-cli-behavior`) in case a future ask genuinely wants that, but it's not
this project's shape.

## Consequences

- Don't run bare `prisma init` again in this project without the `--skills=` flag or without
  checking what it scaffolds first — it defaults toward Composer, and it prompts for consent
  before overwriting an existing `prisma.config.ts` (safe, but non-interactive runs need
  `--confirm`).
- `frontend/.claude/skills/prisma-8/` is the authoritative reference for this project's actual
  query API — read it before writing non-trivial Prisma queries rather than assuming classic
  Prisma Client method names.

## Related records

`CTX-FCT-20260904-prisma8-cli-behavior`.
