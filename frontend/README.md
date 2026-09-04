# frontend

Aplicação de interface com o usuário final do projeto — **tem banco de dados próprio** (é o
sistema de registro de fato, diferente de `../backend/`, que é só um adapter sem persistência
pra API do NextRouter). Consome `../backend/` via HTTP para os dados do softswitch (ASR, ACD, PDD,
clientes) — ver `../backend/docs/API.md`.

## Stack

- **Next.js 16** (App Router, TypeScript, Tailwind CSS, Turbopack)
- **Prisma 8** ("Prisma Next", ainda em release candidate) como ORM, com **PostgreSQL**

## Como rodar

```bash
cd frontend
npm install
cp .env.example .env   # e ajuste DATABASE_URL pra apontar pro seu Postgres
npm run dev
```

Abre em [http://localhost:3000](http://localhost:3000).

## Banco de dados (Prisma)

O schema ("data contract") fica em [`src/prisma/contract.prisma`](src/prisma/contract.prisma).
Fluxo de trabalho:

1. Edita `src/prisma/contract.prisma`.
2. Roda `npm run contract:emit` (ou `npx prisma contract emit`) pra regenerar
   `contract.json`/`contract.d.ts`.
3. Usa `import { db } from './src/prisma/db'` nas suas rotas/componentes — autocomplete e tipos
   prontos pra cada model.

Ver [`prisma-next.md`](prisma-next.md) (gerado pelo próprio Prisma) para mais detalhes e comandos
de migração (`npx prisma db init`, `npx prisma migration status`).

Ainda não há um Postgres real configurado — `.env` tem só um placeholder de `DATABASE_URL`.
