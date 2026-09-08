import { EventEmitter } from "node:events";

export const METRICAS_ATUALIZADAS_EVENT = "metricas-atualizadas";
export const ALERTAS_DISPARADOS_EVENT = "alertas-disparados";

export type MetricasAtualizadasPayload = {
  janela_id: number;
  inicio_janela: string;
  fim_janela: string;
  situacao: string;
  clientes_descobertos: number;
  clientes_processados: number;
};

export type AlertaDisparadoPayload = {
  alerta_id: number;
  gatilho_id: number;
  gatilho_nome: string | null;
  cliente_id: number;
  cliente_nome: string | null;
  janela_id: number;
  metricas_avaliadas: unknown[];
  disparado_em: string;
};

export type AlertasDisparadosPayload = {
  alertas: AlertaDisparadoPayload[];
};

/**
 * Barramento em memória, vivo enquanto o processo do Next.js estiver de pé: o Route Handler do
 * webhook emite aqui, o Route Handler de SSE escuta aqui e repassa pro navegador. Não sobrevive a
 * múltiplas instâncias do servidor — suficiente pro deployment single-instance atual.
 */
export const metricasEventBus = new EventEmitter();
metricasEventBus.setMaxListeners(0);
