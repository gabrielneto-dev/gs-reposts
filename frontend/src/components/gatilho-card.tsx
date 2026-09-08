"use client";

import { useState } from "react";

import { GatilhoForm } from "@/components/gatilho-form";
import { desativarGatilho } from "@/lib/gatilhos-actions";
import type { Gatilho } from "@/lib/gatilhos";
import { SEVERIDADE_LABEL, SEVERIDADE_PILULA } from "@/lib/severidade";

const METRICA_LABEL: Record<string, string> = {
  asr_percentual: "ASR",
  acd_segundos: "ACD",
  pdd_medio_segundos: "PDD",
};

const PERIODO_LABEL: Record<string, string> = {
  media_ontem: "ontem",
  media_semanal: "média semanal",
  media_mensal: "média mensal",
};

const DIRECAO_LABEL: Record<string, string> = {
  aumento: "subir",
  queda: "cair",
  qualquer: "variar",
};

function descreverCondicao(condicao: Gatilho["condicoes"][number]): string {
  const metrica = METRICA_LABEL[condicao.metrica] ?? condicao.metrica;
  const direcao = DIRECAO_LABEL[condicao.direcao] ?? condicao.direcao;
  const periodo = PERIODO_LABEL[condicao.periodo_referencia] ?? condicao.periodo_referencia;
  return `${metrica} ${direcao} ${condicao.percentual_limite}% vs ${periodo}`;
}

export function GatilhoCard({ gatilho }: { gatilho: Gatilho }) {
  const [editando, setEditando] = useState(false);

  return (
    <div className="rounded-3xl border border-black/5 bg-white p-6 shadow-sm shadow-black/[0.03]">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <h3 className="font-medium text-zinc-900">{gatilho.nome}</h3>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-medium ${SEVERIDADE_PILULA[gatilho.severidade]}`}
            >
              {SEVERIDADE_LABEL[gatilho.severidade]}
            </span>
            {!gatilho.ativo && (
              <span className="rounded-full bg-zinc-100 px-2 py-0.5 text-xs font-medium text-zinc-500">
                inativo
              </span>
            )}
            {gatilho.cliente_id !== null && (
              <span className="rounded-full bg-sky-50 px-2 py-0.5 text-xs font-medium text-sky-600">
                cliente {gatilho.cliente_id}
              </span>
            )}
          </div>
          <p className="mt-2 text-sm text-zinc-500">
            {gatilho.condicoes.map(descreverCondicao).join(gatilho.combinador === "e" ? " E " : " OU ")}
          </p>
        </div>
        <div className="flex shrink-0 gap-3 text-xs font-medium">
          <button
            type="button"
            onClick={() => setEditando((v) => !v)}
            className="text-amber-600 hover:text-amber-700"
          >
            {editando ? "fechar" : "editar"}
          </button>
          {gatilho.ativo && (
            <form action={desativarGatilho.bind(null, gatilho.id)}>
              <button type="submit" className="text-rose-500 hover:text-rose-600">
                desativar
              </button>
            </form>
          )}
        </div>
      </div>

      {editando && (
        <div className="mt-5 border-t border-black/5 pt-5">
          <GatilhoForm gatilhoExistente={gatilho} />
        </div>
      )}
    </div>
  );
}
