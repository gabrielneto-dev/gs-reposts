---
id: CTX-FCT-20260909-janelas-page
type: fact
title: /janelas page — day/week/month status views, manual trigger, calendario.ts extraction
branch: frontend-nextjs-prisma
tags: [frontend, janelas, calendar, ui]
status: active
confidence: high
created_at: 2026-09-09
updated_at: 2026-09-09
source_ids: []
related: [CTX-DEC-20260909-manual-window-trigger]
depends_on: [CTX-DEC-20260909-manual-window-trigger]
supersedes: null
superseded_by: null
valid_from: 2026-09-09
valid_until: null
revisit_at: null
---

## What

`frontend/src/app/janelas/page.tsx` — status view of the backend's 15 canonical daily collection
slots (see `Context/branches/metrics-pipeline/decisions/DEC-20260909-manual-window-trigger.md`),
with three views (Dia/Semana/Mês, `?visao=`) and date navigation (`?data=YYYY-MM-DD`), each backed
by one component:

- `frontend/src/components/dia-janelas.tsx` — one row per slot, `useActionState` bound to
  `janelas-actions.ts`'s `dispararJanela(inicio, fim)` server action, shows a "Disparar" /
  "Disparando..." / "Disparado" button only for `faltando` slots.
- `frontend/src/components/semana-janelas.tsx` — 15-row × 7-col table; `faltando` cells get the
  trigger form, `futuro` cells are inert, real-status cells link to the day view.
- `frontend/src/components/mes-janelas.tsx` — month calendar grid, each day cell shows small
  colored dots summarizing that day's slot statuses (priority order for which status "wins" the
  dot when a day has several: `em_andamento > falhou > parcial > faltando > concluida > futuro`).

`frontend/src/lib/calendario.ts` (new) holds shared calendar-math helpers (`gerarCelulasDoMes`,
`addDias`, `addMeses`, `dataISO`, etc.) — extracted out of `date-range-filter.tsx`, which now
imports from here instead of duplicating them, so the two calendar UIs (date-range picker and
janelas month view) share one implementation.

## Bug fixed: "Hoje" nav button not reflecting the viewed date

The middle of the nav bar was a static "Hoje" label with no date display at all, so navigating
away never visibly confirmed the date had changed. Fixed by adding a `rotuloPeriodo()` function
(renders the actual period being viewed) and making "Hoje" a conditional shortcut link
(`estaNoPeriodoAtual` check) that only appears when *not* already viewing the current period.
Found and fixed alongside two small CSS bugs in the same component: a stray Tailwind `capitalize`
class was capitalizing the Portuguese word "de" mid-sentence ("9 De Setembro De 2026"), and the
month tab label relied on a raw enum string + `capitalize`, rendering "Mes" (missing the
circumflex) — replaced with an explicit `VISAO_LABEL: Record<Visao, string>` map instead of
deriving display text from data values.

## Relations

- Backend counterpart: `Context/branches/metrics-pipeline/decisions/DEC-20260909-manual-window-trigger.md`.
- Uses the sidebar navigation described in
  `decisions/DEC-20260909-multi-tool-navigation-architecture.md` (grouped under "Coleta").
