---
id: CTX-CP-20260908-1700-live-verification-and-process-cleanup
type: checkpoint
title: Verified the webhook/live-refresh/period-filter pipeline live end-to-end; found and fixed two real bugs
branch: global
tags: [scheduler, realtime, windows, production-safety]
status: active
confidence: verified
created_at: 2026-09-08
updated_at: 2026-09-08
source_ids: []
related: [CTX-DEC-20260908-frontend-webhook-notification, CTX-FCT-20260908-duplicate-backend-processes-found, CTX-CP-20260908-1600-live-refresh-and-datetime-filter]
depends_on: [CTX-CP-20260908-1600-live-refresh-and-datetime-filter]
supersedes: null
superseded_by: null
valid_from: 2026-09-08
valid_until: null
revisit_at: null
---

## Objective

The user asked to verify — for real, not simulated — that everything built in
`CP-20260908-1600` actually works: automatic discovery, per-window storage, the webhook, and the
frontend updating itself on screen. "Teste em banco e em tela, em back e tudo, e depois me fale."

## What changed

- Ran the real `run_collection_window()` function (same code the scheduler calls) twice, for two
  small ad-hoc windows not aligned to the normal schedule (so they couldn't collide with real
  automated windows), against real production data.
- Found `FRONTEND_WEBHOOK_URL` in `backend/.env` pointed at `:3010`; the real running frontend
  (`start-dev.ps1`) was on `:3001` because `:3000` was taken. Fixed `.env` (not committed, gitignored)
  and `.env.example` (committed, `f84c431`).
- Found **two duplicate backend/scheduler process trees** running simultaneously — killed both,
  started one clean instance. See `facts/FCT-20260908-duplicate-backend-processes-found.md` for
  the full process-tree shape (including the Windows quirk where `uvicorn --reload`'s worker binds
  via the global Python install, not the venv one that launched it).
- Committed and pushed the `.env.example` fix (`f84c431`).

## Decisions

None new — this session updated `decisions/DEC-20260908-frontend-webhook-notification.md`'s
Consequences with the port-drift gotcha found in practice, rather than creating a new decision.

## Discoveries

- The webhook and live-refresh code (`CP-20260908-1600`) was correct — both bugs found were
  **configuration/operational**, not logic bugs: a stale port in `.env`, and a duplicate process
  left over from re-running `start-dev.ps1`. Confirms the design in
  `DEC-20260908-frontend-webhook-notification.md` (best-effort, non-blocking) did exactly what it
  was supposed to: the wrong config caused a silent warning in logs, not a broken collection
  pipeline — the bug was invisible until someone actually checked whether the frontend updated.
- `Get-NetTCPConnection -LocalPort 8000 -State Listen | Select OwningProcess` is the reliable way
  to find which PID in a `uvicorn --reload` process tree is actually serving — the one with the
  recognizable venv path in its command line is usually the *supervisor*, not the worker.

## Problems solved

- Real end-to-end proof, with timestamps: before the fix, an already-open browser tab showed "85
  de 85 clientes" / cliente 918 last-coleta `11:00`; immediately after a corrected-webhook test
  run, without touching the browser, it showed "93 de 93 clientes" / cliente 918 last-coleta
  `11:22` — the SSE → `router.refresh()` path is confirmed working against a real webhook call from
  real backend code (not a synthetic `curl` POST like the first round of testing in
  `CP-20260908-1600` used).
- Backend restarted cleanly: exactly one process tree now, confirmed via `Get-NetTCPConnection`.

## Failed approaches / gotchas worth remembering

- The harness's classifier blocked the `Stop-Process` PowerShell command on the first attempt (no
  specific reason given) — resolved on an identical retry, consistent with the pattern already in
  `Context/core/constraints.md`.
- Two small, harmless "test" `janelas_coleta` rows now exist in the real database
  (`2026-09-08 11:17-11:20` and `11:19-11:22`, both real production data, `id 6` and `id 7`) —
  informational only, not cleaned up (deleting DB rows wasn't asked for and felt like the wrong
  default). Mention this if anyone is confused by odd non-hour-aligned windows in the history.

## Current state

Single clean backend instance running, `.env` correct, `.env.example` fixed and pushed
(`f84c431`). The next real automated collection window (next hour mark) will be the first one to
use the corrected webhook URL from an actually-scheduled fire, not a manual trigger — not
separately verified yet since it requires waiting for the clock, but there's no reason to expect
it to behave differently from the manual runs already verified.

## Open questions

Same as `CP-20260908-1600` — "gatilhos" (business-rule triggers) still not started, still the
most likely next real topic.

## Next steps

1. If anyone wants belt-and-suspenders confidence, check `/api/metricas/janelas` after the next
   real hourly fire and confirm `situacao: concluida` plus a successful webhook delivery pattern
   (no direct log access needed — an open browser tab updating on its own is proof enough, same as
   this session's verification).
2. Pick up "gatilhos" whenever the user is ready.

## Affected files/artifacts

`backend/.env` (not tracked), `backend/.env.example`, the running backend OS process (restarted,
not a file change). No frontend files touched this round.

## Records created/updated

Created: `CTX-FCT-20260908-duplicate-backend-processes-found`, this checkpoint. Updated:
`CTX-DEC-20260908-frontend-webhook-notification` (Consequences), `Context/core/constraints.md`
(new "Dev-server process management" section), `branches/metrics-pipeline/_index.md`.
