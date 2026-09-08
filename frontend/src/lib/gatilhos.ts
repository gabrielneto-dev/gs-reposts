import { backendUrl } from "./backend";

export type CombinadorCondicoes = "e" | "ou";
export type MetricaGatilho = "asr_percentual" | "acd_segundos" | "pdd_medio_segundos";
export type PeriodoReferenciaGatilho = "media_ontem" | "media_semanal" | "media_mensal";
export type DirecaoGatilho = "aumento" | "queda" | "qualquer";

export type CondicaoGatilho = {
  id: number;
  metrica: MetricaGatilho;
  periodo_referencia: PeriodoReferenciaGatilho;
  direcao: DirecaoGatilho;
  percentual_limite: number;
};

export type Gatilho = {
  id: number;
  nome: string;
  cliente_id: number | null;
  combinador: CombinadorCondicoes;
  ativo: boolean;
  criado_em: string;
  atualizado_em: string;
  condicoes: CondicaoGatilho[];
};

export type GatilhosResponse = {
  registros: number;
  gatilhos: Gatilho[];
};

/**
 * Lê do backend/ as regras de gatilho — globais sempre incluídas; passando `clienteId` soma as
 * individuais daquele cliente. Chamado sempre do servidor (Server Component).
 */
export async function getGatilhos(clienteId?: number): Promise<GatilhosResponse> {
  const params = new URLSearchParams();
  if (clienteId !== undefined) params.set("cliente_id", String(clienteId));

  const res = await fetch(backendUrl(`/api/gatilhos?${params.toString()}`), { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Backend respondeu ${res.status} ao buscar /api/gatilhos`);
  }
  return (await res.json()) as GatilhosResponse;
}
