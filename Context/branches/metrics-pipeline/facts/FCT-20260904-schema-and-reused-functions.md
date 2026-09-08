---
id: CTX-FCT-20260904-schema-and-reused-functions
type: fact
title: Postgres schema (3 tables) and the exact reuse map between routes and the scheduler job
branch: metrics-pipeline
tags: [postgres, scheduler, api-design]
status: active
confidence: verified
created_at: 2026-09-04
updated_at: 2026-09-08
source_ids: []
related: [CTX-FCT-20260904-route-inventory, CTX-DEC-20260908-portuguese-schema-naming, CTX-DEC-20260908-collection-window-00h-split]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-04
valid_until: null
revisit_at: null
---

## Fact

**Database**: `gs_reposts_metrics`, role `gs_reposts_backend`, same local Postgres 17 instance the
frontend already used (see `Context/branches/frontend-nextjs-prisma/facts/FCT-20260904-local-postgres.md`)
— a separate database/role from the frontend's old `gs_reposts`/`gs_reposts_app`, per
`CTX-DEC-20260904-dedicated-db-role`'s "least-privilege, dedicated role" principle applied again.
Credentials live in `backend/.env`'s `DATABASE_URL` (not recorded here, per `Context/README.md`
security rules).

**Migrations**: Alembic (`backend/alembic/`), async template, `env.py` wired to
`app.config.settings.database_url` and `app.db.base.Base.metadata` (autogenerate-ready for future
schema changes). Two migrations: `62ecd3fd9f03` (initial schema, hand-written) and `443403c95504`
(2026-09-08, renamed every table/column/enum to Portuguese — see
`CTX-DEC-20260908-portuguese-schema-naming` — via `op.rename_table`/`op.alter_column`, data
preserved, not a drop/recreate).

**Tables** (`backend/app/db/models.py` — names as of 2026-09-08, see the Portuguese-naming
decision for the old-English → new-Portuguese map):

- `clientes` (model `Cliente`) — dimension, PK `cliente_id` (the NextRouter `customer_id`, natural
  key). `nome`, `visto_pela_primeira_vez_em`, `visto_pela_ultima_vez_em`, `atualizado_em`.
  Upserted whenever a client shows up in a discovery scan.
- `janelas_coleta` (model `Janela`) — one row per scheduler run: `inicio_janela`/`fim_janela`
  (unique together), `limite_amostra_descoberta`, `clientes_descobertos`, `clientes_processados`,
  `situacao` (enum `situacao_janela`: `em_andamento`/`concluida`/`falhou`/`parcial`),
  `mensagem_erro`, `iniciado_em`/`finalizado_em`. Gives an audit trail of the scheduler itself.
- `metricas_cliente` (model `MetricaCliente`) — the actual data: FK to both `janelas_coleta`
  (`janela_id`) and `clientes`, denormalized `inicio_janela`/`fim_janela` (so per-client
  time-series queries don't need a join), exact
  `total_atendidas`/`total_falhas`/`asr_percentual`/`acd_segundos`/`pdd_medio_segundos`,
  `ocorrencias_descoberta` (transparency field, see
  `decisions/DEC-20260904-sampled-discovery-exact-client-metrics.md`), `truncado`. Unique on
  `(cliente_id, inicio_janela, fim_janela)`. Indexed on `(cliente_id, inicio_janela DESC)` and
  `inicio_janela` alone.
- No partitioning yet (15 windows/day × active clients is low volume) — revisit only if real
  volume justifies it.
- The Postgres-internal PK/FK/sequence names (e.g. `client_metrics_pkey`, `client_metrics_id_seq`)
  were deliberately **not** renamed during the Portuguese migration — cosmetic, not worth the
  churn. Don't be surprised seeing English in `\d metricas_cliente`'s constraint names.

**Read endpoints on top of this schema** (`backend/app/routers/metricas.py`,
`backend/app/schemas/metricas.py`), all DB-only (never call the softswitch):

- `GET /api/metricas/clientes` — one row per client, their **latest** collected window's
  ASR/ACD/PDD, plus `volume_dia` (calls summed across **every** window collected **today**, not
  just the latest one — a separate `GROUP BY cliente_id` query, added after the user pointed out
  that showing only the latest window's volume was misleading). Query pattern for "latest row per
  client": `select(MetricaCliente).distinct(MetricaCliente.cliente_id).order_by(cliente_id,
  inicio_janela.desc())` wrapped in `.subquery()`, then `aliased(MetricaCliente, subquery)` so the
  outer query can re-sort by client name — Postgres `DISTINCT ON` via SQLAlchemy's dialect-specific
  `.distinct(*cols)`. Reusable pattern for any future "latest per group" query on this schema.
- `GET /api/metricas/clientes/{cliente_id}` — full time series for one client.
- `GET /api/metricas/janelas` — scheduler run history (for monitoring, not client data).

This is what `frontend/`'s clients-overview page consumes — see
`branches/frontend-nextjs-prisma/facts/FCT-20260908-clientes-overview-page.md`.

**Reuse map** (nothing in `nextrouter-api` was duplicated, only one new function was added):

| Need | Function (in `backend/app/clients/nextrouter.py`) | Already used by |
|---|---|---|
| Discover active clients (sampled) | `scan_active_customer_ids` | `/api/clientes/atividade`, `/api/clientes/recorrencia` |
| Look up client names by id | `_buscar_clientes_por_id` (in `routers/clientes.py`, imported directly — see note below) | `/api/clientes/atividade`, `/api/clientes/recorrencia` |
| Exact ACD + answered totals | `get_cdr_aggregate` | `/api/acd`, `/api/asr?exato=true` |
| Exact failure records (for ASR + PDD) | `get_disconnection_full` | `/api/asr?exato=true`, `/api/pdd?exato=true` |
| **New**: exact ASR+ACD+PDD for one client/window in one call | `get_exact_metrics_for_client` (new) | only the scheduler job |

Note: the scheduler (`app/scheduler/jobs.py`) imports the private-by-convention
`_buscar_clientes_por_id` straight out of `app/routers/clientes.py` rather than relocating it into
the client layer. Deliberate, pragmatic call to avoid touching an already-verified production
route file for this change — flagged here in case a future refactor wants to move it into
`clients/nextrouter.py` where it arguably belongs.

## Verification

`alembic upgrade head` applied cleanly against a real Postgres 17 instance; a manual run of
`run_collection_window` for a real production window (2026-09-04, 16:00-17:00) stored exact,
plausible ASR/ACD/PDD for 70 real clients (e.g. cliente_id 256 = Setra, matching known reference
data from `CTX-FCT-20260904-route-inventory`'s verification note).
