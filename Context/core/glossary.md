# Glossary

**Status: established** (2026-09-04).

- **ASR (Answer Seizure Ratio)** — % of call attempts that were answered:
  `atendidas / (atendidas + falhas) * 100`.
- **ACD (Average Call Duration)** — average duration of *answered* calls, in seconds.
- **PDD (Post Dial Delay)** — time from dialing to the first response from the network, in
  seconds. On this NextRouter instance, only tracked on *failed* calls (see
  `Context/branches/nextrouter-api/facts/FCT-20260904-cdr-api-behavior.md`).
- **Softswitch** — the telephony switching platform that routes calls; here, NextBilling's
  **NextRouter C4 SoftSwitch**, hosted per-customer (this company's instance:
  `sip5.gsvoip.com.br`).
- **CDR (Call Detail Record)** — a record of one call attempt. Split across two NextRouter
  endpoints in this project: `/api/cdr` (answered) and `/api/cdrDisconnection` (failed).
- **Disposition** — the categorical outcome of a failed call (`CONGESTION`, `CANCEL`, `NOANSWER`,
  `PDD`, `BUSY`, `NOTFOUND`), distinct from the numeric `sip_code`.
- **cliente_id / customer_id** — the NextRouter subscriber/customer id. Used interchangeably in
  this project's docs; the API field is `customer_id` on CDR records, `id` on `/api/contacts`.
- **NextQualify** — a *separate* NextBilling product (call-quality classifier) with its own
  aggregate ASR reporting API (`graph-pizza`) — **not used by this company**, don't confuse it
  with NextRouter. See
  `Context/branches/nextrouter-api/research/RES-20260904-asr-aggregate-endpoint-search.md`.
- **Amostragem / amostrado (sampled)** vs. **exato (exact)** — this project's own terminology for
  the two computation modes on metrics with no API aggregate. See
  `Context/branches/nextrouter-api/decisions/DEC-20260904-sampling-with-exact-mode.md`.
