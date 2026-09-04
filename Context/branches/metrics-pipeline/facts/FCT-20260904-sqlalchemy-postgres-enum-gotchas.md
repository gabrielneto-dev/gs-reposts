---
id: CTX-FCT-20260904-sqlalchemy-postgres-enum-gotchas
type: fact
title: Two SQLAlchemy/Alembic + Postgres native ENUM gotchas hit while building the first migration
branch: metrics-pipeline
tags: [postgres, sqlalchemy, api-quirks]
status: active
confidence: verified
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: []
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-04
valid_until: null
revisit_at: null
---

## Fact

Two distinct bugs surfaced writing the first Alembic migration for the `window_status` Postgres
native enum (`running`/`completed`/`failed`/`partial`), both worth avoiding next time a native
enum is added:

1. **Double `CREATE TYPE` in a hand-written migration**: explicitly creating a generic `sa.Enum(...)`
   type with `.create(bind, checkfirst=True)` and then reusing that same object as a column type in
   `op.create_table(...)` still raised `DuplicateObjectError: type "window_status" already exists`.
   Root cause: a generic `sa.Enum` gets adapted into the dialect-specific `postgresql.ENUM` at
   DDL-compile time, and that adaptation doesn't reliably carry over `create_type=False` set on the
   original object — so `CREATE TABLE` tries to auto-create the type a second time regardless.
   **Fix**: use `sqlalchemy.dialects.postgresql.ENUM` directly (not generic `sa.Enum`) for both the
   explicit `.create(bind, checkfirst=True)` call and the column definition (with `create_type=False`
   on the column's copy) — no adaptation step, so `create_type=False` is actually honored.

2. **SQLAlchemy's `Enum(PythonEnumClass, ...)` sends the member `.name`, not `.value`, by default**:
   with `class WindowStatus(str, enum.Enum): RUNNING = "running"`, inserting
   `WindowStatus.RUNNING` produced `InvalidTextRepresentationError: invalid input value for enum
   window_status: "RUNNING"` — SQLAlchemy sent the literal member name (`RUNNING`), but the Postgres
   type only has the lowercase `.value`s (`running`). **Fix**: pass
   `values_callable=lambda enum_cls: [member.value for member in enum_cls]` to the SQLAlchemy
   `Enum(...)` column type whenever the Python enum's member names and values differ in case (this
   project's convention is `UPPER_CASE` Python names, `lower_case` stored values, everywhere it
   uses `str, enum.Enum`).

## Verification

Both fixes confirmed live: `alembic upgrade head` created the 3 tables cleanly, and a real
`INSERT` into `collection_windows` with `status=WindowStatus.RUNNING` stored the lowercase
`'running'` correctly, transitioning to `'completed'`/`'partial'` on the same row without error.
