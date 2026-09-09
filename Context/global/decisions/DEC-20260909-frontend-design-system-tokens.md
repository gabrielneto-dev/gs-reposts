---
id: CTX-DEC-20260909-frontend-design-system-tokens
type: decision
title: Frontend design system — light/amber/zinc tokens, applies to every page and tool
branch: global
tags: [frontend, design-system, ui, convention]
status: active
confidence: high
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: [CTX-DEC-20260909-multi-tool-navigation-architecture]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-09
valid_until: null
revisit_at: null
---

## Decision

The frontend has one consistent visual language, established organically across `/relatorios`,
`/gatilhos`, `/alertas`, `/janelas` and now formalized when the double sidebar
(`frontend/src/components/sidebar-dupla.tsx`) was restyled away from its initial dark
Pipedrive-style palette to match it. Every new page/tool should reuse these tokens rather than
inventing new ones:

- **Page background**: `bg-zinc-50`.
- **Cards/panels**: `rounded-3xl border border-black/5 bg-white p-6 shadow-sm shadow-black/[0.03]`
  (popovers/menus that float over content use `shadow-xl shadow-black/10` instead of the subtle
  shadow).
- **Brand eyebrow** (top of every page): `<p className="text-xs font-medium uppercase
  tracking-wide text-amber-600">GS VoIP</p>`.
- **Headings**: `text-zinc-900`. **Body text**: `text-zinc-600`. **Secondary/muted**:
  `text-zinc-500` / `text-zinc-400`.
- **Pill/nav buttons**: `rounded-full border border-black/5 bg-white ... hover:border-amber-300
  hover:text-amber-600`.
- **Active/selected state**: `bg-amber-50` background with `text-amber-600`/`text-amber-700` text
  (used for the sidebar's active tool/link, the date-range filter's in-range calendar cells, badge
  pills).
- **Segmented control "on" state** (e.g. the janelas Dia/Semana/Mês switcher): solid
  `bg-zinc-900 text-white`, not amber — amber is reserved for *navigation/selection* highlighting,
  not view-mode toggles.
- Borders throughout are `border-black/5`, never a solid gray — keeps everything visually light.

## Why

The double sidebar (`CTX-DEC-20260909-multi-tool-navigation-architecture`) was first built copying
Pipedrive's own dark rail+panel colors (`bg-zinc-950`/`bg-zinc-900`, `text-amber-400`,
`border-white/5`). The user's next message was explicit: "coloque no padrão de design do sistema /
cor, formato e etc" — the rest of the app is light-themed and every future "ferramenta" the user
adds needs to look consistent with it, not with whatever reference screenshot inspired the layout.

## Consequences

- Any new tool/page added to `FERRAMENTAS` (see the navigation-architecture decision) should be
  built with these tokens from the start — don't re-derive a palette from a design inspiration
  image without translating it to this system first.
- The "G" brand mark in the sidebar rail uses `rounded-full bg-amber-500 text-white` — a solid
  amber accent is fine for a one-off brand mark, but is not itself a token to reuse for buttons/state
  (those use `bg-amber-50`/`text-amber-600` instead, never solid amber backgrounds).
