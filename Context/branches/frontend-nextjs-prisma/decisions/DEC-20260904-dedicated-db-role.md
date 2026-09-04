---
id: CTX-DEC-20260904-dedicated-db-role
type: decision
title: Use a dedicated Postgres role/database for the app, not the postgres superuser
branch: frontend-nextjs-prisma
tags: [postgres, production-safety]
status: superseded
confidence: high
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-FCT-20260904-local-postgres]
depends_on: []
supersedes: null
superseded_by: CTX-DEC-20260904-backend-owns-storage-and-scheduler
---

> **Superseded 2026-09-04**: `frontend/` no longer owns a database at all (see
> `CTX-DEC-20260904-backend-owns-storage-and-scheduler`), so this specific role/database is moot.
> The underlying principle (dedicated least-privilege role, not the superuser) was reapplied for
> the backend's new `gs_reposts_backend` role — see
> `branches/metrics-pipeline/facts/FCT-20260904-schema-and-reused-functions.md`.

# Decision

## Context

The only credential available for the local Postgres 17 instance was the `postgres` superuser's
password (provided directly by the user in chat to unblock setup — not recorded in `Context/`).

## Decision

Connected once as `postgres` to create a dedicated, least-privilege role and database for the app
(`gs_reposts_app` owning `gs_reposts`), generated a fresh random password for that role (not the
superuser's password), and pointed `frontend/.env`'s `DATABASE_URL` at the dedicated role — never
at `postgres` directly.

## Rationale

Standard practice: an application should hold credentials scoped to only what it needs, not
platform-superuser access. Costs nothing extra to do up front, and avoids the app's `.env` ever
containing the one password that can also administer the whole Postgres instance.

## Consequences

- Future schema changes (`prisma db init` / `prisma migration plan`, etc.) run fine as
  `gs_reposts_app` since it owns the `gs_reposts` database — no need to reach for the superuser
  again for normal day-to-day work.
- If the app ever needs a privilege the owner role doesn't have (e.g. creating extensions), that's
  a deliberate, visible step (connect as `postgres`, grant it) rather than something that happens
  silently because the app already had superuser access.

## Related records

`CTX-FCT-20260904-local-postgres`.
