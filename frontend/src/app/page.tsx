import { ClientesTable } from "@/components/clientes-table";
import { DateRangeFilter } from "@/components/date-range-filter";
import { getClientesResumo, paraDatetimeLocal } from "@/lib/backend";

function primeiroValor(valor: string | string[] | undefined): string | undefined {
  return Array.isArray(valor) ? valor[0] : valor;
}

export default async function Page({ searchParams }: PageProps<"/">) {
  const params = await searchParams;
  const resumo = await getClientesResumo(primeiroValor(params.inicio), primeiroValor(params.fim));

  return (
    <div className="min-h-full flex-1 bg-zinc-50 px-6 py-10 sm:px-10">
      <div className="mx-auto max-w-6xl">
        <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-amber-600">GS VoIP</p>
            <h1 className="text-2xl font-semibold text-zinc-900">Relatórios</h1>
          </div>
          <DateRangeFilter
            inicio={paraDatetimeLocal(resumo.inicio)}
            fim={paraDatetimeLocal(resumo.fim)}
          />
        </header>

        <ClientesTable clientes={resumo.clientes} inicio={resumo.inicio} fim={resumo.fim} />
      </div>
    </div>
  );
}
