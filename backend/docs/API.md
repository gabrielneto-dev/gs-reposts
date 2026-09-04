# API de Relatórios — Documentação de Rotas

API FastAPI que consulta o softswitch **NextRouter** (NextBilling IP Solutions) e expõe métricas
de telefonia (ASR, ACD, PDD) e consulta de clientes, prontas pra consumo por outras ferramentas
(dashboards, relatórios, jobs agendados).

Esse serviço é o **`backend/`** do monorepo — um **adapter**: não tem banco de dados próprio e
não é a fonte de verdade do sistema. Ele só traduz a API (cheia de particularidades) do NextRouter
em endpoints REST limpos. O `frontend/` (em construção) é quem tem banco de dados e é o sistema
de registro de fato; ele consome esse backend pra dados do softswitch.

## Como rodar

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate   # Windows (Git Bash)
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Configuração em [`.env`](../.env) (nunca commitar — já está no `.gitignore`):

```
SOFTSWITCH_API_URL=sip5.gsvoip.com.br
SOFTSWITCH_API_TOKEN=...
SOFTSWITCH_API_KEY=...
```

Docs interativos (Swagger) em `http://127.0.0.1:8000/docs`.

## Como a API do NextRouter é usada por baixo

Todas as rotas consultam, com o padrão de autenticação `.../{api_token}/{api_key}/...` na URL:

- `GET /api/cdr/{token}/{key}(/{cliente_id})` — chamadas **atendidas** (tarifadas). `total_records`
  e `total_time` do agregado são exatos e baratos (`limit=1`).
- `GET /api/cdrDisconnection/{token}/{key}(/{cliente_id})` — chamadas **com falha**. `total_records`
  é exato; os registros individuais (campos `pdd`, `sip_code`, `disposition`) só existem aqui, e a
  API não tem agregado nem filtro por código pronto — por isso várias rotas usam amostragem.
- `GET /api/contacts/{token}/{key}` — cadastro de clientes (agenda de contatos).

Limites descobertos na prática (não documentados oficialmente):

- `limit` por página é aceito até **10.000** — acima disso é cortado silenciosamente pra 200.
- Num período de mais de 1 dia, `time_ini`/`time_end` só valem pro **primeiro** e **último** dia
  do intervalo, não em cada dia do meio — por isso rotas como `/api/clientes/recorrencia` escaneiam
  dia a dia quando precisam da mesma janela de horário todo santo dia.
- Não existe filtro server-side por `disposition`/`sip_code` (testado e ignorado pela API).
- Omitir `data_fim` faz a API usar "hoje" dinamicamente — **sempre passe datas explícitas**.

## Índice de rotas

| Rota | Método | Resumo |
|---|---|---|
| [`/api/asr`](#get-apiasr) | GET | ASR com detalhamento por código (200, 487, 486...) |
| [`/api/acd`](#get-apiacd) | GET | Tempo médio falado (exato) |
| [`/api/pdd`](#get-apipdd) | GET | Tempo até a primeira resposta |
| [`/api/clientes`](#get-apiclientes) | GET | Listagem crua de clientes |
| [`/api/clientes/busca`](#get-apiclientesbusca) | GET | Busca fuzzy por nome |
| [`/api/clientes/atividade`](#get-apiclientesatividade) | GET | Clientes ativos numa janela única |
| [`/api/clientes/recorrencia`](#get-apiclientesrecorrencia) | GET | Clientes ativos em N de M dias |
| [`/health`](#get-health) | GET | Healthcheck da própria API |

---

## `GET /api/asr`

ASR (Answer Seizure Ratio) de um período, com o detalhamento "de pizza" por código de resultado
de chamada (200 OK, 487, 486, 503 etc). `total_atendidas`/`total_falhas`/`total_chamadas`/
`asr_percentual` são **sempre exatos** (agregados da API). O detalhamento por código é amostrado
por padrão; `exato=true` pagina todas as falhas do período pra um número 100% auditável.

### Parâmetros

| Nome | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| `cliente_id` | int | Não | — | ID do cliente. Omitido = base toda |
| `data_inicio` | date | Não | — | `YYYY-MM-DD` |
| `data_fim` | date | Não | — | `YYYY-MM-DD` |
| `hora_inicio` | time | Não | — | `HH:MM:SS` |
| `hora_fim` | time | Não | — | `HH:MM:SS` |
| `amostra_falhas` | int | Não | 1000 | Registros de falha usados no detalhamento por código. Ignorado se `exato=true` |
| `exato` | bool | Não | false | Se true, pagina TODAS as falhas do período (até 10.000/página) — mais lento e mais pesado quanto maior o volume |

### Exemplo

```bash
curl "http://127.0.0.1:8000/api/asr?cliente_id=256&data_inicio=2026-09-03&data_fim=2026-09-03&hora_inicio=15:00&hora_fim=16:00&amostra_falhas=1000"
```

```json
{
  "cliente_id": 256,
  "periodo": {"data_inicio": "2026-09-03", "data_fim": "2026-09-03", "hora_inicio": "15:00:00", "hora_fim": "16:00:00"},
  "total_atendidas": 8606,
  "total_falhas": 92134,
  "total_chamadas": 100740,
  "asr_percentual": 8.54,
  "disposicoes": [
    {"codigo": "200", "descricao": "ANSWERED (atendida)", "quantidade": 8606, "percentual": 8.54, "exato": true},
    {"codigo": "480", "descricao": "Não atendida", "quantidade": 323, "percentual": 64.6, "exato": false},
    {"codigo": "487", "descricao": "Congestionamento / indisponível", "quantidade": 19, "percentual": 3.8, "exato": false}
  ],
  "tamanho_amostra_falhas": 500,
  "exato": false,
  "truncado": false
}
```

**Cuidado com `exato=true`**: em janelas grandes ou clientes de alto volume pode levar minutos
(medido: ~20s pra 22 mil falhas, ~3 páginas). O campo `truncado: true` avisa se bateu no limite de
segurança (100 páginas / 1 milhão de registros) antes de esgotar o período.

---

## `GET /api/acd`

ACD (Average Call Duration / tempo médio falado). Sempre exato — vem direto do agregado de
`/api/cdr` (`total_time / total_records`), sem amostragem.

### Parâmetros

| Nome | Tipo | Obrigatório | Descrição |
|---|---|---|---|
| `cliente_id` | int | Não | ID do cliente. Omitido = base toda |
| `data_inicio` / `data_fim` | date | Não | `YYYY-MM-DD` |
| `hora_inicio` / `hora_fim` | time | Não | `HH:MM:SS` |

### Exemplo

```bash
curl "http://127.0.0.1:8000/api/acd?cliente_id=256&data_inicio=2026-09-04&data_fim=2026-09-04&hora_inicio=08:00&hora_fim=08:15"
```

```json
{
  "cliente_id": 256,
  "periodo": {"data_inicio": "2026-09-04", "data_fim": "2026-09-04", "hora_inicio": "08:00:00", "hora_fim": "08:15:00"},
  "total_atendidas": 2407,
  "acd_segundos": 32.82
}
```

---

## `GET /api/pdd`

PDD (Post Dial Delay / tempo até a primeira resposta). O campo `pdd` só existe em chamadas com
**falha** (`/api/cdrDisconnection`) — não há agregado/média pronta na API, então é sempre estimado
a partir de registros individuais: amostrado por padrão, ou exato com `exato=true`.

### Parâmetros

| Nome | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| `cliente_id` | int | Não | — | ID do cliente. Omitido = base toda |
| `data_inicio` / `data_fim` | date | Não | — | `YYYY-MM-DD` |
| `hora_inicio` / `hora_fim` | time | Não | — | `HH:MM:SS` |
| `amostra` | int | Não | 1000 | Registros de falha usados na média. Ignorado se `exato=true` |
| `exato` | bool | Não | false | Pagina TODAS as falhas do período pra uma média 100% exata |

### Exemplo

```bash
curl "http://127.0.0.1:8000/api/pdd?cliente_id=256&data_inicio=2026-09-04&data_fim=2026-09-04&hora_inicio=08:00&hora_fim=08:15"
```

```json
{
  "cliente_id": 256,
  "periodo": {"data_inicio": "2026-09-04", "data_fim": "2026-09-04", "hora_inicio": "08:00:00", "hora_fim": "08:15:00"},
  "pdd_medio_segundos": 0.7,
  "tamanho_amostra": 1000,
  "total_falhas_periodo": 14445,
  "exato": false,
  "truncado": false
}
```

---

## `GET /api/clientes`

Listagem crua dos clientes/assinantes cadastrados na plataforma (`/api/contacts`), paginada, na
ordem que a API retorna. **Sem relação com uso/atividade** — é só o cadastro.

### Parâmetros

| Nome | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| `start` | int | Não | 0 | Offset de paginação |
| `limit` | int | Não | 50 | Clientes por página (máx 500) |

### Exemplo

```bash
curl "http://127.0.0.1:8000/api/clientes?start=0&limit=50"
```

```json
{
  "offset": 0, "limit": 50, "registros": 50,
  "clientes": [
    {"id": 256, "tipo": "4", "tipo_descricao": "CUSTOMER", "nome_fantasia": "SETRA SOLUCOES EM ATENDIMENTO LTDA",
     "razao_social": "SETRA SOLUCOES EM ATENDIMENTO LTDA", "telefone": "11979533326",
     "email": "beatriz.oliveira@setrabpo.com.br", "cidade": "São Caetano do Sul", "estado": "SP",
     "status": 1, "usuarios": ["setra.voip"]}
  ]
}
```

---

## `GET /api/clientes/busca`

Busca aproximada (fuzzy) por nome fantasia ou razão social — tolera nomes parciais e pequenas
diferenças de digitação (ex: "Seetraa" ainda acha "SETRA...").

### Parâmetros

| Nome | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| `nome` | string | **Sim** | — | Termo buscado |
| `limiar` | float | Não | 60.0 | Similaridade mínima (%) |
| `max_resultados` | int | Não | 20 | Máximo de resultados, ordenados por similaridade |

### Exemplo

```bash
curl "http://127.0.0.1:8000/api/clientes/busca?nome=Setra&limiar=90"
```

```json
{
  "registros": 1,
  "clientes": [{"id": 256, "nome_fantasia": "SETRA SOLUCOES EM ATENDIMENTO LTDA", "similaridade": 100.0, "...": "..."}],
  "aviso": null
}
```

**Como funciona**: compara o termo contra cada palavra do nome (não contra qualquer substring
aleatória — evita falsos positivos tipo "Setra" batendo com "administradora" por causa de um
"astra" escondido em "cadastrais"). Escaneia até 20.000 clientes por busca (paginado, limite de
segurança).

---

## `GET /api/clientes/atividade`

Clientes com chamada (atendida ou falha) em **uma janela** de data/hora, ordenados por volume.
Detecção por **amostragem** — a API não tem um "distinct customer" pronto, então isso amostra até
`amostra_atividade` registros de `/api/cdr` + `/api/cdrDisconnection` (sem filtro de cliente) e
conta quantas vezes cada `customer_id` aparece.

⚠️ Em janelas de mais de 1 dia, a amostra pode ficar enviesada pro início do período — prefira
`/api/clientes/recorrencia` pra períodos longos, ou janelas curtas aqui.

### Parâmetros

| Nome | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| `data_inicio` | date | **Sim** | — | Início do período |
| `data_fim` | date | Não | = `data_inicio` | Fim do período |
| `hora_inicio` / `hora_fim` | time | Não | — | `HH:MM` |
| `amostra_atividade` | int | Não | 3000 | Registros escaneados por endpoint |
| `limit` | int | Não | 50 | Máximo de clientes retornados |

### Exemplo

```bash
curl "http://127.0.0.1:8000/api/clientes/atividade?data_inicio=2026-09-04&data_fim=2026-09-04&hora_inicio=08:00&hora_fim=08:15"
```

```json
{
  "periodo": {"data_inicio": "2026-09-04", "data_fim": "2026-09-04", "hora_inicio": "08:00:00", "hora_fim": "08:15:00"},
  "registros": 3,
  "clientes": [
    {"id": 256, "nome_fantasia": "SETRA SOLUCOES EM ATENDIMENTO LTDA", "chamadas_na_amostra": 4120, "...": "..."}
  ],
  "aviso": null
}
```

---

## `GET /api/clientes/recorrencia`

Clientes com atividade em pelo menos `dias_minimos` dias **distintos** dentro de um período
(ex: "usou pelo menos 3 dos últimos 7 dias"). Escaneia dia a dia — corrige o viés de
`/atividade` em períodos longos.

O período vem de **`janela_dias`** (atalho: últimos N dias a partir de hoje) **ou** de
`data_inicio`+`data_fim` explícitos — use um ou outro, não os dois.

Com **`cliente_id`**: checagem leve e **exata** (não amostrada) — só 2 requisições `limit=1` por
dia, sem baixar chamada nenhuma. Sem `cliente_id`: descobre todos os clientes recorrentes da base
(mais pesado, por amostragem).

### Parâmetros

| Nome | Tipo | Obrigatório | Padrão | Descrição |
|---|---|---|---|---|
| `dias_minimos` | int | **Sim** | — | Mínimo de dias distintos com atividade |
| `janela_dias` | int | Não* | — | Últimos N dias a partir de hoje (1-31). Alternativa a `data_inicio`/`data_fim` |
| `data_inicio` / `data_fim` | date | Não* | — | Período explícito. Alternativa a `janela_dias` |
| `cliente_id` | int | Não | — | Se informado: checagem leve e exata só desse cliente |
| `hora_inicio` / `hora_fim` | time | Não | — | Aplicado em CADA dia do período |
| `amostra_atividade` | int | Não | 3000 | Por dia. Ignorado se `cliente_id` for passado |
| `limit` | int | Não | 50 | Máximo de clientes retornados (modo descoberta) |

\* Informe `janela_dias` OU (`data_inicio` e `data_fim`) — nunca os dois.

### Exemplos

```bash
# checagem leve e exata de UM cliente: usou pelo menos 3 dos últimos 7 dias?
curl "http://127.0.0.1:8000/api/clientes/recorrencia?cliente_id=256&dias_minimos=3&janela_dias=7"

# descoberta: todos os clientes que usaram pelo menos 3 dos últimos 7 dias
curl "http://127.0.0.1:8000/api/clientes/recorrencia?dias_minimos=3&janela_dias=7&limit=20"
```

```json
{
  "data_inicio": "2026-08-29",
  "data_fim": "2026-09-04",
  "dias_minimos": 3,
  "registros": 1,
  "clientes": [
    {
      "id": 256, "nome_fantasia": "SETRA SOLUCOES EM ATENDIMENTO LTDA",
      "chamadas_na_amostra": 3063606,
      "dias_ativos": 5,
      "datas_ativas": ["2026-08-31", "2026-09-01", "2026-09-02", "2026-09-03", "2026-09-04"]
    }
  ],
  "aviso": "Checagem exata (não amostrada) — cliente_id foi informado."
}
```

Se o cliente não bater `dias_minimos`, a resposta vem com `registros: 0` e `clientes: []` (não é
erro).

**Limite de segurança**: até 31 dias por consulta.

---

## `GET /health`

Healthcheck da própria API FastAPI — não consulta o NextRouter. Útil pra monitoramento de infra
(load balancer, Kubernetes, etc) sem depender do softswitch estar respondendo.

```bash
curl "http://127.0.0.1:8000/health"
```

```json
{"status": "ok"}
```

---

## Padrões usados em várias rotas

- **`Periodo`**: `{data_inicio, data_fim, hora_inicio, hora_fim}` — ecoa de volta os filtros usados.
- **Amostragem vs. exato**: quando um valor não tem agregado pronto na API do NextRouter (PDD,
  detalhamento por código, contagem de clientes ativos), a rota amostra por padrão (rápido) e,
  quando existe, oferece um caminho exato (mais lento, paginado). Isso é sempre sinalizado no
  campo `exato`/`aviso` da resposta.
- **`aviso`**: campo de transparência — presente sempre que o resultado tem alguma limitação
  (amostragem, truncamento por limite de segurança, etc). `null` quando não há ressalva.
- **Sempre passe `data_inicio` E `data_fim` juntos** quando quiser um período específico —
  deixar `data_fim` de fora faz a API do NextRouter usar "hoje" dinamicamente no momento da
  consulta.
