import type { ComponentType, SVGProps } from "react";

export type ItemNav = {
  href: string;
  label: string;
};

export type SecaoNav = {
  titulo?: string;
  itens: ItemNav[];
};

export type Ferramenta = {
  id: string;
  label: string;
  /** Ícone do rail — só ele aparece na barra estreita; o nome completo vai no tooltip/painel. */
  Icone: ComponentType<SVGProps<SVGSVGElement>>;
  secoes: SecaoNav[];
};

function IconeMonitoramento(props: SVGProps<SVGSVGElement>) {
  return (
    <svg viewBox="0 0 20 20" fill="none" {...props}>
      <path
        d="M3 15.5v-3l4-4 3 3 6-6"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M12.5 5.5H16v3.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M3 17.5h14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}

/**
 * Navegação por ferramenta: cada `Ferramenta` é um ícone no rail (a barra estreita mais à
 * esquerda); o painel ao lado mostra as seções/páginas daquela ferramenta. Uma ferramenta nova
 * (ex.: outro produto/monitoramento além do de clientes) é só uma entrada nova nesse array — o
 * rail e o painel se adaptam sozinhos.
 */
export const FERRAMENTAS: Ferramenta[] = [
  {
    id: "monitoramento-clientes",
    label: "Monitoramento de Clientes",
    Icone: IconeMonitoramento,
    secoes: [
      { itens: [{ href: "/relatorios", label: "Relatórios" }] },
      {
        titulo: "Alertas",
        itens: [
          { href: "/gatilhos", label: "Gatilhos" },
          { href: "/alertas", label: "Central de alertas" },
        ],
      },
      {
        titulo: "Coleta",
        itens: [{ href: "/janelas", label: "Janelas de coleta" }],
      },
    ],
  },
];

/** Acha a ferramenta dona de um caminho — usado pra saber qual ícone do rail fica ativo. */
export function ferramentaDoCaminho(pathname: string): Ferramenta | undefined {
  return FERRAMENTAS.find((f) => f.secoes.some((s) => s.itens.some((i) => i.href === pathname)));
}
