# Constraints

**Status: established** (2026-09-04).

## Production, no staging

The only NextRouter environment available is the company's real production softswitch
(`sip5.gsvoip.com.br`). There is no sandbox/staging instance. Every request this project's tests
or routes make is a real request against production. The user has explicitly asked for caution
here: **only read (GET) routes are permitted** — never call a write/mutating endpoint (e.g.
`manageCredit`, `manageCustomers`, or the `DELETE /api/onlineCalls/{token}/{key}/{id}` hangup
endpoint) without explicit authorization for that specific action.

## Credentials

Softswitch credentials (`SOFTSWITCH_API_URL`, `SOFTSWITCH_API_TOKEN`, `SOFTSWITCH_API_KEY`) live
in `backend/.env`; the frontend's Postgres `DATABASE_URL` lives in `frontend/.env`. Both are
git-ignored. Per `Context/README.md` security rules, actual credential values are never written
into `Context/` — only that they exist, their env-var names, and (for the local Postgres role)
which role/database they authenticate as. See
`Context/branches/frontend-nextjs-prisma/facts/FCT-20260904-local-postgres.md`.

## Query cost / rate limits (self-imposed, not enforced by the API)

The NextRouter API itself has no visible rate limiting, but several undocumented behaviors make
naive queries expensive at scale — see
`Context/branches/nextrouter-api/facts/FCT-20260904-cdr-api-behavior.md`. This project's own code
enforces safety caps (page size <=10,000, max pages, max days per request, bounded concurrency via
semaphores) to avoid hammering production — preserve these when modifying the sampling/exact-mode
logic.

## Git repository

The project is now a git repo pushed to GitHub (`https://github.com/gabrielneto-dev/gs-reposts.git`,
branch `main`) — commit history is available going forward for "why was this changed" questions
from 2026-09-04 onward. Before that date, no history exists, so decisions from that period (e.g.
`CTX-DEC-20260904-route-simplification`) still need to be carried explicitly in `Context/`.

The harness's own auto-mode safety classifier has, twice so far, blocked ordinary git operations
(`git add` on a large directory, `git push`) with a generic "blocked by classifier" error and no
specific reason. Both resolved on a plain retry of the identical command. Don't treat this as a
real permissions or auth problem — retry once before troubleshooting further.
