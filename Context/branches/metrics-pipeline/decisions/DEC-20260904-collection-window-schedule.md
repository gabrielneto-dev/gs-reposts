---
id: CTX-DEC-20260904-collection-window-schedule
type: decision
title: Collection windows are hourly 07:00-20:00 plus one overnight window 20:00-07:00
branch: metrics-pipeline
tags: [scheduler, api-design, production-safety]
status: active
confidence: high
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-FCT-20260904-cdr-api-behavior]
depends_on: []
supersedes: null
superseded_by: null
---

# Decision

## Context

The user specified the collection cadence directly: from 20:00 to 07:00 the next day, collect as
**one** window; from 07:00 to 20:00, collect **one window per hour**
(`[07:00,08:00)`, `[08:00,09:00)`, ..., `[19:00,20:00)`).

## Decision

- `APScheduler` `CronTrigger(hour="7-20", minute=0)` — 14 fires/day, always on the hour, always at
  the *close* of the window being processed (fire at 08:00 processes `[07:00,08:00)`, fire at 20:00
  processes `[19:00,20:00)`).
- `resolve_window(now)` in `backend/app/scheduler/jobs.py` maps "fired at hour H" to the window:
  - `H == 7` → overnight window `[yesterday 20:00, today 07:00)`
  - otherwise → `[today (H-1):00, today H:00)`
- The overnight window spans two calendar dates for the softswitch API call
  (`date_ini`=yesterday, `date_end`=today, `time_ini`=20:00, `time_end`=07:00). This happens to
  line up exactly with the documented NextRouter quirk in `CTX-FCT-20260904-cdr-api-behavior`
  (point 2): `time_ini`/`time_end` only bind the *edge* days of a multi-day range, not every day in
  between — since there are no days in between here (just the two edges), no special-casing was
  needed. This would NOT work for a 3+ day window.
- `max_instances=1`, `coalesce=True`, `misfire_grace_time=300` on the job — prevents overlapping
  runs and tolerates a restart within 5 minutes of a scheduled fire without losing that window.
- `SCHEDULER_ENABLED=false` (env) fully disables the job — used to run the API locally without
  hitting production on a timer.

## Rationale

Directly matches the user's stated requirement. The "fire at close of window" convention (rather
than "fire at start") was chosen because the data for an hour only exists once that hour is over.

## Consequences

- If the process is down across a scheduled fire time by more than `misfire_grace_time` (5 min),
  that window is silently skipped — there's no backfill mechanism yet. Worth building if missed
  windows turn out to matter in practice.
- Changing the window boundaries (e.g. different day/night split) means changing both the
  `CronTrigger` hours and `resolve_window`'s branching — they must stay in sync, there's no single
  source of truth for "which hours are overnight vs hourly."

## Related records

`CTX-FCT-20260904-cdr-api-behavior`, `branches/metrics-pipeline/_index.md`.
