# Context/ — Project Memory System

This directory is the persistent, file-based memory of the **relatorios** project. It exists so that any AI agent — in any future session, with zero conversational memory — can recover what the project is, what it knows, what it has decided, and where it left off, without re-deriving everything from scratch.

`AGENTS.md` (project root) defines *how* agents should work. This file defines *how the memory itself works*.

## 1. Purpose

- Preserve facts, decisions, research, assumptions, questions, plans, risks, experiments and failures across sessions.
- Let an agent load only the context relevant to the task at hand (progressive loading), not the whole memory.
- Keep a clear line between "we know this," "we assume this," "we're asking this," and "we decided this."

## 2. Directory structure

```
Context/
├── README.md          # this file
├── MAP.md              # routing: question/topic -> branch -> index -> record
├── STATE.md            # current state of the project (not history)
├── _meta/
│   ├── config.yaml      # context engineering configuration
│   ├── taxonomy.yaml    # canonical tags, statuses, confidence levels
│   ├── catalog.jsonl    # derived index of all atomic records (one JSON per line)
│   ├── changelog.md     # structural changes to the memory system itself
│   └── templates/       # templates for new records
├── core/
│   ├── overview.md      # what the project is
│   ├── goals.md         # goals / non-goals / success criteria
│   ├── constraints.md   # durable constraints
│   └── glossary.md      # domain terms
├── branches/            # domain-specific knowledge (created as domains emerge)
│   └── <branch>/
│       ├── _index.md
│       ├── facts/
│       ├── research/
│       ├── decisions/
│       ├── assumptions/
│       ├── questions/
│       ├── plans/
│       ├── risks/
│       ├── experiments/
│       └── notes/
├── global/              # cross-cutting records not owned by a single branch
│   ├── decisions/
│   ├── assumptions/
│   ├── questions/
│   ├── plans/
│   └── risks/
├── checkpoints/         # session/milestone checkpoints
├── sources/             # provenance / evidence (created when first needed)
├── future/              # unapproved ideas, candidate features, revisit-later items
└── archive/             # superseded/deprecated material kept for history
```

Empty directories are created only when they have content — they are omitted otherwise for clarity, and created on demand.

## 3. Record types

| Prefix | Type | Meaning |
|---|---|---|
| FCT | fact | Something considered true in the current scope |
| RES | research | An investigation and its findings |
| DEC | decision | A choice that was made, with rationale |
| ASM | assumption | A hypothesis used to keep moving without full confirmation |
| QUE | question | An open question, first-class until answered |
| PLN | plan | A candidate/planned/in-progress/completed body of work |
| RSK | risk | A known risk with impact/likelihood/mitigation |
| NTE | note | Miscellaneous durable note that doesn't fit other types |
| SRC | source | Provenance / external evidence |
| EXP | experiment | A hypothesis-driven test and its result |
| CP | checkpoint | A session/milestone snapshot |

Never conflate these. A hypothesis is not a fact. A research finding is not a decision. A future idea is not an approved plan.

## 4. Metadata schema

Every atomic record uses YAML frontmatter:

```yaml
---
id: CTX-DEC-20260903-example-slug
type: decision
title: Human-readable title
branch: <branch-name-or-global>
tags: [tag-one, tag-two]
status: active
confidence: medium
created_at: 2026-09-03
updated_at: 2026-09-03
source_ids: []
related: []
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-03
valid_until: null
revisit_at: null
---
```

Minimum required: `id, type, title, branch, tags, status, created_at, updated_at`. Others are used when meaningful.

## 5. Naming

Files: `<TYPE>-<YYYYMMDD>-<kebab-case-slug>.md` (e.g. `DEC-20260903-use-postgresql.md`).
IDs: `CTX-<TYPE>-<YYYYMMDD>-<slug>`, stable even if the file is later moved.
Tags: `kebab-case`, normalized in `_meta/taxonomy.yaml` — reuse an existing tag before inventing a new one.

## 6. Retrieval protocol

1. **Understand the request** — objective, entities, likely branch(es)/tags, temporality.
2. **Load L0** — `MAP.md` + `STATE.md` only.
3. **Select branches** — read only the relevant `branches/<branch>/_index.md`.
4. **Targeted retrieval** — search by id/title/tags/type/status/keywords (e.g. `rg "type: decision" Context/`, `rg "status: open" Context/`).
5. **Expand via relations** — follow `related`/`depends_on`/`source_ids`/supersession one hop at a time; only go deeper if the task requires it.
6. Never treat `superseded`/`deprecated`/`archived` records as current state without checking their successor.

## 7. Persistence — "Context Save Protocol"

Reading context is automatic. **Writing is controlled.** Run this protocol only when the user's intent is equivalent to "salvar contexto" / "save context" / "criar checkpoint" / "atualizar memória do projeto" (recognize the intent, not an exact string).

Pipeline:

```
INSPECT PROJECT CHANGES → ANALYZE → DISTILL → CLASSIFY → DEDUPLICATE → RELATE
→ UPDATE/CREATE ATOMIC RECORDS → CREATE CHECKPOINT → UPDATE STATE
→ UPDATE BRANCH INDEXES → UPDATE MAP IF NEEDED → UPDATE CATALOG
→ UPDATE CONTEXT CHANGELOG IF NEEDED → EVALUATE AGENTS.md RULES → VALIDATE
```

Distill, don't transcribe: capture causes, decisions, validated solutions, failed approaches worth avoiding, new facts/assumptions/questions/risks, and next steps — not a transcript of the conversation. Before creating a record, search for an existing equivalent (id/title/tags/branch) and update it instead of duplicating; if the information genuinely changed, mark the old record `superseded` and link `supersedes`/`superseded_by`.

Filter for every candidate item: *"Would an agent in a brand-new session need this to continue the work, avoid repeating a mistake, or make a better decision?"* If no, discard it.

Checkpoints live in `checkpoints/CP-YYYYMMDD-HHMM-<slug>.md` (id `CTX-CP-YYYYMMDD-HHMM-<slug>`) and capture: objective, what changed, decisions, discoveries, problems solved, failed approaches worth remembering, current state, open questions, next steps, affected files/artifacts, and records created/updated. After a checkpoint, `STATE.md` is rewritten to reflect the present and points at the latest checkpoint.

During save, check whether a durable *operating rule* (not project knowledge) surfaced — if so, consider adding it to `AGENTS.md`'s managed block rather than to `Context/`.

## 8. Semantic commands

- **salvar contexto** — run the full Context Save Protocol above.
- **carregar contexto** — force re-reading `MAP.md`, `STATE.md`, and relevant branches before continuing.
- **buscar contexto `<assunto>`** — search the memory by tag/title/content/id/relations, most relevant first.
- **status do contexto** — summarize current state, latest checkpoint, branches, critical open questions, blockers.
- **auditar contexto** — run the maintenance audit (section 10).

## 9. Supersession and conflicts

Never silently delete superseded knowledge. Mark the old record `status: superseded` + `superseded_by: <new-id>`; the new record gets `supersedes: <old-id>`. Move material with no remaining active value to `archive/`, keeping it for history.

When two records conflict, do not pick one silently — compare date, status, scope, origin, confidence, and temporal validity; if still ambiguous, create/update a `question` record documenting the conflict.

## 10. Maintenance / audit

Periodically (or when asked to "auditar contexto"), check for: duplicate IDs, dangling relation references, duplicate/synonymous tags, contradictory records, stale statuses (e.g. an answered question still `open`, a superseded record shown as `active`), broken links, oversized branches/records, unclassified records, missing provenance where it matters, a stale `MAP.md`, an over-historical `STATE.md`, a `catalog.jsonl` that has drifted from the canonical `.md` files (rebuild it from the records, which are always canonical), duplicated rules between `AGENTS.md`/`CLAUDE.md`, and any accidentally persisted secret.

## 11. Security

Never persist actual secret values (passwords, API keys, tokens, cookies, private keys, recovery codes). Referencing an environment-variable *name* or secret-manager *location* is fine.

## 12. Adding a branch

Create `Context/branches/<name>/_index.md` only when a real, relatively independent knowledge domain emerges for this project (e.g. once actual code/features exist). Don't create branches to fill out the structure. Each branch index states: purpose, scope, current state, core concepts, key records, active decisions, open questions, risks, relations to other branches.
