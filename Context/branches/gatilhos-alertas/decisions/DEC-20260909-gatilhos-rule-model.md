---
id: CTX-DEC-20260909-gatilhos-rule-model
type: decision
title: Gatilhos data/rule model — global + per-client rules, AND/OR conditions, rolling reference periods
branch: gatilhos-alertas
tags: [gatilhos, alertas, rule-engine, data-model]
status: active
confidence: high
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: [CTX-DEC-20260909-severidade-visto-delivery]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-08
valid_until: null
revisit_at: null
---

## Decision

Built a configurable alert-rule system on top of the existing `metricas_cliente` data
(`Context/branches/metrics-pipeline/`):

- **`gatilhos` table**: a rule = `nome`, optional `cliente_id` (null = **global**, applies to every
  client; set = **individual**, applies only to that client — globals and individuals are always
  evaluated together, not mutually exclusive), `combinador` (`e`/`ou` — how its conditions combine),
  `ativo` (bool), `severidade` (see `DEC-20260909-severidade-visto-delivery.md`).
- **`condicoes_gatilho` table**: one row per condition inside a gatilho — `metrica`
  (`asr_percentual` | `acd_segundos` | `pdd_medio_segundos`), `periodo_referencia`
  (`media_ontem` | `media_semanal` | `media_mensal`), `direcao` (`aumento` | `queda` | `qualquer`),
  `percentual_limite` (e.g. "ASR fell 20%+ vs. yesterday's average → fire").
- **Reference periods are rolling windows, not calendar-aligned** (`app/gatilhos/referencias.py`,
  `_intervalo_do_periodo`): `media_ontem` = the complete previous calendar day; `media_semanal` /
  `media_mensal` = the last 7 / 30 running days ending yesterday (today, still in progress, is
  always excluded). Chosen explicitly over calendar week/month so there's always a comparison
  baseline even on a Monday or the 1st of the month.
- Evaluated after **every** collection window closes (`avaliar_gatilhos_da_janela`, called from
  `backend/app/scheduler/jobs.py`'s `run_collection_window`), not on a separate schedule.
- A gatilho with a real firing history is **soft-deleted** (`ativo=False` via `DELETE
  /api/gatilhos/{id}`, which is actually a `PUT ativo=false`), never hard-deleted — `alertas_disparados.gatilho_id`
  has no `ondelete`, so a real delete would be blocked by FK anyway; this was deliberate so history
  is never silently lost.

## Why

The user wanted rules like "if today's average ASR drops 20%+ vs. yesterday, fire an alert" or "ASR
down but PDD up, fire", configurable both globally and per-client, using percentage thresholds
against a prior reference (yesterday/weekly/monthly average) — their own words, from the session
that started this feature: "quero gatilhos configuráveis... posso criar uma regra de porcentagem,
que por exemplo se o asr médio de hoje diminuir 20% já ativa o alerta... com base tanto na média
mensal [quanto] semanal [quanto] de ontem". The rolling-vs-calendar-aligned choice was an explicit
`AskUserQuestion` the user answered directly.

## Consequences

- `calcular_medias_referencia` does one batched query per period type across all needed clients
  (not one query per client/condition) specifically to avoid N+1 when many gatilhos share a
  reference period in the same evaluation pass.
- A fresh agent asked to add a new `metrica`/`periodo_referencia`/`direcao` option should extend the
  enums in `backend/app/db/models.py` (`MetricaGatilho`, `PeriodoReferenciaGatilho`,
  `DirecaoGatilho`) plus `_intervalo_do_periodo`'s `_DIAS_DO_PERIODO` map and `_avaliar_condicao` in
  `app/gatilhos/avaliacao.py` — all three need to move together.
- See `facts/FCT-20260909-engine-implementation.md` for the concrete files/bugs found while
  building this.
