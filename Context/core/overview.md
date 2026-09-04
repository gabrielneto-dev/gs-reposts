# Project Overview

**Status: confirmed** (2026-09-04). See `CTX-FCT-20260904-project-purpose-confirmed`.

`gs-reposts` (GitHub repo name; local directory still called `relatorios`) is a **monorepo** for a
VoIP telephony company (GS VoIP)'s internal reporting system. Two halves, split 2026-09-04 (see
`Context/global/decisions/DEC-20260904-monorepo-restructure.md`), with the storage ownership
amended the same day (see `Context/global/decisions/DEC-20260904-backend-owns-storage-and-scheduler.md`):

- **`backend/`** — Python/FastAPI service that fronts the company's **NextRouter C4 SoftSwitch**
  (NextBilling IP Solutions, `sip5.gsvoip.com.br`) and exposes clean, read-only HTTP endpoints for
  ASR/ACD/PDD metrics and client lookups (`Context/branches/nextrouter-api/_index.md`). It also
  **owns a Postgres database and a scheduler** (`Context/branches/metrics-pipeline/_index.md`) that
  periodically discovers active clients and stores their exact ASR/ACD/PDD per time window —
  **it is now the system of record**, not just an adapter.
- **`frontend/`** — Next.js 16 app, still being built. **No database, no ORM** — a pure HTTP
  consumer of `backend/`'s API (no integration code written yet). See
  `Context/branches/frontend-nextjs-prisma/_index.md`.

## Where things live

- Repo: `https://github.com/gabrielneto-dev/gs-reposts.git`, branch `main`
- Backend code: `backend/app/` (`config.py`, `clients/nextrouter.py`, `routers/`, `schemas/`,
  `utils/`, `db/`, `scheduler/`) — run with `cd backend && uvicorn app.main:app --reload`
- Backend route docs: `backend/docs/API.md`
- Backend migrations: `backend/alembic/` (`alembic upgrade head`)
- Frontend code: `frontend/src/` (Next.js App Router at `src/app/`) — run with
  `cd frontend && npm run dev`
- Root `README.md` — the map of the monorepo, read it first in a new session
- Credentials: `backend/.env` (NextRouter API + the metrics Postgres `DATABASE_URL`), both
  git-ignored — never committed; see `Context/core/constraints.md`. `frontend/.env` no longer holds
  anything (Prisma removed).
