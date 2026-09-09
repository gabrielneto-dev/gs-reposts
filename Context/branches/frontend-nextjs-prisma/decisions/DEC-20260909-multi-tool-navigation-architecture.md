---
id: CTX-DEC-20260909-multi-tool-navigation-architecture
type: decision
title: Double sidebar (icon rail + grouped panel), data-driven by a FERRAMENTAS array
branch: frontend-nextjs-prisma
tags: [frontend, navigation, information-architecture]
status: active
confidence: high
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: [CTX-DEC-20260909-frontend-design-system-tokens]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-09
valid_until: null
revisit_at: null
---

## Decision

Replaced the original single horizontal top nav (`frontend/src/components/nav-bar.tsx`, deleted)
with a Pipedrive-style **double sidebar**: a narrow icon rail (one icon per "ferramenta"/tool) plus
a wider panel showing that tool's sections/pages, both in
`frontend/src/components/sidebar-dupla.tsx`.

The navigation model is fully data-driven from `frontend/src/lib/navegacao.tsx`'s `FERRAMENTAS`
array — each entry is `{ id, label, Icone, secoes: [{ titulo?, itens: [{ href, label }] }] }`.
Today there is exactly one tool ("Monitoramento de Clientes", covering ASR/PDD/ACD monitoring: the
`/relatorios`, `/gatilhos`, `/alertas`, `/janelas` pages, grouped into "Alertas" and "Coleta"
sections). Adding a future tool is meant to be **only a new array entry** — the rail and panel
adapt automatically, no changes needed to `sidebar-dupla.tsx` itself.

`ferramentaDoCaminho(pathname)` finds which tool owns the current route (by scanning all
tools' `secoes`/`itens` for a matching `href`) so the rail highlights the right icon and the panel
shows the right section list even on a page reached by direct URL, not just by clicking through the
nav.

## Why

User's own words, verbatim, after being shown a Pipedrive screenshot: "Então, eu preciso que seja
de uma forma bem construída. Queria que fosse separado por ferramenta pois vou colocar mais
ferramentas aqui então quero uma ferramenta de monitoramento de clientes e aqui vou ter
monitoramento de ASR, PDD e ACD junto e assim vou ir construindo ferramenta por ferramenta." — an
explicit statement that this is a multi-tool platform in the making, so the nav needed to scale by
construction, not just look like Pipedrive's.

The sidebar was first built with Pipedrive's own dark color palette, then immediately restyled to
the app's actual light design system on the very next message — see
`Context/global/decisions/DEC-20260909-frontend-design-system-tokens.md` for the concrete tokens
used instead.

## Consequences

- Adding tool #2 means adding one `Ferramenta` entry to `FERRAMENTAS` with its own `secoes`/`itens`
  and a new icon component (follow the pattern of `IconeMonitoramento`: a small inline `<svg>`
  function, not an icon library dependency — none is installed).
- The rail icon for a tool links to `ferramenta.secoes[0].itens[0].href` (its first page) — a tool
  with an empty `secoes[0].itens` would break this; every tool needs at least one item in its first
  section.
- `frontend/src/lib/navegacao.tsx` must stay a `.tsx` file (not `.ts`) since it defines JSX
  (`IconeMonitoramento`'s `<svg>`) — this was gotten wrong once and had to be renamed.
