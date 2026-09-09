---
id: CTX-DEC-20260909-severidade-visto-delivery
type: decision
title: Alert severity ranking, seen/unseen tracking, and delivery channels
branch: gatilhos-alertas
tags: [gatilhos, alertas, severidade, ux, notifications]
status: active
confidence: high
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: [CTX-DEC-20260909-gatilhos-rule-model, CTX-DEC-20260909-frontend-design-system-tokens]
depends_on: [CTX-DEC-20260909-gatilhos-rule-model]
supersedes: null
superseded_by: null
valid_from: 2026-09-08
valid_until: null
revisit_at: null
---

## Decision

**Severity**: each `gatilho` has a `severidade` (`SeveridadeGatilho` enum: `atencao` < `medio` <
`critico` < `urgente`, with a `SEVERIDADE_ORDEM` dict for ranking). Every fired
`alertas_disparados` row **copies** the gatilho's severidade at fire time (doesn't follow live
edits to the rule) so history keeps reflecting what was actually severe at that moment. Alert
history (`GET /api/alertas`) is ordered by severity desc, then `disparado_em` desc. The client-table
badge dot shows the color of the client's **highest-severity unseen** alert.

**Seen/unseen ("visto")**: `alertas_disparados` has `visto` (bool) + `visto_em` (nullable
timestamp, set only when marked seen — shown in the UI alongside `disparado_em`). Per-alert
(`POST /api/alertas/{id}/marcar-visto`) and bulk, optionally scoped to one client
(`POST /api/alertas/marcar-todos-vistos?cliente_id=`) mark-as-seen actions. The client-table badge
counts **all** unseen alerts regardless of age — deliberately **no 24h cutoff** (an initial simpler
design used a time window; the user wanted it to just track seen/unseen state instead).

**Delivery — three channels, not one**: (1) the badge dot on the clients table
(`/relatorios`), (2) a dedicated alert history page (`/alertas`), (3) an external webhook
(`FRONTEND_ALERTAS_WEBHOOK_URL`, separate from the metrics-refresh webhook) that also drives (4) a
native browser `Notification` fired client-side in `frontend/src/components/live-refresher.tsx`
when a live alert event arrives over the existing SSE channel.

## Why

User's own words: "Eu preciso ser capaz de ranquear esse tipo de alerta, por exemplo alerta
vermelho, alerta amarelo, alerta ferrada" → landed on 4 levels via `AskUserQuestion`. Seen/unseen
was requested after reviewing the alert list ("eu preciso saber a hora que eu marquei como visto
também" — twice) — the timestamp requirement is why `visto_em` exists as its own column rather than
inferring it from an audit log. The browser notification was a lightweight explicit ask ("Seria
interessante também lançar uma notificação no próprio navegador") layered on top of the
already-working SSE pipeline from `metrics-pipeline`.

## Consequences

- Any code reading severity for display should use `SEVERIDADE_ORDEM` for sorting, never string
  comparison — enum member order isn't guaranteed to match visual severity order.
- The unseen-badge query does a **Python-side reduction** (`alertas_nao_vistos` in
  `app/routers/alertas.py`) to find, per client, the max severity + latest timestamp among unseen
  alerts — not a single SQL aggregate — worth knowing before "optimizing" it into a query that
  might get the max-severity-vs-latest-timestamp pairing subtly wrong.
- Frontend color/label maps live in `frontend/src/lib/severidade.ts`
  (`SEVERIDADE_LABEL`/`PILULA`/`PONTO`) — the single place to add a 5th level later.
