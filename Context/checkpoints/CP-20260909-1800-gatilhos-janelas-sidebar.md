---
id: CTX-CP-20260909-1800-gatilhos-janelas-sidebar
type: checkpoint
title: Gatilhos/alertas feature, janelas status page, multi-tool sidebar navigation
branch: global
tags: [checkpoint, gatilhos, alertas, janelas, navigation, design-system]
status: active
confidence: high
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: [CTX-DEC-20260909-gatilhos-rule-model, CTX-DEC-20260909-severidade-visto-delivery, CTX-DEC-20260909-manual-window-trigger, CTX-DEC-20260909-multi-tool-navigation-architecture, CTX-DEC-20260909-frontend-design-system-tokens, CTX-CP-20260908-1700-live-verification-and-process-cleanup]
depends_on: [CTX-CP-20260908-1700-live-verification-and-process-cleanup]
supersedes: null
superseded_by: null
valid_from: 2026-09-09
valid_until: null
revisit_at: null
---

## Objective

Persist everything built since the last checkpoint (`CP-20260908-1700-live-verification-and-process-cleanup`,
at commit `f84c431`): the gatilhos/alertas configurable alert-rule system, a historical backfill
script, a janelas (collection-window) status page with manual trigger, a multi-tool double-sidebar
navigation replacing the old top nav, and the frontend design-system tokens that emerged from
restyling it. Covers commits `2ba6674` through `24784db`, plus uncommitted work at save time
(sidebar restyle to light theme, `/` → `/relatorios` route move).

## What changed

- **Gatilhos/alertas** (new branch `gatilhos-alertas`): configurable alert rules (global + per-client,
  AND/OR conditions, percentage threshold vs. rolling ontem/semanal/mensal reference), 4 severity
  levels (Atenção/Médio/Crítico/Urgente), seen/unseen tracking with a seen-timestamp, delivery via
  table badge + `/alertas` history page + external webhook + browser `Notification`. See
  `Context/branches/gatilhos-alertas/_index.md`.
- **Historical backfill** (`backend/scripts/backfill_historico.py`): built to backfill N days, only
  actually run for "yesterday" per a mid-task user course correction. See
  `Context/branches/metrics-pipeline/decisions/DEC-20260909-backfill-scope-yesterday-only.md`.
- **Janelas status page** (`/janelas`): day/week/month views of the 15 canonical daily collection
  slots, manual trigger for missed past slots (future blocked), guarded by a shared `asyncio.Lock`
  against overlapping the automatic scheduler. See
  `Context/branches/metrics-pipeline/decisions/DEC-20260909-manual-window-trigger.md` and
  `Context/branches/frontend-nextjs-prisma/facts/FCT-20260909-janelas-page.md`.
- **Multi-tool double sidebar**: replaced the single horizontal top nav with a Pipedrive-style icon
  rail + grouped panel, driven by a data-driven `FERRAMENTAS` array so future tools are just new
  array entries. See
  `Context/branches/frontend-nextjs-prisma/decisions/DEC-20260909-multi-tool-navigation-architecture.md`.
- **Frontend design system tokens formalized**: the sidebar was first built with Pipedrive's dark
  palette, then restyled to the app's actual light amber/zinc system on the user's next message —
  now written down as a standing convention. See
  `Context/global/decisions/DEC-20260909-frontend-design-system-tokens.md`.
- **Route move**: clients-overview page moved `/` → `/relatorios`; `/` is now a redirect. See
  `Context/branches/frontend-nextjs-prisma/facts/FCT-20260909-relatorios-route-move.md`.

## Decisions made

- `CTX-DEC-20260909-gatilhos-rule-model`, `CTX-DEC-20260909-severidade-visto-delivery`
  (gatilhos-alertas)
- `CTX-DEC-20260909-manual-window-trigger`, `CTX-DEC-20260909-backfill-scope-yesterday-only`
  (metrics-pipeline)
- `CTX-DEC-20260909-multi-tool-navigation-architecture` (frontend-nextjs-prisma)
- `CTX-DEC-20260909-frontend-design-system-tokens` (global)

## Discoveries / problems solved

- **`DetachedInstanceError` 500 on `PUT /api/gatilhos/{id}`** (recurred across sessions, finally
  root-caused): `session.refresh()` after commit omitted `atualizado_em`
  (`onupdate=func.now()`), which SQLAlchemy expires on any real UPDATE; reading it after the session
  closed raised the error. Fixed by including it in `attribute_names`. Verified via direct in-process
  ASGI reproduction before/after. See
  `Context/branches/gatilhos-alertas/facts/FCT-20260909-engine-implementation.md`.
- **Reference-window day boundary computed in UTC instead of the operational timezone**: asyncpg
  always returns UTC-tzinfo datetimes for `timestamptz` columns regardless of original insert
  timezone; `_intervalo_do_periodo` now converts to `America/Sao_Paulo` before computing `.date()`.
  Same fact file — general asyncpg/Postgres gotcha, not gatilhos-specific.
- **"Hoje" nav button on `/janelas` never reflected the viewed date** — fixed alongside two small
  Tailwind bugs (`capitalize` mangling Portuguese "de", a raw-enum month label missing its
  circumflex). See `Context/branches/frontend-nextjs-prisma/facts/FCT-20260909-janelas-page.md`.
- **`frontend/src/lib/navegacao.ts` created with the wrong extension** (contained JSX, needed
  `.tsx`) — deleted and recreated correctly.
- **Backend process found not running** at the start of this session (fetch failed on
  `/relatorios`) — restarted cleanly; added to `Context/core/constraints.md` as a known recurring
  pattern on this machine (check the port before assuming a code regression).

## Investigated, not fixed (deliberately)

- **ASR discrepancy vs. NextRouter's own "SIP Codes / Assinante" report**: extensive empirical
  testing found our number internally consistent; the platform's own report was described by the
  user as "flutuante" and is a plausible-but-unconfirmed unreliable reference. Did **not** alter the
  ASR formula without a confirmed root cause. See
  `Context/branches/nextrouter-api/research/RES-20260909-asr-discrepancy-vs-sip-codes-report.md` —
  still an open question if it recurs.

## Current state

- All of the above through commit `24784db` is pushed to `main` on GitHub.
- **Uncommitted at save time**: the sidebar's dark→light restyle
  (`frontend/src/components/sidebar-dupla.tsx`) and the `/` → `/relatorios` route move (`page.tsx`
  moved to `relatorios/page.tsx`, redirect added, `navegacao.tsx`/`alertas-actions.ts` updated to
  match) — both verified working live in the browser preview, not yet committed. Per the user's
  standing preference, wait for an explicit "pode commitar"/"pode subir" before committing/pushing.
- Two harmless "test" `janelas_coleta` rows from 2026-09-08 live verification still exist in the
  real database (informational only, carried over from the prior checkpoint, still not cleaned up).

## Open questions

- Whether the NextRouter platform's "SIP Codes / Assinante" report is ever a reliable historical
  reference (see the research record above).
- Whether/when a fuller historical backfill (beyond "yesterday") will be wanted — script already
  supports it via `--dias`.
- Auth strategy for the frontend — still not decided, still not urgent.

## Next likely steps

1. Commit and push the uncommitted sidebar restyle + route-move work once the user asks.
2. If the user adds a second "ferramenta", extend `FERRAMENTAS` in
   `frontend/src/lib/navegacao.tsx` following
   `Context/branches/frontend-nextjs-prisma/decisions/DEC-20260909-multi-tool-navigation-architecture.md`
   — don't touch `sidebar-dupla.tsx` itself unless the layout itself needs to change.
3. Any new frontend page must follow
   `Context/global/decisions/DEC-20260909-frontend-design-system-tokens.md` from the start.
4. Before debugging a frontend "fetch failed" report, check whether `backend/`'s `uvicorn` is
   actually running first — see the new bullet in `Context/core/constraints.md`.

## Affected files/artifacts

Backend: `app/db/models.py`, 3 new Alembic migrations, `app/gatilhos/` (new), `app/routers/gatilhos.py`,
`app/routers/alertas.py`, `app/schemas/gatilhos.py`, `app/schemas/alertas.py`, `app/scheduler/grade.py`
(new), `app/scheduler/jobs.py`, `app/scheduler/scheduler.py`, `app/routers/metricas.py`,
`app/schemas/metricas.py`, `scripts/backfill_historico.py` (new).
Frontend: `src/lib/gatilhos.ts`/`gatilhos-actions.ts`/`alertas.ts`/`alertas-actions.ts`/`severidade.ts`
(new), `src/components/gatilho-form.tsx`/`gatilho-card.tsx`/`alertas-table.tsx` (new),
`src/lib/calendario.ts` (new), `src/lib/janelas.ts`/`janelas-actions.ts` (new),
`src/app/janelas/page.tsx` + `dia-janelas.tsx`/`semana-janelas.tsx`/`mes-janelas.tsx` (new),
`src/lib/navegacao.tsx` (new), `src/components/sidebar-dupla.tsx` (new, then restyled),
`src/app/layout.tsx` (edited), `src/components/nav-bar.tsx` (deleted),
`src/app/relatorios/page.tsx` (moved from `src/app/page.tsx`, which is now a redirect).

## Records created/updated this checkpoint

Created: `global/decisions/DEC-20260909-frontend-design-system-tokens.md`,
`branches/gatilhos-alertas/_index.md` + 2 decisions + 1 fact,
`branches/metrics-pipeline/decisions/DEC-20260909-manual-window-trigger.md`,
`branches/metrics-pipeline/decisions/DEC-20260909-backfill-scope-yesterday-only.md`,
`branches/frontend-nextjs-prisma/decisions/DEC-20260909-multi-tool-navigation-architecture.md`,
`branches/frontend-nextjs-prisma/facts/FCT-20260909-janelas-page.md`,
`branches/frontend-nextjs-prisma/facts/FCT-20260909-relatorios-route-move.md`,
`branches/nextrouter-api/research/RES-20260909-asr-discrepancy-vs-sip-codes-report.md`,
this checkpoint. Updated: `branches/metrics-pipeline/_index.md`,
`branches/frontend-nextjs-prisma/_index.md`, `branches/nextrouter-api/_index.md`,
`core/constraints.md`, `MAP.md`, `STATE.md`.
