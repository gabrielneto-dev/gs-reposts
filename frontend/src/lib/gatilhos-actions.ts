"use server";

import { revalidatePath } from "next/cache";

import { backendUrl } from "./backend";
import type { CombinadorCondicoes, DirecaoGatilho, MetricaGatilho, PeriodoReferenciaGatilho } from "./gatilhos";

type CondicaoInput = {
  metrica: MetricaGatilho;
  periodo_referencia: PeriodoReferenciaGatilho;
  direcao: DirecaoGatilho;
  percentual_limite: number;
};

export type ResultadoAcaoGatilho = { ok: boolean; erro?: string };

function condicoesDoFormData(formData: FormData): CondicaoInput[] {
  const bruto = formData.get("condicoes");
  if (typeof bruto !== "string" || !bruto) return [];
  return JSON.parse(bruto) as CondicaoInput[];
}

/** Cria um gatilho (global se `cliente_id` vier vazio, individual caso contrário). */
export async function criarGatilho(
  _estadoAnterior: ResultadoAcaoGatilho | null,
  formData: FormData,
): Promise<ResultadoAcaoGatilho> {
  const nome = String(formData.get("nome") ?? "").trim();
  const clienteIdBruto = String(formData.get("cliente_id") ?? "").trim();
  const combinador = formData.get("combinador") as CombinadorCondicoes;
  const condicoes = condicoesDoFormData(formData);

  if (!nome || condicoes.length === 0) {
    return { ok: false, erro: "Preencha o nome e adicione ao menos uma condição." };
  }

  const res = await fetch(backendUrl("/api/gatilhos"), {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      nome,
      cliente_id: clienteIdBruto ? Number(clienteIdBruto) : null,
      combinador,
      condicoes,
    }),
  });

  if (!res.ok) {
    return { ok: false, erro: `Backend respondeu ${res.status}: ${await res.text()}` };
  }

  revalidatePath("/gatilhos");
  return { ok: true };
}

/** Substitui nome/combinador/ativo/condições de um gatilho existente (o escopo — global ou
 * individual de qual cliente — é fixado na criação e não muda depois). */
export async function atualizarGatilho(
  gatilhoId: number,
  _estadoAnterior: ResultadoAcaoGatilho | null,
  formData: FormData,
): Promise<ResultadoAcaoGatilho> {
  const nome = String(formData.get("nome") ?? "").trim();
  const combinador = formData.get("combinador") as CombinadorCondicoes;
  const ativo = formData.get("ativo") === "on";
  const condicoes = condicoesDoFormData(formData);

  if (!nome || condicoes.length === 0) {
    return { ok: false, erro: "Preencha o nome e adicione ao menos uma condição." };
  }

  const res = await fetch(backendUrl(`/api/gatilhos/${gatilhoId}`), {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ nome, combinador, ativo, condicoes }),
  });

  if (!res.ok) {
    return { ok: false, erro: `Backend respondeu ${res.status}: ${await res.text()}` };
  }

  revalidatePath("/gatilhos");
  return { ok: true };
}

/** Soft-delete (`ativo=false`) — preserva o histórico de alertas já disparados pela regra. */
export async function desativarGatilho(gatilhoId: number): Promise<void> {
  const res = await fetch(backendUrl(`/api/gatilhos/${gatilhoId}`), { method: "DELETE" });
  if (!res.ok) {
    throw new Error(`Backend respondeu ${res.status} ao desativar o gatilho ${gatilhoId}`);
  }
  revalidatePath("/gatilhos");
}
