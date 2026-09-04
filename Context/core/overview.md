# Project Overview

**Status: confirmed** (2026-09-04). See `CTX-FCT-20260904-project-purpose-confirmed`.

`relatorios` is a Python/FastAPI backend service for a VoIP telephony company (GS VoIP) that
fronts their **NextRouter C4 SoftSwitch** (NextBilling IP Solutions), hosted at
`sip5.gsvoip.com.br`. It exposes clean, purpose-built read-only HTTP endpoints for:

- **ASR** (Answer Seizure Ratio) — overall and broken down by SIP result code
- **ACD** (Average Call Duration)
- **PDD** (Post Dial Delay)
- **Client lookups** — raw listing, fuzzy name search, and activity/recurrence detection

...by querying the NextRouter's own REST API server-side (which has no ready-made aggregates for
most of this — see `Context/branches/nextrouter-api/facts/FCT-20260904-cdr-api-behavior.md`) and
computing the metrics itself.

See `Context/branches/nextrouter-api/_index.md` for the full technical picture, and
`docs/API.md` (project root) for the consumer-facing route documentation.

## Where things live

- App code: `app/` (`config.py`, `clients/nextrouter.py`, `routers/`, `schemas/`, `utils/`)
- Route docs for API consumers: `docs/API.md`
- Softswitch credentials: `.env` (never committed; see `Context/core/constraints.md`)
- Run with: `uvicorn app.main:app --reload`
