---
id: CTX-FCT-20260908-clientes-overview-page
type: fact
title: First real frontend page — a clients-overview table fed by backend/'s stored metrics
branch: frontend-nextjs-prisma
tags: [nextjs, ui, api-design]
status: active
confidence: verified
created_at: 2026-09-08
updated_at: 2026-09-08
source_ids: []
related: [CTX-FCT-20260904-schema-and-reused-functions]
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

## Verification

Tested live via the Browser tool against real collected data (77 clients): search filter, sort
ascending/descending on the ASR column, mobile viewport (375px — table becomes horizontally
scrollable, not restructured), and a clean `npm run build` (TypeScript + static generation) after
every change in this batch of work, including after the Portuguese field rename in
`CTX-DEC-20260908-portuguese-schema-naming` (`inicio_janela`/`fim_janela` replacing
`window_start`/`window_end` in the TS types and component).
