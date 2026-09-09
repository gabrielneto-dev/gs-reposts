import { backendUrl } from "./backend";

export type SituacaoSlot = "em_andamento" | "concluida" | "falhou" | "parcial" | "faltando" | "futuro";

export type SlotJanela = {
  inicio_janela: string;
  fim_janela: string;
  situacao: SituacaoSlot;
  janela_id: number | null;
  clientes_descobertos: number | null;
  clientes_processados: number | null;
  mensagem_erro: string | null;
  pode_disparar: boolean;
};

export type DiaGrade = {
  data: string;
  janelas: SlotJanela[];
};

export type GradeJanelasResponse = {
  dias: DiaGrade[];
};

export const SITUACAO_LABEL: Record<SituacaoSlot, string> = {
  em_andamento: "Em andamento",
  concluida: "Concluída",
  falhou: "Falhou",
  parcial: "Parcial",
  faltando: "Faltando",
  futuro: "Futuro",
};

/** Pílula (fundo + texto) por situação — usada nas 3 visões. */
export const SITUACAO_PILULA: Record<SituacaoSlot, string> = {
  em_andamento: "bg-sky-100 text-sky-700",
  concluida: "bg-emerald-100 text-emerald-700",
  falhou: "bg-rose-100 text-rose-700",
  parcial: "bg-amber-100 text-amber-700",
  faltando: "border border-dashed border-zinc-300 bg-zinc-50 text-zinc-500",
  futuro: "bg-zinc-50 text-zinc-300",
};

/** Cor sólida (fundo) por situação — usada nas células compactas da visão de semana/mês. */
export const SITUACAO_COR = {
  em_andamento: "bg-sky-400",
  concluida: "bg-emerald-400",
  falhou: "bg-rose-400",
  parcial: "bg-amber-400",
  faltando: "bg-zinc-300",
  futuro: "bg-zinc-100",
} satisfies Record<SituacaoSlot, string>;

/** Os 15 slots canônicos de cada dia do intervalo, já cruzados com o que existe no banco —
 * inclui `faltando`/`futuro` sintéticos pra slots sem `Janela`. Chamado sempre do servidor. */
export async function getGradeJanelas(dataInicio: string, dataFim: string): Promise<GradeJanelasResponse> {
  const params = new URLSearchParams({ data_inicio: dataInicio, data_fim: dataFim });
  const res = await fetch(backendUrl(`/api/metricas/janelas/grade?${params.toString()}`), { cache: "no-store" });
  if (!res.ok) {
    throw new Error(`Backend respondeu ${res.status} ao buscar /api/metricas/janelas/grade`);
  }
  return (await res.json()) as GradeJanelasResponse;
}
