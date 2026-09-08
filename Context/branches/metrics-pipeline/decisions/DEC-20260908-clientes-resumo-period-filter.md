---
id: CTX-DEC-20260908-clientes-resumo-period-filter
type: decision
title: "/api/metricas/clientes filters by an explicit inicio/fim datetime period, defaulting to today"
branch: metrics-pipeline
tags: [api-design, scheduler]
status: active
confidence: high
created_at: 2026-09-08
updated_at: 2026-09-08
source_ids: []
related: [CTX-FCT-20260904-schema-and-reused-functions]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-08
valid_until: null
revisit_at: null
---

# Decision

## Context

`GET /api/metricas/clientes` originally showed, per client, their **most recent ever** collected
window — no time filter at all. This surfaced as a real bug report from the user: clients with no
calls since 2026-09-04 kept showing up in the "today" table with `volume_dia = 0` and a stale
`fim_janela`, indistinguishable at a glance from clients genuinely active today. The fix went
through three shapes in one session before landing: a single `data` (day) filter, then a
`data_inicio`/`data_fim` (day range) filter, then the final `inicio`/`fim` (full datetime) filter
— because the user then asked to be able to pick the hour on each side too, and to page through
periods with "próxima/anterior" buttons that shift by the period's own duration (e.g.
12:00-13:00 → 13:00-14:00; 00:00-07:00 → 07:00-14:00).

## Decision

- Query params `inicio`/`fim` (`datetime`, both optional). Neither given → default is **today
  in full** (`[start of today, start of tomorrow)`, timezone `settings.scheduler_timezone`).
  A naive datetime (no offset, e.g. what `<input type="datetime-local">` sends) is assumed to
  already be in that timezone — see `_com_timezone()` in `backend/app/routers/metricas.py`.
- Both the "latest window per client" subquery and the `volume_periodo` aggregate (renamed from
  `volume_dia`) are scoped to `fim_janela >= inicio AND fim_janela < fim` — a client with zero
  activity in the filtered period simply doesn't appear in the response at all, instead of
  appearing with old data.
- `400` if `inicio >= fim` (via `HTTPException`).
- Response echoes back the resolved `inicio`/`fim` (not just `registros`/`clientes`) so the
  frontend always knows exactly what period was applied, including when it didn't specify one.

## Rationale

An explicit, always-bounded period read is the only way to make "who's active in this period" look
right when clients have irregular activity — there is no such thing as a period-less "current
state" for this data model (a client's last known window can be arbitrarily old). Defaulting to
today keeps the common case (open the page, see today) working with no query params, matching the
pre-existing UX.

## Consequences

- Breaking API change from the pre-2026-09-08 shape (no `data`/`volume_dia` fields survive) — only
  `frontend/`'s clients-overview page consumes this endpoint today, and it was updated in the same
  commit, so no external consumer is affected.
- `historico_cliente` and `listar_janelas` (same file) were **not** touched — they still take
  `data_inicio`/`data_fim` as plain `date` (whole-day granularity), which is the right grain for
  their use cases (a client's full history, the scheduler's run log). Don't try to unify the three
  endpoints' filter shapes; they solve different problems.

## Related records

`CTX-FCT-20260904-schema-and-reused-functions`,
`branches/frontend-nextjs-prisma/facts/FCT-20260908-clientes-overview-page.md` (the calendar UI
built on top of this), `branches/metrics-pipeline/_index.md`.
