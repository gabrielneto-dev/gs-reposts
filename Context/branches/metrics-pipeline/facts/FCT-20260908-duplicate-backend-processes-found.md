---
id: CTX-FCT-20260908-duplicate-backend-processes-found
type: fact
title: Two live backend/scheduler process trees were found running at once; cleaned up during live verification
branch: metrics-pipeline
tags: [scheduler, windows, production-safety]
status: active
confidence: verified
created_at: 2026-09-08
updated_at: 2026-09-08
source_ids: []
related: [CTX-DEC-20260908-frontend-webhook-notification, CTX-CP-20260908-1700-live-verification-and-process-cleanup]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-08
valid_until: null
revisit_at: null
---

## Fact

While doing live end-to-end verification of the collection pipeline (2026-09-08), found **two
separate `uvicorn app.main:app --reload` process trees** alive at the same time on the dev
machine — meaning two independent scheduler instances, each on their own 15x/day cron, both
capable of firing collection windows against the real production softswitch. Likely cause:
`start-dev.ps1` was run more than once across sessions without checking whether an earlier
backend window was already open.

**Process tree shape discovered** (relevant for anyone debugging "why does `Get-CimInstance
Win32_Process` show a `python.exe` outside the venv"): `uvicorn --reload`'s own supervisor process
(the one launched from `.venv\Scripts\python.exe`) spawns its actual worker — the process that
really binds the port and runs the app — via **the global Python install**
(`AppData\Local\Programs\Python\Python312\python.exe`), not the venv interpreter, even though the
venv has all the right packages. This is a Windows-specific `uvicorn`/`multiprocessing` quirk in
this environment, not a broken venv or wrong PATH — reproduced identically on a clean restart.
Use `Get-NetTCPConnection -LocalPort 8000 -State Listen | Select OwningProcess` to find which PID
in the tree is *actually* serving, not just which one has the recognizable venv command line.

**Consequence realized**: no data corruption (Postgres' unique constraint on
`metricas_cliente(cliente_id, inicio_janela, fim_janela)` would just fail the second insert for
any window both instances tried to collect), but duplicate load against production and duplicate
webhook attempts (one succeeding, one likely also succeeding — the frontend has no dedup on double
notifications since `router.refresh()` is idempotent, so this was survivable, just wasteful).

**Cleanup done**: killed the entire stale tree (all 4 PIDs: reloader, worker, worker's own
multiprocessing spawn child, and the hosting PowerShell window), then started one fresh instance
the same way `start-dev.ps1` does. Confirmed via `Get-NetTCPConnection` that exactly one process
owns port 8000 afterward.

## Verification

`Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*uvicorn*app.main*' }` showed
2 full trees before cleanup, 1 after. `Get-NetTCPConnection -LocalPort 8000` showed exactly one
owning PID after restart. `/health` and `/api/metricas/clientes` both responded correctly from the
single surviving instance.
