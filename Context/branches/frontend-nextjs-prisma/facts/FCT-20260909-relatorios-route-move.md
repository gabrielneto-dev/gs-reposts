---
id: CTX-FCT-20260909-relatorios-route-move
type: fact
title: Clients-overview page moved from "/" to "/relatorios"
branch: frontend-nextjs-prisma
tags: [frontend, routing]
status: active
confidence: high
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: []
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-09
valid_until: null
revisit_at: null
---

## What

The clients-overview table page (formerly `frontend/src/app/page.tsx`, `PageProps<"/">`) now lives
at `frontend/src/app/relatorios/page.tsx` (`PageProps<"/relatorios">`). The old root path `"/"` is
now a small redirect-only page (`redirect("/relatorios")` from `next/navigation`), so any stray
link/bookmark to `/` still lands correctly. The sidebar's "Relatórios" nav item and the "G" logo
mark (`frontend/src/lib/navegacao.tsx`, `frontend/src/components/sidebar-dupla.tsx`) both link
directly to `/relatorios` (not `/`, to avoid the extra redirect hop).

`frontend/src/lib/alertas-actions.ts`'s `marcarAlertaVisto`/`marcarTodosVistos` server actions call
`revalidatePath` to refresh the clients-table badges after marking an alert seen — these were
updated from `revalidatePath("/")` to `revalidatePath("/relatorios")` at the same time. **Any other
code that revalidates or links to `"/"` expecting the clients table is now wrong** — grep for
`revalidatePath("/")` / `href="/"` before adding new alert-related mutations.

## Why

User's explicit request: "quero que relatórios ao invés de ser / quero que seja /relatorios" — no
further reasoning given; likely to keep `/` available as a neutral landing/redirect point as more
tools get added under the same multi-tool navigation (see
`decisions/DEC-20260909-multi-tool-navigation-architecture.md`).
