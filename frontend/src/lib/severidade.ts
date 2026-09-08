export type SeveridadeGatilho = "atencao" | "medio" | "critico" | "urgente";

export const SEVERIDADES: { value: SeveridadeGatilho; label: string }[] = [
  { value: "atencao", label: "Atenção" },
  { value: "medio", label: "Médio" },
  { value: "critico", label: "Crítico" },
  { value: "urgente", label: "Urgente" },
];

export const SEVERIDADE_LABEL: Record<SeveridadeGatilho, string> = {
  atencao: "Atenção",
  medio: "Médio",
  critico: "Crítico",
  urgente: "Urgente",
};

/** Classes de pílula (fundo + texto) por severidade — mesma escala de cor em toda a UI. */
export const SEVERIDADE_PILULA: Record<SeveridadeGatilho, string> = {
  atencao: "bg-amber-100 text-amber-700",
  medio: "bg-orange-100 text-orange-700",
  critico: "bg-orange-200 text-orange-900",
  urgente: "bg-rose-100 text-rose-700",
};

/** Cor sólida (fundo) por severidade — usada no ponto/badge da tabela de clientes. */
export const SEVERIDADE_PONTO: Record<SeveridadeGatilho, string> = {
  atencao: "bg-amber-500",
  medio: "bg-orange-500",
  critico: "bg-orange-700",
  urgente: "bg-rose-600",
};
