"use server";

import { revalidatePath } from "next/cache";

import { backendUrl } from "./backend";

export type ResultadoDisparo = { ok: boolean; erro?: string };

/** Dispara manualmente a coleta de um slot que ficou faltando (só passado — o backend bloqueia
 * futuro, duplicata e sobreposição com outra coleta em andamento). Roda em background no
 * backend; a tela recebe o webhook de conclusão e atualiza sozinha (mesmo mecanismo do
 * live-refresh de métricas/alertas), então aqui só precisamos revalidar a rota. */
export async function dispararJanela(inicioJanela: string, fimJanela: string): Promise<ResultadoDisparo> {
  const res = await fetch(backendUrl("/api/metricas/janelas/disparar"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ inicio_janela: inicioJanela, fim_janela: fimJanela }),
  });

  if (!res.ok) {
    const corpo = await res.json().catch(() => null);
    return { ok: false, erro: corpo?.detail ?? `Backend respondeu ${res.status}` };
  }

  revalidatePath("/janelas");
  return { ok: true };
}
