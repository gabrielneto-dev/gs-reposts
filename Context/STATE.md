# Project State

Last updated: 2026-09-09
Latest checkpoint: `Context/checkpoints/CP-20260909-1800-gatilhos-janelas-sidebar.md`

## Current objective

No specific new task queued as of this checkpoint. Just landed a large batch of work (gatilhos/
alertas, janelas status page, multi-tool sidebar). Good candidate for the next message: commit and
push the currently-uncommitted sidebar restyle + `/relatorios` route move (see "In progress"
below), if the user asks.

## Working

- `backend/`: configurable alert rules ("gatilhos") — global + per-client, AND/OR conditions,
  percentage threshold vs. rolling ontem/semanal/mensal reference periods, 4 severity levels,
  evaluated after every collection window (automatic, manual, or backfilled). Seen/unseen tracking
  with a seen-timestamp. Delivered via client-table badge, `/alertas` history page, external
  webhook, and a browser `Notification`. See `Context/branches/gatilhos-alertas/_index.md`.
- `backend/`: `/janelas` status page backed by `GET /api/metricas/janelas/grade` +
  `POST /api/metricas/janelas/disparar` — status of the 15 canonical daily slots, manual trigger for
  missed past slots (future blocked), guarded by a shared `asyncio.Lock` against overlapping the
  automatic scheduler. See
  `Context/branches/metrics-pipeline/decisions/DEC-20260909-manual-window-trigger.md`.
- `backend/`: a historical backfill script exists (`scripts/backfill_historico.py`, supports
  `--dias N` / `--dia YYYY-MM-DD`) but has only actually been run for "yesterday" so far — don't
  assume a deep history of `metricas_cliente` exists. See
  `Context/branches/metrics-pipeline/decisions/DEC-20260909-backfill-scope-yesterday-only.md`.
- `backend/`: scheduler still fires 15x/day — `[00:00,07:00)`, hourly 07:00-20:00, `[20:00,00:00)`.
  **The backend `uvicorn` process has been found not running between sessions on this machine** —
  if the frontend shows a generic "fetch failed", check `http://127.0.0.1:8000/docs` before
  assuming a code bug. See `Context/core/constraints.md`'s "Dev-server process management" section.
- `frontend/`: multi-page now, navigated via a double sidebar (icon rail + grouped panel) driven by
  a data-driven `FERRAMENTAS` array in `src/lib/navegacao.tsx` — adding a future tool is meant to be
  just a new array entry. See
  `Context/branches/frontend-nextjs-prisma/decisions/DEC-20260909-multi-tool-navigation-architecture.md`.
  Pages: `/relatorios` (clients overview, moved off `/` — `/` now redirects there), `/gatilhos`,
  `/alertas`, `/janelas`.
- `frontend/`: the app's light amber/zinc design system is now written down explicitly — see
  `Context/global/decisions/DEC-20260909-frontend-design-system-tokens.md`. New pages/tools should
  follow it from the start rather than re-deriving a palette.
- Still no database on the frontend side, no auth.
- Repo on GitHub: `https://github.com/gabrielneto-dev/gs-reposts.git` (branch `main`, at `24784db`
  as of this checkpoint).
- Two small harmless "test" `janelas_coleta` rows exist in the real database from 2026-09-08 live
  verification — informational only, still not cleaned up.

## In progress

Uncommitted at save time (both verified working live, not yet committed per the user's standing
preference to only commit/push on explicit request):

- `frontend/src/components/sidebar-dupla.tsx` restyled from its initial dark Pipedrive-style
  palette to the app's light design system tokens.
- `/` → `/relatorios` route move: `src/app/page.tsx` moved to `src/app/relatorios/page.tsx`; `/` is
  now a small redirect page; `navegacao.tsx` and `alertas-actions.ts`'s `revalidatePath` calls
  updated to match.

## Blockers

None currently. See `Context/core/constraints.md` for recurring environment quirks: the harness's
classifier occasionally blocking ordinary commands (retry once), connection-reset-shaped errors on
this Windows machine during concurrent async I/O that can be transient, duplicate backend
processes from re-running `start-dev.ps1`, the frontend's dev port silently drifting, **a second
unrelated local project ("voip-monitor") also competing for ports 3000/3001** (has broken
webhook/notification delivery more than once — check which process is actually listening, not just
whether the port responds), and the backend `uvicorn` process being found not running at all
between sessions (check before assuming a code regression).

## Active decisions

- `CTX-DEC-20260904-monorepo-restructure`, `CTX-DEC-20260904-backend-owns-storage-and-scheduler`,
  `CTX-DEC-20260908-portuguese-schema-naming`, `CTX-DEC-20260909-frontend-design-system-tokens`
  (global)
- `CTX-DEC-20260904-sampling-with-exact-mode`, `CTX-DEC-20260904-route-simplification`,
  `CTX-DEC-20260904-activity-detection-day-by-day` (nextrouter-api)
- `CTX-DEC-20260908-collection-window-00h-split` (supersedes `DEC-20260904-collection-window-schedule`),
  `CTX-DEC-20260904-sampled-discovery-exact-client-metrics`,
  `CTX-DEC-20260908-clientes-resumo-period-filter`,
  `CTX-DEC-20260908-frontend-webhook-notification`,
  `CTX-DEC-20260909-manual-window-trigger`,
  `CTX-DEC-20260909-backfill-scope-yesterday-only` (metrics-pipeline)
- `CTX-DEC-20260908-sse-same-origin-live-refresh`,
  `CTX-DEC-20260909-multi-tool-navigation-architecture`, plus the fetch-strategy choice in
  `FCT-20260908-clientes-overview-page` (frontend-nextjs-prisma)
- `CTX-DEC-20260909-gatilhos-rule-model`, `CTX-DEC-20260909-severidade-visto-delivery`
  (gatilhos-alertas)

## Open critical questions

- Frontend data model (beyond consuming `backend/`) and auth strategy — not yet decided.
- Whether the transient-network-failure risk in `metrics-pipeline` needs a retry — needs more
  unattended run time before deciding.
- Whether NextRouter's own "SIP Codes / Assinante" report is ever a reliable historical reference —
  see `Context/branches/nextrouter-api/research/RES-20260909-asr-discrepancy-vs-sip-codes-report.md`.
- If the frontend is ever scaled to multiple processes, the live-refresh event bus (in-memory,
  single-process) needs a real pub/sub backend — not urgent today.

## Next likely steps

1. Commit and push the uncommitted sidebar restyle + `/relatorios` route move if the user asks.
2. If the user asks for anything in `backend/`'s live routes, check
   `Context/branches/nextrouter-api/_index.md` first.
3. If the user asks for anything about stored metrics/scheduling/schema/webhooks/janelas, check
   `Context/branches/metrics-pipeline/_index.md` first — naming is Portuguese
   (`Context/global/decisions/DEC-20260908-portuguese-schema-naming.md`).
4. If the user asks for anything about alert rules/severity/seen-unseen, check
   `Context/branches/gatilhos-alertas/_index.md` first.
5. If the user asks for new frontend pages/tools, check
   `Context/branches/frontend-nextjs-prisma/decisions/DEC-20260909-multi-tool-navigation-architecture.md`
   (how to add a tool to `FERRAMENTAS`) and
   `Context/global/decisions/DEC-20260909-frontend-design-system-tokens.md` (the visual language to
   use) first.
6. Any new DB table/column or API field must be named in Portuguese — see the `AGENTS.md`
   Conventions section.
7. Before restarting or debugging the backend dev process, read `Context/core/constraints.md`'s
   "Dev-server process management" section first.
