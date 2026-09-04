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
in `.env` at the project root, which is git-ignored. Per `Context/README.md` security rules, the
actual credential values are never written into `Context/` — only that they exist and their
env-var names.

## Query cost / rate limits (self-imposed, not enforced by the API)

The NextRouter API itself has no visible rate limiting, but several undocumented behaviors make
naive queries expensive at scale — see
`Context/branches/nextrouter-api/facts/FCT-20260904-cdr-api-behavior.md`. This project's own code
enforces safety caps (page size <=10,000, max pages, max days per request, bounded concurrency via
semaphores) to avoid hammering production — preserve these when modifying the sampling/exact-mode
logic.

## No git repository

The project directory has no `.git` — there is no commit history to fall back on for "why was
this removed/changed" questions. That's part of why `Context/` needs to carry decisions like
`CTX-DEC-20260904-route-simplification` explicitly.
