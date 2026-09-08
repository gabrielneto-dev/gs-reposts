export type ClienteResumo = {
  cliente_id: number;
  nome: string | null;
  inicio_janela: string;
  fim_janela: string;
  total_atendidas: number;
  total_falhas: number;
  asr_percentual: number;
  acd_segundos: number | null;
  pdd_medio_segundos: number | null;
  volume_periodo: number;
};

export type ClientesResumoResponse = {
  inicio: string;
  fim: string;
  registros: number;
  clientes: ClienteResumo[];
};

function backendUrl(path: string): string {
  const base = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";
  return `${base}${path}`;
}

/**
 * Le do backend/ (metrics-pipeline) o snapshot de cada cliente coletado pelo scheduler no período
 * informado (default: hoje inteiro, resolvido pelo backend). `inicio`/`fim` são datetimes locais
 * (ex: "2026-09-08T09:00", sem timezone — o backend assume o fuso operacional do sistema). Chamado
 * sempre do servidor (Server Component) — nunca exposto ao navegador.
 */
export async function getClientesResumo(inicio?: string, fim?: string): Promise<ClientesResumoResponse> {
  const params = new URLSearchParams({ limit: "1000" });
  if (inicio) params.set("inicio", inicio);
  if (fim) params.set("fim", fim);

  const res = await fetch(backendUrl(`/api/metricas/clientes?${params.toString()}`), {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Backend respondeu ${res.status} ao buscar /api/metricas/clientes`);
  }

  return (await res.json()) as ClientesResumoResponse;
}

/**
 * Converte o datetime com offset que o backend devolve (ex: "2026-09-08T00:00:00-03:00") pro
 * formato que <input type="datetime-local"> aceita como defaultValue ("2026-09-08T00:00"). Os
 * primeiros 16 caracteres já SÃO a hora local (o offset só marca qual fuso é esse), então é um
 * corte de string, não uma conversão de fuso.
 */
export function paraDatetimeLocal(isoComOffset: string): string {
  return isoComOffset.slice(0, 16);
}
