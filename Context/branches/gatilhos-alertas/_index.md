# Branch: gatilhos-alertas

## Purpose

Configurable alert-rule system built on top of `metrics-pipeline`'s stored ASR/ACD/PDD data:
user-defined rules ("gatilhos") that fire alerts when a metric moves a threshold percentage
against a rolling reference period, with severity ranking, seen/unseen tracking, and three
delivery channels (badge, history page, webhook + browser notification).

## Scope

- `backend/app/gatilhos/` — the evaluation engine (`referencias.py`, `avaliacao.py`)
- `backend/app/routers/gatilhos.py`, `backend/app/routers/alertas.py` and their schemas
  (`backend/app/schemas/gatilhos.py`, `backend/app/schemas/alertas.py`)
- The `Gatilho` / `CondicaoGatilho` / `AlertaDisparado` models and their enums in
  `backend/app/db/models.py` (shared file with `metrics-pipeline`, but these specific
  classes/tables are owned here)
- `frontend/src/app/gatilhos/`, `frontend/src/app/alertas/`, `frontend/src/lib/gatilhos*.ts`,
  `frontend/src/lib/alertas*.ts`, `frontend/src/lib/severidade.ts`,
  `frontend/src/components/gatilho-*.tsx`, `alertas-table.tsx`
- The alert-firing extension of `frontend/src/lib/metricas-event-bus.ts` and
  `frontend/src/components/live-refresher.tsx` (browser `Notification`)

## Current state

Working end-to-end, verified against real production NextRouter data (real ASR drops triggering
real alerts, both global and per-client rules). Ships with 4 severity levels
(Atenção/Médio/Crítico/Urgente), seen/unseen tracking with a seen-timestamp, and one real bug found
and fixed (`DetachedInstanceError` on `PUT /api/gatilhos/{id}`, see
`facts/FCT-20260909-engine-implementation.md`). A historical backfill script
(`backend/scripts/backfill_historico.py`, lives in `metrics-pipeline`'s scope since it's a
metrics-collection tool, see `Context/branches/metrics-pipeline/_index.md`) exists so reference
periods have enough history to compare against on a fresh environment.

Not yet done: no automated tests; no UI for viewing a gatilho's condition-by-condition evaluation
history (only the final fire/no-fire result is stored).

## Core concepts

- **Global vs. individual rules, evaluated together** — see
  `decisions/DEC-20260909-gatilhos-rule-model.md`.
- **Rolling (not calendar-aligned) reference periods** — ontem/semanal/mensal all end "yesterday",
  moving forward every day. Same decision record.
- **Severity is copied at fire time**, not looked up live from the (possibly since-edited) rule —
  see `decisions/DEC-20260909-severidade-visto-delivery.md`.
- **No time-limited unseen window** — the badge counts all unseen alerts regardless of age, by
  deliberate choice (see the same decision record).
- **Soft-delete only** — `alertas_disparados.gatilho_id` has no `ondelete`, so history blocks a
  real delete by FK; `DELETE /api/gatilhos/{id}` actually sets `ativo=false`.

## Key records

- `decisions/DEC-20260909-gatilhos-rule-model.md`
- `decisions/DEC-20260909-severidade-visto-delivery.md`
- `facts/FCT-20260909-engine-implementation.md` — files, and the two real bugs found (SQLAlchemy
  `session.refresh` expiry, asyncpg UTC-tzinfo day-boundary)
- `Context/global/decisions/DEC-20260909-frontend-design-system-tokens.md` — the UI styling this
  feature's pages/components must follow

## Active decisions

`decisions/DEC-20260909-gatilhos-rule-model.md`, `decisions/DEC-20260909-severidade-visto-delivery.md`.

## Open questions

None currently open.

## Risks

- Same production-caution constraint as the rest of the backend: evaluation runs automatically
  after every real scheduler window, unattended — but it only *reads* `metricas_cliente` (already
  collected data), makes no new NextRouter calls itself, so no additional production-load risk
  beyond what `metrics-pipeline` already accounts for.
- The external alert webhook (`FRONTEND_ALERTAS_WEBHOOK_URL`) is subject to the same port-drift
  risk documented in `Context/core/constraints.md` — confirm the frontend's actual port before
  trusting it.

## Relations to other branches

- `metrics-pipeline` — this branch reads `MetricaCliente` rows and hooks into
  `run_collection_window` (called once per real window, and once per manually-triggered/backfilled
  window too — a gatilho can fire from a manual trigger, not just the automatic schedule).
- `frontend-nextjs-prisma` — owns this feature's pages/components; see that branch's facts for the
  route layout (`/gatilhos`, `/alertas`) and how they fit the multi-tool navigation.
