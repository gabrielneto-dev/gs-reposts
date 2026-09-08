import { ClientesTable } from "@/components/clientes-table";
import { getClientesResumo } from "@/lib/backend";

export default async function Page() {
  const clientes = await getClientesResumo();

  return (
    <div className="min-h-full flex-1 bg-zinc-50 px-6 py-10 sm:px-10">
      <div className="mx-auto max-w-6xl">
        <header className="mb-6">
          <p className="text-xs font-medium uppercase tracking-wide text-amber-600">GS VoIP</p>
          <h1 className="text-2xl font-semibold text-zinc-900">Relatórios</h1>
        </header>

        <ClientesTable clientes={clientes} />
      </div>
    </div>
  );
}
