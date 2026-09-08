import { AlertasTable } from "@/components/alertas-table";
import { getAlertas } from "@/lib/alertas";
import { marcarTodosVistos } from "@/lib/alertas-actions";

function primeiroValor(valor: string | string[] | undefined): string | undefined {
  return Array.isArray(valor) ? valor[0] : valor;
}

export default async function AlertasPage({ searchParams }: PageProps<"/alertas">) {
  const params = await searchParams;
  const clienteIdBruto = primeiroValor(params.cliente_id);
  const clienteId = clienteIdBruto ? Number(clienteIdBruto) : undefined;

  const { alertas, registros } = await getAlertas({ clienteId });
  const naoVistos = alertas.filter((a) => !a.visto).length;

  return (
    <div className="min-h-full flex-1 bg-zinc-50 px-6 py-10 sm:px-10">
      <div className="mx-auto max-w-4xl">
        <header className="mb-6 flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-xs font-medium uppercase tracking-wide text-amber-600">GS VoIP</p>
            <h1 className="text-2xl font-semibold text-zinc-900">Central de alertas</h1>
            <p className="mt-1 text-sm text-zinc-500">
              {registros} alerta(s) disparado(s){clienteId !== undefined ? ` pelo cliente ${clienteId}` : ""}
              {naoVistos > 0 ? ` · ${naoVistos} não visto(s)` : ""}
            </p>
          </div>
          {naoVistos > 0 && (
            <form action={marcarTodosVistos.bind(null, clienteId)}>
              <button
                type="submit"
                className="rounded-full bg-zinc-900 px-4 py-2 text-xs font-medium text-white transition hover:bg-zinc-800"
              >
                Marcar todos como vistos
              </button>
            </form>
          )}
        </header>

        <AlertasTable alertas={alertas} />
      </div>
    </div>
  );
}
