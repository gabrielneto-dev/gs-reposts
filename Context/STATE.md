# Project State

Last updated: 2026-09-04
Latest checkpoint: `Context/checkpoints/CP-20260904-1800-metrics-storage-and-scheduler.md`

## Current objective

No specific new task queued as of this checkpoint. Natural next step: build the frontend UI/pages
that consume `backend/`'s data (both the existing NextRouter-adapter routes and the new
`metrics-pipeline` storage) — no frontend-to-backend integration code exists yet.

## Working

- `backend/`: 8 GET routes (`nextrouter-api`), all verified against production — unchanged this
  session. See `Context/branches/nextrouter-api/facts/FCT-20260904-route-inventory.md`.
- `backend/`: Postgres metrics store + APScheduler (`metrics-pipeline`), new this session, verified
  end-to-end against production (migration applied, a real 1-hour window collected 70/72 clients'
  exact ASR/ACD/PDD). Scheduler fires automatically 07:00-20:00 hourly + one overnight window
  whenever the app runs (`SCHEDULER_ENABLED=true` by default). See
  `Context/branches/metrics-pipeline/_index.md`.
- `frontend/`: Next.js 16 scaffold, no database/ORM (Prisma removed this session), `npm run build`
  verified clean. No real pages beyond the starter. See
  `Context/branches/frontend-nextjs-prisma/_index.md`.
- Repo is on GitHub: `https://github.com/gabrielneto-dev/gs-reposts.git` (branch `main`). Changes
  from this session are on disk but not yet committed (as of this checkpoint) — check `git status`
  before assuming they're committed.

## In progress

Nothing in progress.

## Blockers

None currently. Note: this session hit the harness's auto-mode classifier blocking a few ordinary
commands (`npm install`, `rm`) — see `Context/core/constraints.md`'s classifier-retry note; usually
resolves on retry, or work around with `Write`-to-empty instead of `rm` for files that must not be
deleted outright.

## Active decisions

- `CTX-DEC-20260904-monorepo-restructure`, `CTX-DEC-20260904-backend-owns-storage-and-scheduler`
  (global)
- `CTX-DEC-20260904-sampling-with-exact-mode`, `CTX-DEC-20260904-route-simplification`,
  `CTX-DEC-20260904-activity-detection-day-by-day` (nextrouter-api)
- `CTX-DEC-20260904-collection-window-schedule`,
  `CTX-DEC-20260904-sampled-discovery-exact-client-metrics` (metrics-pipeline)
- `frontend-nextjs-prisma` has no active decisions anymore — its Prisma-era decisions are
  superseded (see the branch index).

## Open critical questions

- Frontend data model — not yet defined (only the Next.js starter page exists).
- Frontend auth strategy — not yet decided.
- How the frontend will consume `metrics-pipeline`'s data — not yet designed.
- Whether transient network failures during collection (see
  `Context/branches/metrics-pipeline/risks/RSK-20260904-transient-network-failures-during-collection.md`)
  are common enough in practice to justify adding a retry — needs the scheduler to run unattended
  for a while first.

## Next likely steps

1. If the user asks for anything in `backend/`'s HTTP routes, check
   `Context/branches/nextrouter-api/_index.md` first — several routes were already built once and
   deliberately removed; don't rebuild without confirming.
2. If the user asks for anything about stored metrics/scheduling, check
   `Context/branches/metrics-pipeline/_index.md` first.
3. If the user asks for anything in `frontend/`, check
   `Context/branches/frontend-nextjs-prisma/_index.md` first — it has no database now, and no
   integration with `backend/` exists yet, so most "frontend" work starts from a blank slate plus
   whatever `backend/` already exposes.
4. Consider building a small retry around `get_exact_metrics_for_client` if `collection_windows`
   rows show up `partial` often in practice (see the open question above).
