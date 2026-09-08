import { GatilhoCard } from "@/components/gatilho-card";
import { GatilhoForm } from "@/components/gatilho-form";
import { getGatilhos } from "@/lib/gatilhos";

export default async function GatilhosPage() {
  const { gatilhos } = await getGatilhos();
  const globais = gatilhos.filter((g) => g.cliente_id === null);
  const individuais = gatilhos.filter((g) => g.cliente_id !== null);

  return (
    <div className="min-h-full flex-1 bg-zinc-50 px-6 py-10 sm:px-10">
      <div className="mx-auto max-w-4xl space-y-10">
        <header>
          <p className="text-xs font-medium uppercase tracking-wide text-amber-600">GS VoIP</p>
          <h1 className="text-2xl font-semibold text-zinc-900">Gatilhos</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Regras que disparam um alerta quando ASR/ACD/PDD variam demais em relação a um período de
            referência (ontem, média semanal ou mensal). Regras globais valem pra todo cliente; regras
            individuais se somam a elas.
          </p>
        </header>

        <section className="rounded-3xl border border-black/5 bg-white p-6 shadow-sm shadow-black/[0.03]">
          <h2 className="mb-4 text-lg font-semibold text-zinc-900">Nova regra</h2>
          <GatilhoForm />
        </section>

        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-zinc-900">Regras globais</h2>
          {globais.length === 0 && (
            <p className="text-sm text-zinc-400">Nenhuma regra global cadastrada.</p>
          )}
          {globais.map((g) => (
            <GatilhoCard key={g.id} gatilho={g} />
          ))}
        </section>

        <section className="space-y-4">
          <h2 className="text-lg font-semibold text-zinc-900">Regras individuais</h2>
          {individuais.length === 0 && (
            <p className="text-sm text-zinc-400">Nenhuma regra individual cadastrada.</p>
          )}
          {individuais.map((g) => (
            <GatilhoCard key={g.id} gatilho={g} />
          ))}
        </section>
      </div>
    </div>
  );
}
