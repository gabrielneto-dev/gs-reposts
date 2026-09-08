import { backendUrl } from "./backend";

export type CondicaoAvaliada = {
  metrica: string;
  periodo_referencia: string;
  direcao: string;
  percentual_limite: number;
  atual: number | null;
  referencia: number | null;
  percentual_variacao: number | null;
  bateu: boolean;
};

export type AlertaDisparado = {
  id: number;
  gatilho_id: number;
  gatilho_nome: string;
  cliente_id: number;
  cliente_nome: string | null;
  janela_id: number;
  inicio_janela: string;
  fim_janela: string;
  metricas_avaliadas: CondicaoAvaliada[];
  disparado_em: string;
  visto: boolean;
  visto_em: string | null;
};

export type AlertasResponse = {
  registros: number;
  alertas: AlertaDisparado[];
};

export type ClienteComAlertaNaoVisto = {
  cliente_id: number;
  ultimo_alerta_nao_visto_em: string;
};

export type AlertasNaoVistosResponse = {
  alertas: ClienteComAlertaNaoVisto[];
};

/** Histórico de alertas disparados — central de alertas. Chamado sempre do servidor. */
export async function getAlertas(
  filtros: { clienteId?: number; gatilhoId?: number; visto?: boolean; dataInicio?: string; dataFim?: string } = {},
): Promise<AlertasResponse> {
  const params = new URLSearchParams({ limit: "500" });
  if (filtros.clienteId !== undefined) params.set("cliente_id", String(filtros.clienteId));
  if (filtros.gatilhoId !== undefined) params.set("gatilho_id", String(filtros.gatilhoId));
  if (filtros.visto !== undefined) params.set("visto", String(filtros.visto));
  if (filtros.dataInicio) params.set("data_inicio", filtros.dataInicio);
  if (filtros.dataFim) params.set("data_fim", filtros.dataFim);

  const res = await fetch(backendUrl(`/api/alertas?${params.toString()}`), { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Backend respondeu ${res.status} ao buscar /api/alertas`);
  }
  return (await res.json()) as AlertasResponse;
}

/** Retorno leve (cliente_id + disparo não visto mais recente) pra alimentar o badge da tabela de
 * clientes — sem limite de tempo, um alerta só some daqui quando alguém marcar como visto. */
export async function getAlertasNaoVistos(): Promise<AlertasNaoVistosResponse> {
  const res = await fetch(backendUrl("/api/alertas/nao-vistos"), { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Backend respondeu ${res.status} ao buscar /api/alertas/nao-vistos`);
  }
  return (await res.json()) as AlertasNaoVistosResponse;
}
