---
id: CTX-FCT-20260909-engine-implementation
type: fact
title: Gatilhos engine implementation — files, and two real bugs found while building it
branch: gatilhos-alertas
tags: [gatilhos, alertas, sqlalchemy, bug, backend]
status: active
confidence: high
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: [CTX-DEC-20260909-gatilhos-rule-model]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-08
valid_until: null
revisit_at: null
---

## Files

- `backend/app/db/models.py` — enums (`CombinadorCondicoes`, `MetricaGatilho`,
  `PeriodoReferenciaGatilho`, `DirecaoGatilho`, `SeveridadeGatilho` + `SEVERIDADE_ORDEM`),
  `_enum_column()` helper, `Gatilho` / `CondicaoGatilho` / `AlertaDisparado` models.
- Migrations: `fa5834948681_create_gatilhos_tables.py`,
  `edcd9ca68242_add_visto_to_alertas_disparados.py`, `59162df51080_add_severidade_to_gatilhos.py`
  — each verified with a full `upgrade head` → `downgrade -1` → `upgrade head` round-trip.
- `backend/app/gatilhos/referencias.py` — `calcular_medias_referencia`, `_intervalo_do_periodo`
  (rolling reference windows, see `DEC-20260909-gatilhos-rule-model.md`).
- `backend/app/gatilhos/avaliacao.py` — `_avaliar_condicao`, `avaliar_gatilhos_da_janela` (the entry
  point called from `scheduler/jobs.py` after every window), `_notificar_frontend_alertas`,
  `_notificar_webhook_externo` (both best-effort, swallow their own failures).
- `backend/app/routers/gatilhos.py` (CRUD, soft-delete) and `backend/app/routers/alertas.py`
  (history + seen/unseen) — see `Context/branches/nextrouter-api`-style route docs; full paths
  listed in `Context/STATE.md`.

## Bug 1 — DetachedInstanceError on `PUT /api/gatilhos/{id}` (fixed)

`session.refresh(gatilho, attribute_names=["condicoes"])` after commit refreshed only the
`condicoes` relationship. `atualizado_em` (`onupdate=func.now()`, server-computed) gets marked
**expired** by SQLAlchemy whenever an UPDATE actually changes a row. Response serialization happens
*after* the `async with` session block closes — touching that expired attribute with no session
attached raised `DetachedInstanceError`, surfacing as an intermittent 500 (only on edits that
changed something, which is why it looked random). **Fix**: include every column that can be
expired post-commit in `attribute_names`, not just the relationship being explicitly reassigned —
`await session.refresh(gatilho, attribute_names=["condicoes", "atualizado_em"])`. General
takeaway for this codebase: any model with an `onupdate=func.now()` column needs that column named
explicitly in `session.refresh()` calls after a commit that might touch it, everywhere in the app,
not just here.

## Bug 2 — reference-window day boundary computed in the wrong timezone (fixed)

`_intervalo_do_periodo` in `referencias.py` originally computed `agora.date()` directly. **asyncpg
always returns UTC-tzinfo datetimes for a `timestamptz` column, regardless of what timezone the
value was originally inserted with** — so `.date()` on the raw value silently used UTC's calendar
day, not the operational timezone's (`America/Sao_Paulo`, UTC-3), shifting the rolling-window
boundary by hours near midnight. **Fix**: `agora.astimezone(tz).date()` before computing
`inicio_hoje`. This is a general asyncpg/Postgres gotcha, not gatilhos-specific — anywhere in this
codebase that needs "what calendar day is this timestamptz value on" must convert to the
operational timezone first; comparing aware datetimes across timezones for ordering is fine
(Python compares absolute instants), only day-boundary/calendar-day logic is affected.

## Relations

- `Context/branches/metrics-pipeline/facts/FCT-20260904-sqlalchemy-postgres-enum-gotchas.md` — a
  sibling SQLAlchemy/Postgres gotcha (native enum `values_callable`) found earlier in the same
  codebase; worth reading together if debugging another SQLAlchemy surprise here.
