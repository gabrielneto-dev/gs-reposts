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
  volume_dia: number;
};

type ClientesResumoResponse = {
  registros: number;
  clientes: ClienteResumo[];
};

function backendUrl(path: string): string {
  const base = process.env.BACKEND_API_URL ?? "http://127.0.0.1:8000";
  return `${base}${path}`;
}

/**
 * Le do backend/ (metrics-pipeline) o snapshot mais recente de cada cliente ja coletado pelo
 * scheduler. Chamado sempre do servidor (Server Component) — nunca exposto ao navegador.
 */
export async function getClientesResumo(): Promise<ClienteResumo[]> {
  const res = await fetch(backendUrl("/api/metricas/clientes?limit=1000"), {
    cache: "no-store",
  });

  if (!res.ok) {
    throw new Error(`Backend respondeu ${res.status} ao buscar /api/metricas/clientes`);
  }

  const data = (await res.json()) as ClientesResumoResponse;
  return data.clientes;
}
