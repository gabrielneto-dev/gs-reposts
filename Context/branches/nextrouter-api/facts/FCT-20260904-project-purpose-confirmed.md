---
id: CTX-FCT-20260904-project-purpose-confirmed
type: fact
title: relatorios is a FastAPI reporting API for a VoIP telephony company (GS VoIP), fronting the NextRouter softswitch
branch: nextrouter-api
tags: [project-scope, fastapi, nextrouter, softswitch, telephony]
status: active
confidence: verified
created_at: 2026-09-04
updated_at: 2026-09-04
source_ids: []
related: [CTX-QUE-20260903-project-purpose, CTX-ASM-20260903-project-domain-reports]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-04
valid_until: null
revisit_at: null
---

## Fact

The `relatorios` project is a Python/FastAPI backend service for a VoIP telephony company
(GS VoIP, softswitch at `sip5.gsvoip.com.br`) that runs NextBilling IP Solutions' **NextRouter
C4 SoftSwitch**. The API's job is to expose telephony quality/volume metrics — ASR (Answer
Seizure Ratio), ACD (Average Call Duration), PDD (Post Dial Delay) — and client lookups, by
querying the NextRouter's own REST API server-side and re-shaping the results into clean,
purpose-built endpoints for internal consumption (dashboards, periodic jobs, ad-hoc analysis via
tools like Bruno/Postman).

This resolves `CTX-QUE-20260903-project-purpose` (closed as answered) and confirms
`CTX-ASM-20260903-project-domain-reports` was directionally correct (superseded by this fact —
"relatorios" does mean reports, specifically telephony call-quality reports).

## How this was established

User request in-session: "Preciso de uma rota que traga pra mim a analise do ASR por periodo e
por cliente" for a telephony company using softswitches, pointing at the company's NextBilling
Confluence space as documentation.

## Consequence

`Context/core/overview.md`, `goals.md`, `constraints.md`, `glossary.md` are now populated for
real (see those files) instead of carrying bootstrap placeholders.
