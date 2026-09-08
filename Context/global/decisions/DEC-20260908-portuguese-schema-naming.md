---
id: CTX-DEC-20260908-portuguese-schema-naming
type: decision
title: Database tables/columns and API response fields are named in Portuguese, not English
branch: global
tags: [postgres, api-design, i18n]
status: active
confidence: high
created_at: 2026-09-08
updated_at: 2026-09-08
source_ids: []
related: [CTX-FCT-20260904-schema-and-reused-functions]
depends_on: []
supersedes: null
superseded_by: null
---

# Decision

## Context

The `metrics-pipeline` schema was originally built with English table/column names
(`clients`, `collection_windows`, `client_metrics`, `window_start`, `status`, `error_message`,
etc.) mixed in with already-Portuguese ones (`cliente_id`, `asr_percentual`...). The user
explicitly said they don't read English comfortably and asked for everything translated.

## Decision

**Every DB table, column, enum type/value, and the matching API JSON response field is now in
Portuguese.** Renamed via `backend/alembic/versions/443403c95504_...py` (data-preserving rename,
not a drop/recreate):

| Old (English) | New (Portuguese) |
|---|---|
| `clients` (table) | `clientes` |
| `collection_windows` (table) | `janelas_coleta` |
| `client_metrics` (table) | `metricas_cliente` |
| `window_status` (enum type) | `situacao_janela` |
| `running`/`completed`/`failed`/`partial` (enum values) | `em_andamento`/`concluida`/`falhou`/`parcial` |
| `window_start` / `window_end` | `inicio_janela` / `fim_janela` |
| `first_seen_at` / `last_seen_at` / `updated_at` / `created_at` / `started_at` / `finished_at` | `visto_pela_primeira_vez_em` / `visto_pela_ultima_vez_em` / `atualizado_em` / `criado_em` / `iniciado_em` / `finalizado_em` |
| `status` (column) | `situacao` |
| `error_message` | `mensagem_erro` |
| `discovery_sample_limit` / `clients_discovered` / `clients_processed` | `limite_amostra_descoberta` / `clientes_descobertos` / `clientes_processados` |
| `occurrences_discovery` | `ocorrencias_descoberta` |
| `window_id` | `janela_id` |

Matching Python: `Client`→`Cliente`, `CollectionWindow`→`Janela`, `ClientMetric`→`MetricaCliente`,
`WindowStatus`→`SituacaoJanela` (in `backend/app/db/models.py`). The Pydantic response schemas in
`backend/app/schemas/metricas.py` were renamed field-for-field to match, and the `/api/metricas/janelas`
query param `status` became `situacao` (values now `em_andamento`/`concluida`/`falhou`/`parcial`).

Fields that were already Portuguese (`cliente_id`, `nome`, `total_atendidas`, `total_falhas`,
`asr_percentual`, `acd_segundos`, `pdd_medio_segundos`, `truncado`, `volume_dia`) were left as-is.

## Rationale

The user is the primary (and currently only) consumer of this system's raw data/API and does not
read English well. Half-English/half-Portuguese naming (as it was) is worse than either fully
consistent choice — picked Portuguese since that's what the user actually reads, and most of the
schema was already Portuguese anyway.

## Consequences

- **Going forward, name all new tables, columns, enum values, and API response fields in
  Portuguese** — this is now the project's naming convention, not a one-off. Flagged in `AGENTS.md`
  as an operating rule so future sessions don't reintroduce English names by habit.
- `nextrouter-api`'s existing routes (`/api/asr`, `/api/acd`, `/api/pdd`, `/api/clientes/*`) were
  **not** touched — they were already all-Portuguese from the start, nothing to rename there.
- Internal Python local variable names (e.g. `window_start`/`window_end` as function parameters in
  `backend/app/scheduler/jobs.py`) were deliberately left in English where they're pure
  implementation detail with no DB/API surface — only names that appear in the database or in an
  HTTP response were translated. Don't assume every identifier in the codebase is Portuguese.

## Related records

`CTX-FCT-20260904-schema-and-reused-functions` (updated in place with the new names),
`branches/metrics-pipeline/_index.md`.
