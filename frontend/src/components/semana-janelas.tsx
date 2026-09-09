"use client";

import Link from "next/link";
import { useActionState } from "react";

import { dispararJanela, type ResultadoDisparo } from "@/lib/janelas-actions";
import { SITUACAO_COR, SITUACAO_LABEL, type DiaGrade, type SlotJanela } from "@/lib/janelas";
import { DIAS_SEMANA } from "@/lib/calendario";

const formatadorHora = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "America/Sao_Paulo",
  hour: "2-digit",
  minute: "2-digit",
});

function formatarFaixa(inicioIso: string, fimIso: string): string {
  return `${formatadorHora.format(new Date(inicioIso))} – ${formatadorHora.format(new Date(fimIso))}`;
}

function formatarDiaMes(dataISO: string): string {
  const [, mes, dia] = dataISO.split("-");
  return `${dia}/${mes}`;
}

const ESTADO_INICIAL: ResultadoDisparo = { ok: false };

function CelulaSlot({ slot, data }: { slot: SlotJanela; data: string }) {
  const acao = dispararJanela.bind(null, slot.inicio_janela, slot.fim_janela);
  const [estado, submeter, pendente] = useActionState(acao, ESTADO_INICIAL);

  const titulo = `${formatarFaixa(slot.inicio_janela, slot.fim_janela)} · ${SITUACAO_LABEL[slot.situacao]}${
    slot.janela_id !== null ? ` · ${slot.clientes_processados}/${slot.clientes_descobertos} clientes` : ""
  }${estado.erro ? ` · ${estado.erro}` : ""}`;

  if (slot.situacao === "faltando") {
    return (
      <form action={submeter} title={titulo}>
        <button
          type="submit"
          disabled={pendente || estado.ok}
          className={`h-6 w-6 rounded-md transition hover:ring-2 hover:ring-amber-300 disabled:pointer-events-none ${
            estado.ok ? SITUACAO_COR.concluida : SITUACAO_COR.faltando
          } ${pendente ? "animate-pulse" : ""}`}
        />
      </form>
    );
  }

  if (slot.situacao === "futuro") {
    return <div title={titulo} className={`h-6 w-6 rounded-md ${SITUACAO_COR.futuro}`} />;
  }

  return (
    <Link
      href={`/janelas?visao=dia&data=${data}`}
      title={titulo}
      className={`block h-6 w-6 rounded-md transition hover:ring-2 hover:ring-amber-300 ${SITUACAO_COR[slot.situacao]}`}
    />
  );
}

export function SemanaJanelas({ dias }: { dias: DiaGrade[] }) {
  const totalSlots = dias[0]?.janelas.length ?? 0;

  return (
    <div className="overflow-x-auto rounded-3xl border border-black/5 bg-white p-6 shadow-sm shadow-black/[0.03]">
      <table className="w-full min-w-[560px] border-collapse">
        <thead>
          <tr>
            <th className="w-16 pb-3 text-left text-xs font-medium text-zinc-400" />
            {dias.map((dia, indice) => (
              <th key={dia.data} className="pb-3 text-center text-xs font-medium text-zinc-500">
                {DIAS_SEMANA[indice]}
                <br />
                {formatarDiaMes(dia.data)}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {Array.from({ length: totalSlots }).map((_, indiceSlot) => (
            <tr key={indiceSlot}>
              <td className="py-1 pr-3 text-right text-xs text-zinc-400">
                {dias[0] ? formatadorHora.format(new Date(dias[0].janelas[indiceSlot].inicio_janela)) : ""}
              </td>
              {dias.map((dia) => (
                <td key={dia.data} className="p-1 text-center">
                  <div className="flex items-center justify-center">
                    <CelulaSlot slot={dia.janelas[indiceSlot]} data={dia.data} />
                  </div>
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
