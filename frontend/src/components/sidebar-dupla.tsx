"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { FERRAMENTAS, ferramentaDoCaminho } from "@/lib/navegacao";

export function SidebarDupla() {
  const pathname = usePathname();
  const ferramentaAtiva = ferramentaDoCaminho(pathname) ?? FERRAMENTAS[0];

  const paginaAtiva = ferramentaAtiva.secoes
    .flatMap((s) => s.itens)
    .find((i) => i.href === pathname);

  return (
    <div className="flex h-full shrink-0">
      {/* Rail: um ícone por ferramenta. Só uma hoje — o array cresce sozinho quando entrar a
          próxima ferramenta, sem mexer em nada aqui. */}
      <nav className="flex w-16 shrink-0 flex-col items-center gap-2 bg-zinc-950 py-4">
        <Link
          href="/"
          className="mb-2 flex h-9 w-9 items-center justify-center rounded-xl bg-amber-500 text-sm font-bold text-zinc-950"
          title="GS VoIP"
        >
          G
        </Link>
        {FERRAMENTAS.map((ferramenta) => {
          const ativa = ferramenta.id === ferramentaAtiva.id;
          return (
            <Link
              key={ferramenta.id}
              href={ferramenta.secoes[0].itens[0].href}
              title={ferramenta.label}
              className={`flex h-11 w-11 items-center justify-center rounded-xl transition ${
                ativa ? "bg-amber-500/15 text-amber-400" : "text-zinc-500 hover:bg-white/5 hover:text-zinc-300"
              }`}
            >
              <ferramenta.Icone className="h-5 w-5" />
            </Link>
          );
        })}
      </nav>

      {/* Painel: seções/páginas da ferramenta ativa. */}
      <div className="flex w-64 shrink-0 flex-col bg-zinc-900">
        <div className="border-b border-white/5 px-5 py-4">
          <p className="truncate text-xs text-zinc-500">
            {ferramentaAtiva.label}
            {paginaAtiva ? ` / ${paginaAtiva.label}` : ""}
          </p>
        </div>

        <div className="flex-1 space-y-5 overflow-y-auto px-3 py-4">
          {ferramentaAtiva.secoes.map((secao, indice) => (
            <div key={indice}>
              {secao.titulo && (
                <p className="mb-1.5 px-3 text-xs font-medium uppercase tracking-wide text-zinc-500">
                  {secao.titulo}
                </p>
              )}
              <div className="space-y-0.5">
                {secao.itens.map((item) => {
                  const ativo = item.href === pathname;
                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`block rounded-lg px-3 py-2 text-sm transition ${
                        ativo ? "bg-amber-500/15 font-medium text-amber-400" : "text-zinc-300 hover:bg-white/5"
                      }`}
                    >
                      {item.label}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
