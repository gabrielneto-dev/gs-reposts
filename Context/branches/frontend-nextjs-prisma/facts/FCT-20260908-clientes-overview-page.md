---
id: CTX-FCT-20260908-clientes-overview-page
type: fact
title: First real frontend page — a clients-overview table fed by backend/'s stored metrics
branch: frontend-nextjs-prisma
tags: [nextjs, ui, api-design, realtime]
status: active
confidence: verified
created_at: 2026-09-08
updated_at: 2026-09-08
source_ids: []
related: [CTX-FCT-20260904-schema-and-reused-functions, CTX-DEC-20260908-sse-same-origin-live-refresh, CTX-DEC-20260908-frontend-webhook-notification, CTX-DEC-20260908-clientes-resumo-period-filter]
depends_on: []
supersedes: null
superseded_by: null
valid_from: 2026-09-08
valid_until: null
revisit_at: null
---

## Fact

`frontend/src/app/page.tsx` (root `/`) replaced the `create-next-app` starter with the project's
first real feature: a table listing every client `metrics-pipeline` has collected data for, with
Volume (today), ASR (200 OK only — no per-code breakdown), ACD, and PDD. Visual reference given by
the user: a "Crextio" HR-dashboard screenshot (rounded cards, avatar initials, clean table) —
matched with Tailwind, not a component library.

**Architecture**:

- `frontend/src/lib/backend.ts` — `getClientesResumo()`, a server-only `fetch` against
  `${BACKEND_API_URL}/api/metricas/clientes` (env var, defaults to `http://127.0.0.1:8000`,
  server-side only, never reaches the browser bundle). `cache: "no-store"` — data changes hourly,
  always fetch fresh (Next.js 16's default fetch behavior is already no-cache, this is explicit
  for clarity, not strictly required).
- `frontend/src/app/page.tsx` — Server Component (`async function Page()`), awaits the fetch,
  passes plain data down.
- `frontend/src/components/clientes-table.tsx` — the only Client Component (`"use client"`):
  search-by-name/id and click-to-sort-by-column, both computed client-side over the already-fetched
  list (no extra network round-trips). Confirmed via live browser testing (search "setra" → 1/77;
  clicking a column header toggles asc/desc correctly).
- `frontend/src/app/error.tsx` — error boundary shown if the backend fetch throws (e.g. backend
  down), with a "tentar de novo" retry button.

**Decision**: fetch strategy is server-side (Server Component), not client-side `fetch`/SWR — the
user explicitly chose this when asked, specifically to avoid needing CORS on the FastAPI backend
and to keep the backend's address out of the browser. If client-side fetching is ever needed
later, `backend/app/main.py` will need CORS middleware added (`fastapi.middleware.cors`) — not
present today.

**Known cosmetic bug fixed during this work**: a naive "first letter of first two words" avatar-
initials function produced garbage for names with punctuation as a "word" (e.g. "AADVANCE -
CONSULTORIA..." → "A-", "BARCELOS & JANSSEN..." → "B&"). Fixed by filtering split tokens to only
those starting with a letter (`/^\p{L}/u` regex) before taking initials.

**Added later the same day — live-refresh + a datetime range filter**:

- Live-refresh: `frontend/src/components/live-refresher.tsx` (mounted in `app/layout.tsx`) opens
  an `EventSource` to the app's own `/api/eventos` and calls `router.refresh()` on every message —
  see `decisions/DEC-20260908-sse-same-origin-live-refresh.md` for the full mechanism and why it
  stays same-origin. `/api/eventos` and `/api/webhook/metricas-atualizadas` are this app's first
  API routes ever.
- Date/time filter: `frontend/src/components/date-range-filter.tsx` replaced the page's implicit
  "always today" behavior with an explicit `inicio`/`fim` filter driven by URL search params (so
  it composes with `router.refresh()` above — refreshing re-fetches with whatever period is
  currently in the URL). UI is an Airbnb-style two-month range calendar (click start day, click end
  day, hover previews the in-between band) plus a `type="time"` input per side (Airbnb's own
  picker has no time granularity, this app needed it), a row of one-click presets (Hoje, Ontem,
  Últimas 24h, Esta semana, Este mês), and separate "‹ Anterior" / "Próximo ›" buttons that shift
  the whole period by its own duration (e.g. 12:00-13:00 → 13:00-14:00; 00:00-07:00 → 07:00-14:00)
  — recomputed from whatever's currently applied, not a fixed step. All hand-rolled with native
  `Date` math (no calendar library added) — see `decisions/DEC-20260908-clientes-resumo-period-filter.md`
  for the backend side of this. `frontend/src/app/page.tsx` is now `async function Page({
  searchParams })`, using the `PageProps<"/">` global helper (Next.js 16 generates it), reading
  `inicio`/`fim` and passing the resolved period down to both `DateRangeFilter` and
  `ClientesTable`. `ClienteResumo.volume_dia` was renamed `volume_periodo` throughout the TS types
  to match the backend rename.
- **Gotcha worth remembering**: all datetime arithmetic in `date-range-filter.tsx` deliberately
  avoids `Intl.DateTimeFormat` with an explicit `timeZone` and avoids `new Date(isoStringWithNoOffset)`
  — both would silently reinterpret a naive "wall-clock" string through the *browser's* timezone.
  Instead every conversion goes through matched pairs of manual parse/format helpers
  (`datetimeLocalParaDate`/`dateParaDatetimeLocal`) that only ever use the `Date` object's own
  local getters/constructor — self-consistent regardless of the browser's timezone, since the
  string is never round-tripped through an explicit-zone formatter.

## Verification

Tested live via the Browser tool against real collected data (77 clients): search filter, sort
ascending/descending on the ASR column, mobile viewport (375px — table becomes horizontally
scrollable, not restructured), and a clean `npm run build` (TypeScript + static generation) after
every change in this batch of work, including after the Portuguese field rename in
`CTX-DEC-20260908-portuguese-schema-naming` (`inicio_janela`/`fim_janela` replacing
`window_start`/`window_end` in the TS types and component).

Live-refresh + datetime filter (added later 2026-09-08) also verified live via the Browser tool
against the user's already-running dev servers: simulated the backend's webhook with a raw `curl`
POST and confirmed the open tab issued a fresh RSC fetch immediately after (SSE → refresh path);
exercised the calendar (multi-day range selection with hover-preview band, applying custom hours,
all 5 presets, Anterior/Próximo shifting a 7h window to 07:00-14:00 as specified, click-outside-to-close
via a real `mousedown` event — `.click()` alone doesn't trigger it, Esc key). One thing to know:
during rapid iterative edits, Turbopack's dev-mode Fast Refresh produced transient errors in an
open tab (stale module state mid-HMR) that were not real bugs — always re-verify with a fresh
navigation before treating a console error as real.
