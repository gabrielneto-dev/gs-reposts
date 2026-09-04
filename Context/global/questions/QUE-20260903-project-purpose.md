---
id: CTX-QUE-20260903-project-purpose
type: question
title: What is this project actually for?
branch: global
tags: [project-scope, bootstrap]
status: answered
created_at: 2026-09-03
updated_at: 2026-09-04
related: [CTX-ASM-20260903-project-domain-reports, CTX-FCT-20260904-project-purpose-confirmed]
---

## Answer (2026-09-04)

Resolved by direct user request in-session. See
`Context/branches/nextrouter-api/facts/FCT-20260904-project-purpose-confirmed.md` for the full
answer: a FastAPI reporting API for a VoIP telephony company (GS VoIP) fronting their NextRouter
C4 SoftSwitch, exposing ASR/ACD/PDD metrics and client lookups.

## Question

What is the `relatorios` project meant to build or do? Who is it for, what kind of "reports" (if any) are involved, what technology stack/language is expected, and what's the current scope?

## Why this matters

The working directory was completely empty at bootstrap time (no code, README, or config). Every other context file (`core/overview.md`, `core/goals.md`, `core/constraints.md`, `MAP.md` branches) depends on this answer and currently carries only placeholders/assumptions.

## What depends on the answer

- `Context/core/overview.md`, `goals.md`, `constraints.md`, `glossary.md`
- Which branches get created under `Context/branches/`
- Whether `CTX-ASM-20260903-project-domain-reports` becomes a fact or gets discarded

## Known options

None yet — no options have been discussed.

## How to resolve

Ask the user, or infer from the first real work (code, files, requirements) once it appears in the project.
