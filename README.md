# gs-reposts

Sistema interno de relatórios de telefonia para uma empresa de VoIP (GS VoIP), com dados vindos do
softswitch **NextRouter C4 SoftSwitch** (NextBilling IP Solutions).

## Estrutura

```
.
├── backend/    API FastAPI — adapter/integração com o NextRouter. Sem banco de dados próprio,
│               não é a fonte de verdade. Ver backend/docs/API.md.
├── frontend/   Aplicação com interface para o usuário final. Tem seu próprio banco de dados —
│               é o sistema de registro de fato. Consome o backend pra dados do softswitch.
├── Context/    Memória persistente do projeto (decisões, fatos, riscos) — ver AGENTS.md.
└── AGENTS.md   Contrato operacional para agentes de IA trabalhando neste repositório.
```

## Papel de cada parte

- **`backend/`**: só traduz a API do NextRouter (cheia de particularidades não documentadas —
  ver `Context/branches/nextrouter-api/facts/FCT-20260904-cdr-api-behavior.md`) em endpoints REST
  limpos (ASR, ACD, PDD, clientes). Stateless, sem persistência própria.
- **`frontend/`**: interface do usuário + banco de dados próprio (autenticação, preferências,
  dados agregados, o que mais for necessário). Consome o backend via HTTP.

Ver `backend/docs/API.md` para a documentação completa das rotas do backend.
