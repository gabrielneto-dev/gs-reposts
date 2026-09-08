"use client";

import { useState } from "react";
import type { AlertaDisparado } from "@/lib/alertas";
import { marcarAlertaVisto } from "@/lib/alertas-actions";
import { SEVERIDADE_LABEL, SEVERIDADE_PILULA, SEVERIDADE_PONTO } from "@/lib/severidade";

const formatadorData = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "America/Sao_Paulo",
  day: "2-digit",
  month: "2-digit",
  year: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

const METRICA_LABEL: Record<string, string> = {
  asr_percentual: "ASR",
  acd_segundos: "ACD",
  pdd_medio_segundos: "PDD",
};

function formatarValor(metrica: string, valor: number | null): string {
  if (valor === null) return "—";
  return metrica === "asr_percentual" ? `${valor.toFixed(1)}%` : `${valor.toFixed(2)}s`;
}

export function AlertasTable({ alertas }: { alertas: AlertaDisparado[] }) {
  const [expandido, setExpandido] = useState<number | null>(null);

  if (alertas.length === 0) {
    return (
      <div className="rounded-3xl border border-black/5 bg-white p-10 text-center text-sm text-zinc-400 shadow-sm shadow-black/[0.03]">
        Nenhum alerta disparado ainda.
      </div>
    );
  }

  return (
    <div className="divide-y divide-black/5 rounded-3xl border border-black/5 bg-white shadow-sm shadow-black/[0.03]">
      {alertas.map((alerta) => {
        const aberto = expandido === alerta.id;
        return (
          <div
            key={alerta.id}
            className={`flex items-start gap-4 p-5 ${alerta.visto ? "" : "bg-amber-50/40"}`}
          >
            <span
              title={alerta.visto ? "Visto" : "Não visto"}
              className={`mt-2 h-2 w-2 shrink-0 rounded-full ${SEVERIDADE_PONTO[alerta.severidade]} ${alerta.visto ? "opacity-30" : ""}`}
            />

            <div className="min-w-0 flex-1">
              <button
                type="button"
                onClick={() => setExpandido(aberto ? null : alerta.id)}
                className="flex w-full flex-wrap items-center justify-between gap-2 text-left"
              >
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <p className={`font-medium ${alerta.visto ? "text-zinc-500" : "text-zinc-900"}`}>
                      {alerta.gatilho_nome}
                    </p>
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${SEVERIDADE_PILULA[alerta.severidade]}`}
                    >
                      {SEVERIDADE_LABEL[alerta.severidade]}
                    </span>
                  </div>
                  <p className="text-sm text-zinc-500">
                    {alerta.cliente_nome ?? `Cliente ${alerta.cliente_id}`} · ID {alerta.cliente_id}
                  </p>
                </div>
                <span className="text-xs text-zinc-400">{formatadorData.format(new Date(alerta.disparado_em))}</span>
              </button>

              {aberto && (
                <div className="mt-4 space-y-2 rounded-2xl bg-zinc-50 p-4 text-sm">
                  {alerta.metricas_avaliadas.map((c, i) => (
                    <div key={i} className="flex flex-wrap items-center justify-between gap-2">
                      <span className="text-zinc-600">
                        {METRICA_LABEL[c.metrica] ?? c.metrica} vs {c.periodo_referencia.replace("media_", "média ")}
                      </span>
                      <span className="font-medium text-zinc-900">
                        {formatarValor(c.metrica, c.atual)} (era {formatarValor(c.metrica, c.referencia)}
                        {c.percentual_variacao !== null
                          ? `, ${c.percentual_variacao > 0 ? "+" : ""}${c.percentual_variacao.toFixed(1)}%`
                          : ", sem histórico"}
                        )
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {!alerta.visto && (
              <form action={marcarAlertaVisto.bind(null, alerta.id)} className="shrink-0">
                <button
                  type="submit"
                  className="rounded-full border border-black/5 bg-white px-3 py-1.5 text-xs font-medium text-zinc-600 transition hover:border-amber-300 hover:text-amber-700"
                >
                  marcar como visto
                </button>
              </form>
            )}
          </div>
        );
      })}
    </div>
  );
}
