---
id: CTX-DEC-20260909-backfill-scope-yesterday-only
type: decision
title: Historical backfill actually run for "yesterday" only, not 30 days
branch: metrics-pipeline
tags: [scheduler, backfill, gatilhos]
status: active
confidence: high
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: [CTX-DEC-20260909-manual-window-trigger]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-09
valid_until: null
revisit_at: null
---

## Decision

`backend/scripts/backfill_historico.py` was built to backfill up to N days of history (`--dias`,
default 30, or `--dia` for one specific date) against real production data, so gatilho reference
periods (media_semanal/media_mensal) would have enough history to compare against. **The user only
actually ran it for yesterday** ("vamos fazer o seguinte, pegue apenas o dia de ontem" →
"esqueça esses 30 dias") — the script itself keeps its general `--dias`/`--dia` flags (no code was
removed), it just was never run at the larger scope in practice.

## Why

Mid-task course correction from the user — a full 30-day backfill against real production is a lot
of NextRouter API volume (`--pausa` between windows exists specifically to soften this), and the
user decided it wasn't worth doing at that scope right now.

## Consequences

- Don't assume 30 days of historical `metricas_cliente` data exists — as of this checkpoint, real
  history only goes back to whenever the scheduler organically started running, plus one backfilled
  day (yesterday relative to 2026-09-09).
- If the user later asks for a fuller backfill, the script already supports it (`--dias N`) — no
  new code needed, just confirm before running it given the production-volume caution above.
