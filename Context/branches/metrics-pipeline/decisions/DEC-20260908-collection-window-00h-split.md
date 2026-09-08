---
id: CTX-DEC-20260908-collection-window-00h-split
type: decision
title: Split the overnight window into two same-day windows (00:00-07:00 and 20:00-00:00)
branch: metrics-pipeline
tags: [scheduler, api-design, production-safety]
status: active
confidence: high
created_at: 2026-09-08
updated_at: 2026-09-08
source_ids: []
related: [CTX-FCT-20260904-cdr-api-behavior]
depends_on: []
supersedes: CTX-DEC-20260904-collection-window-schedule
superseded_by: null
---

# Decision

## Context

The original schedule (`CTX-DEC-20260904-collection-window-schedule`) had one 11-hour overnight
window `[20:00, 07:00 next day)`. The user asked instead for: `[00:00,07:00)` in the morning,
hourly `[07:00,08:00)` ... `[19:00,20:00)` during the day (unchanged), and `[20:00,00:00)` in the
evening — three distinct segments instead of two.

## Decision

- `APScheduler` `CronTrigger(hour="0,7-20", minute=0)` — now **15** fires/day (was 14): at 00:00,
  and every hour 07:00-20:00. Still fires at the *close* of the window being processed.
- `resolve_window(now)` in `backend/app/scheduler/jobs.py`:
  - `H == 0` → evening window of the day that just ended: `[yesterday 20:00, today 00:00)`
  - `H == 7` → morning window, same day: `[today 00:00, today 07:00)`
  - `H` in 8-20 → hourly, same as before: `[today (H-1):00, today H:00)`
- Every window is now within a **single calendar day**, except the 00:00 trigger's window, which
  still spans two dates (`date_ini`=yesterday, `date_end`=today) the same way the old overnight
  window did — same NextRouter edge-day quirk applies and was reverified: `time_ini=20:00` on the
  yesterday side (no `time_end`, so it runs to end-of-day) + `time_end=00:00` on the today side (an
  empty span, contributing nothing) = exactly `[20:00, 24:00)` of yesterday, nothing from today.
  Confirmed via `periodo_params` output directly, not just reasoning about it.
- `misfire_grace_time=300`, `max_instances=1`, `coalesce=True` unchanged.

## Rationale

Directly requested by the user. Splitting the old 11-hour window into a 7-hour morning piece and a
4-hour evening piece gives more temporal resolution for whatever reporting/alerting comes next,
and each window (bar the 00:00 edge case) is now trivially single-day, simplifying reasoning about
what data a window actually contains.

## Consequences

- `collection_windows`/`janelas_coleta` rows before this change used the old `[20:00,07:00)`
  boundary — a query spanning the 2026-09-04→2026-09-08 gap in stored data will see the old
  window shape, not the new one. Not a bug, just a fact to remember when reading historical rows.
- Same backfill/misfire caveat as the superseded decision: no backfill tool exists, a missed fire
  beyond the grace period silently skips that window.

## Related records

`CTX-FCT-20260904-cdr-api-behavior`, `CTX-DEC-20260904-collection-window-schedule` (superseded),
`branches/metrics-pipeline/_index.md`.
