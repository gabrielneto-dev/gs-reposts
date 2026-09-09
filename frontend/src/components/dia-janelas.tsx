"use client";

import { useActionState } from "react";

import { dispararJanela, type ResultadoDisparo } from "@/lib/janelas-actions";
import { SITUACAO_LABEL, SITUACAO_PILULA, type SlotJanela } from "@/lib/janelas";

const formatadorHora = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "America/Sao_Paulo",
  hour: "2-digit",
  minute: "2-digit",
});

function formatarFaixa(inicioIso: string, fimIso: string): string {
  return `${formatadorHora.format(new Date(inicioIso))} – ${formatadorHora.format(new Date(fimIso))}`;
}

const ESTADO_INICIAL: ResultadoDisparo = { ok: false };

function LinhaSlot({ slot }: { slot: SlotJanela }) {
  const acao = dispararJanela.bind(null, slot.inicio_janela, slot.fim_janela);
  const [estado, submeter, pendente] = useActionState(acao, ESTADO_INICIAL);

  return (
    <div className="flex flex-wrap items-center justify-between gap-3 p-4">
      <div className="flex items-center gap-4">
        <span className="w-32 shrink-0 text-sm font-medium text-zinc-700">
          {formatarFaixa(slot.inicio_janela, slot.fim_janela)}
        </span>
        <span className={`rounded-full px-2.5 py-1 text-xs font-medium ${SITUACAO_PILULA[slot.situacao]}`}>
          {SITUACAO_LABEL[slot.situacao]}
        </span>
        {slot.janela_id !== null && (
          <span className="text-sm text-zinc-500">
            {slot.clientes_processados}/{slot.clientes_descobertos} clientes
          </span>
        )}
        {slot.mensagem_erro && <span className="text-sm text-rose-600">{slot.mensagem_erro}</span>}
      </div>

      {slot.pode_disparar && (
        <form action={submeter}>
          <button
            type="submit"
            disabled={pendente || estado.ok}
            className="rounded-full border border-black/5 bg-white px-3.5 py-1.5 text-xs font-medium text-zinc-600 transition hover:border-amber-300 hover:text-amber-700 disabled:pointer-events-none disabled:opacity-50"
          >
            {pendente ? "Disparando..." : estado.ok ? "Disparado" : "Disparar"}
          </button>
          {estado.erro && <p className="mt-1 text-xs text-rose-600">{estado.erro}</p>}
        </form>
      )}
    </div>
  );
}

export function DiaJanelas({ janelas }: { janelas: SlotJanela[] }) {
  return (
    <div className="divide-y divide-black/5 rounded-3xl border border-black/5 bg-white shadow-sm shadow-black/[0.03]">
      {janelas.map((slot) => (
        <LinhaSlot key={slot.inicio_janela} slot={slot} />
      ))}
    </div>
  );
}
