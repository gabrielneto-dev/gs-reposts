"use client";

import { useMemo, useState } from "react";
import type { ClienteResumo } from "@/lib/backend";

type SortKey = "nome" | "asr" | "acd" | "pdd" | "volume" | "coleta";
type SortDirection = "asc" | "desc";

const AVATAR_COLORS = [
  "bg-amber-100 text-amber-700",
  "bg-rose-100 text-rose-700",
  "bg-sky-100 text-sky-700",
  "bg-emerald-100 text-emerald-700",
  "bg-violet-100 text-violet-700",
  "bg-orange-100 text-orange-700",
];

function iniciais(nome: string | null, clienteId: number): string {
  if (!nome) return String(clienteId).slice(0, 2);
  // Só considera "palavras" que comecam com letra - ignora hifens, "&", etc. soltos no meio do nome.
  const partes = nome
    .trim()
    .split(/\s+/)
    .filter((p) => /^\p{L}/u.test(p));
  const letras =
    partes.length >= 2 ? partes[0][0] + partes[1][0] : (partes[0]?.slice(0, 2) ?? "?");
  return letras.toUpperCase();
}

function corAvatar(clienteId: number): string {
  return AVATAR_COLORS[clienteId % AVATAR_COLORS.length];
}

function formatarSegundos(valor: number | null): string {
  if (valor === null) return "—";
  return `${valor.toFixed(valor < 10 ? 2 : 1)}s`;
}

function formatarAsr(valor: number): string {
  return `${valor.toFixed(1)}%`;
}

const formatadorData = new Intl.DateTimeFormat("pt-BR", {
  timeZone: "America/Sao_Paulo",
  day: "2-digit",
  month: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
});

function formatarColeta(windowEndIso: string): string {
  return formatadorData.format(new Date(windowEndIso));
}

export function ClientesTable({ clientes }: { clientes: ClienteResumo[] }) {
  const [busca, setBusca] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("nome");
  const [sortDir, setSortDir] = useState<SortDirection>("asc");

  const filtrados = useMemo(() => {
    const termo = busca.trim().toLowerCase();
    const base = termo
      ? clientes.filter(
          (c) =>
            c.nome?.toLowerCase().includes(termo) || String(c.cliente_id).includes(termo),
        )
      : clientes;

    const dir = sortDir === "asc" ? 1 : -1;

    return [...base].sort((a, b) => {
      switch (sortKey) {
        case "nome":
          return (a.nome ?? "").localeCompare(b.nome ?? "") * dir;
        case "asr":
          return (a.asr_percentual - b.asr_percentual) * dir;
        case "acd":
          return ((a.acd_segundos ?? -1) - (b.acd_segundos ?? -1)) * dir;
        case "pdd":
          return ((a.pdd_medio_segundos ?? -1) - (b.pdd_medio_segundos ?? -1)) * dir;
        case "volume":
          return (a.volume_dia - b.volume_dia) * dir;
        case "coleta":
          return (
            (new Date(a.fim_janela).getTime() - new Date(b.fim_janela).getTime()) * dir
          );
        default:
          return 0;
      }
    });
  }, [clientes, busca, sortKey, sortDir]);

  function alternarOrdenacao(chave: SortKey) {
    if (chave === sortKey) {
      setSortDir((atual) => (atual === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(chave);
      setSortDir("asc");
    }
  }

  return (
    <div className="rounded-3xl border border-black/5 bg-white shadow-sm shadow-black/[0.03]">
      <div className="flex flex-col gap-4 border-b border-black/5 p-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-zinc-900">Clientes</h2>
          <p className="text-sm text-zinc-500">
            {filtrados.length} de {clientes.length} clientes com coleta registrada
          </p>
        </div>
        <div className="relative w-full sm:w-72">
          <SearchIcon className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-400" />
          <input
            value={busca}
            onChange={(e) => setBusca(e.target.value)}
            placeholder="Buscar por nome ou ID..."
            className="w-full rounded-full border border-black/5 bg-zinc-50 py-2.5 pl-10 pr-4 text-sm text-zinc-800 outline-none transition placeholder:text-zinc-400 focus:border-amber-300 focus:bg-white focus:ring-2 focus:ring-amber-100"
          />
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[720px] border-collapse text-sm">
          <thead>
            <tr className="text-left text-xs font-medium uppercase tracking-wide text-zinc-400">
              <Th
                label="Cliente"
                onClick={() => alternarOrdenacao("nome")}
                active={sortKey === "nome"}
                dir={sortDir}
                className="pl-6"
              />
              <Th
                label="Volume (hoje)"
                onClick={() => alternarOrdenacao("volume")}
                active={sortKey === "volume"}
                dir={sortDir}
              />
              <Th
                label="ASR (200 OK)"
                onClick={() => alternarOrdenacao("asr")}
                active={sortKey === "asr"}
                dir={sortDir}
              />
              <Th
                label="ACD"
                onClick={() => alternarOrdenacao("acd")}
                active={sortKey === "acd"}
                dir={sortDir}
              />
              <Th
                label="PDD"
                onClick={() => alternarOrdenacao("pdd")}
                active={sortKey === "pdd"}
                dir={sortDir}
              />
              <Th
                label="Última coleta"
                onClick={() => alternarOrdenacao("coleta")}
                active={sortKey === "coleta"}
                dir={sortDir}
                className="pr-6"
              />
            </tr>
          </thead>
          <tbody className="divide-y divide-black/5">
            {filtrados.map((cliente) => {
              return (
                <tr key={cliente.cliente_id} className="transition-colors hover:bg-amber-50/40">
                  <td className="py-3 pl-6 pr-4">
                    <div className="flex items-center gap-3">
                      <span
                        className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${corAvatar(
                          cliente.cliente_id,
                        )}`}
                      >
                        {iniciais(cliente.nome, cliente.cliente_id)}
                      </span>
                      <div className="min-w-0">
                        <p
                          className="truncate font-medium text-zinc-900"
                          title={cliente.nome ?? undefined}
                        >
                          {cliente.nome ?? `Cliente ${cliente.cliente_id}`}
                        </p>
                        <p className="text-xs text-zinc-400">ID {cliente.cliente_id}</p>
                      </div>
                    </div>
                  </td>
                  <td className="py-3 pr-4 text-zinc-600">
                    {cliente.volume_dia.toLocaleString("pt-BR")}
                  </td>
                  <td className="py-3 pr-4">
                    <span className="font-medium text-zinc-900">
                      {formatarAsr(cliente.asr_percentual)}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-zinc-600">
                    {formatarSegundos(cliente.acd_segundos)}
                  </td>
                  <td className="py-3 pr-4 text-zinc-600">
                    {formatarSegundos(cliente.pdd_medio_segundos)}
                  </td>
                  <td className="py-3 pr-6 text-zinc-500">{formatarColeta(cliente.fim_janela)}</td>
                </tr>
              );
            })}
          </tbody>
        </table>

        {filtrados.length === 0 && (
          <p className="px-6 py-10 text-center text-sm text-zinc-400">
            Nenhum cliente encontrado para &quot;{busca}&quot;.
          </p>
        )}
      </div>
    </div>
  );
}

function Th({
  label,
  onClick,
  active,
  dir,
  className = "",
}: {
  label: string;
  onClick: () => void;
  active: boolean;
  dir: SortDirection;
  className?: string;
}) {
  return (
    <th className={`py-3 font-medium ${className}`}>
      <button
        type="button"
        onClick={onClick}
        className={`inline-flex items-center gap-1 transition-colors hover:text-zinc-700 ${
          active ? "text-zinc-700" : ""
        }`}
      >
        {label}
        <span
          className={`text-[10px] transition-transform ${
            active && dir === "desc" ? "rotate-180" : ""
          }`}
        >
          ▾
        </span>
      </button>
    </th>
  );
}

function SearchIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <path
        d="M9 16a7 7 0 1 1 0-14 7 7 0 0 1 0 14Zm9 2-4.35-4.35"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
