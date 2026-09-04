# Project Overview

**Status: confirmed** (2026-09-04). See `CTX-FCT-20260904-project-purpose-confirmed`.

`gs-reposts` (GitHub repo name; local directory still called `relatorios`) is a **monorepo** for a
VoIP telephony company (GS VoIP)'s internal reporting system. Two halves, split
2026-09-04 (see `Context/global/decisions/DEC-20260904-monorepo-restructure.md`):

- **`backend/`** — Python/FastAPI service that fronts the company's **NextRouter C4 SoftSwitch**
  (NextBilling IP Solutions, `sip5.gsvoip.com.br`) and exposes clean, read-only HTTP endpoints for
  ASR/ACD/PDD metrics and client lookups. An **adapter only** — no database, not the system of
  record. See `Context/branches/nextrouter-api/_index.md`.
- **`frontend/`** — Next.js 16 + Prisma 8 (Postgres) app, still being built. Owns its own
  database; is the actual system of record. Will consume `backend/`'s endpoints for softswitch
  data. See `Context/branches/frontend-nextjs-prisma/_index.md`.

## Where things live

- Repo: `https://github.com/gabrielneto-dev/gs-reposts.git`, branch `main`
- Backend code: `backend/app/` (`config.py`, `clients/nextrouter.py`, `routers/`, `schemas/`,
  `utils/`) — run with `cd backend && uvicorn app.main:app --reload`
- Backend route docs: `backend/docs/API.md`
- Frontend code: `frontend/src/` (Next.js App Router at `src/app/`, Prisma at `src/prisma/`) — run
  with `cd frontend && npm run dev`
- Root `README.md` — the map of the monorepo, read it first in a new session
- Credentials: `backend/.env` (NextRouter) and `frontend/.env` (Postgres `DATABASE_URL`), both
  git-ignored — never committed; see `Context/core/constraints.md`
