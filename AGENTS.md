# AGENTS.md

Operational contract for AI agents working in this project.

<!-- CONTEXT-ENGINEERING:START -->

# Project Context System

This project uses `Context/` as its persistent project memory and knowledge system.

## Context discovery

For every non-trivial task:

1. Read `Context/MAP.md`.
2. Read `Context/STATE.md`.
3. Determine which context branches are relevant.
4. Read only the corresponding branch `_index.md` files.
5. Retrieve atomic records only when required.
6. Follow `related`, `depends_on`, `source_ids`, `supersedes`, and `superseded_by` only when they materially affect the current task.
7. Do not recursively load the entire `Context/` directory.

Use progressive context loading: MAP + STATE → relevant branch index → specific atomic records → relations → sources (only if needed).

## Sources of truth

- `AGENTS.md` — permanent operational instructions.
- `Context/MAP.md` — context routing and navigation.
- `Context/STATE.md` — current project state.
- `Context/core/**` — stable project fundamentals.
- `Context/branches/**` — domain-specific knowledge.
- `Context/global/**` — cross-cutting decisions, questions, assumptions, risks and plans.
- `Context/checkpoints/**` — distilled session/milestone checkpoints.
- `Context/sources/**` — provenance and evidence.
- `Context/_meta/**` — context configuration, taxonomy, catalog and maintenance metadata.

## Context write policy

Context reading is automatic for non-trivial work.

Context persistence is controlled. Do not write documentation for every conversation message.

Run the Context Save Protocol (see `Context/README.md`) when the user expresses an intent equivalent to:

- "salvar contexto" / "salve o contexto" / "save context"
- "persistir contexto" / "atualizar contexto" / "atualizar memória do projeto"
- "criar checkpoint" / "checkpoint da sessão"

Do not copy the conversation verbatim. Persist distilled, durable knowledge only.

## Safety

Never persist secrets, passwords, access tokens, API keys, private keys, session cookies or credential values inside `Context/`. References to environment-variable names or secret-manager locations are allowed.

## Maintenance

If a durable, project-wide operating rule is discovered, evaluate whether it belongs in `AGENTS.md`. Do not put transient state or detailed knowledge in `AGENTS.md`.

## Project status

This project was bootstrapped while the working directory was empty. There is no code, README, or prior documentation yet. See `Context/global/questions/QUE-20260903-project-purpose.md` for the open question about what this project actually is, and `Context/STATE.md` for current status.

<!-- CONTEXT-ENGINEERING:END -->
