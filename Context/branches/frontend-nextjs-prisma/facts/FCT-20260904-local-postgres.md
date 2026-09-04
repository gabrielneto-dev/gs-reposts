---
id: CTX-FCT-20260904-local-postgres
type: fact
title: Local development database setup
branch: frontend-nextjs-prisma
tags: [postgres, production-safety]
status: superseded
confidence: verified
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-DEC-20260904-dedicated-db-role]
depends_on: []
supersedes: null
superseded_by: CTX-DEC-20260904-backend-owns-storage-and-scheduler
valid_from: 2026-09-04
valid_until: 2026-09-04
revisit_at: null
---

> **Superseded 2026-09-04**: `frontend/` no longer has a database — Prisma was removed, see
> `CTX-DEC-20260904-backend-owns-storage-and-scheduler`. The `gs_reposts_app`/`gs_reposts`
> role/database described below were NOT dropped and may still exist on the local Postgres
> instance, just unused. The Postgres-17-as-a-Windows-service fact below is still true and
> reusable — the new `gs_reposts_backend`/`gs_reposts_metrics` role/database (see
> `branches/metrics-pipeline/facts/FCT-20260904-schema-and-reused-functions.md`) lives on the same
> instance.

## Fact

The development machine has **PostgreSQL 17 installed natively and running as a Windows service**
(`postgresql-x64-17`, binaries at `C:\Program Files\PostgreSQL\17\bin`) — not inside Docker.
Docker Desktop is also installed but did not finish starting on its own (likely needs manual
interaction on first launch — accepting terms, sign-in, etc.); the native install was used instead
and needs no Docker at all for local frontend development.

`pg_hba.conf` requires password auth (`scram-sha-256`) for all connections, including localhost —
no trust/peer shortcut. There is no way to connect without a real password.

A dedicated role and database were created for this project (see
`CTX-DEC-20260904-dedicated-db-role` for why not the `postgres` superuser):

- Role: `gs_reposts_app`
- Database: `gs_reposts` (owned by that role)
- `frontend/.env`'s `DATABASE_URL` points at `localhost:5432` using this role/database

The actual password is **not** recorded here or anywhere in `Context/` (per `Context/README.md`
security rules) — it only lives in the git-ignored `frontend/.env`. If it's lost, connect as the
`postgres` superuser (password known to the user, entered once during this session — not
recorded) and run `ALTER ROLE gs_reposts_app WITH PASSWORD '...'` to reset it.

## How to verify the setup still works

```bash
export PATH="/c/Program Files/PostgreSQL/17/bin:$PATH"
PGPASSWORD=<password> psql -U gs_reposts_app -h localhost -p 5432 -d gs_reposts -w -c "\dt"
```

Should list `post` and `user` tables (the current starter schema — see
`CTX-FCT-20260904-scaffold`).
