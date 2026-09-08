"use client";

import { useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

const NOMES_MES = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];
const DIAS_SEMANA = ["D", "S", "T", "Q", "Q", "S", "S"];

const pad = (n: number) => String(n).padStart(2, "0");

function inicioDoDia(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

function mesmoDia(a: Date | null, b: Date | null): boolean {
  return (
    !!a && !!b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
  );
}

function addMeses(mes: Date, n: number): Date {
  return new Date(mes.getFullYear(), mes.getMonth() + n, 1);
}

function addDias(d: Date, n: number): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
}

/** Datetime-local ("2026-09-08T09:00") -> Date, sem passar pelo parser de fuso do JS. */
function datetimeLocalParaDate(s: string): Date {
  const [dataParte, horaParte] = s.split("T");
  const [ano, mes, dia] = dataParte.split("-").map(Number);
  const [h, min] = (horaParte ?? "00:00").split(":").map(Number);
  return new Date(ano, mes - 1, dia, h, min);
}

function dateParaDatetimeLocal(dia: Date, hora: string): string {
  return `${dia.getFullYear()}-${pad(dia.getMonth() + 1)}-${pad(dia.getDate())}T${hora}`;
}

function horaDe(d: Date): string {
  return `${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

function gerarCelulasDoMes(mes: Date): (Date | null)[] {
  const ano = mes.getFullYear();
  const mesIndex = mes.getMonth();
  const primeiroDiaSemana = new Date(ano, mesIndex, 1).getDay();
  const totalDias = new Date(ano, mesIndex + 1, 0).getDate();

  const celulas: (Date | null)[] = [];
  for (let i = 0; i < primeiroDiaSemana; i++) celulas.push(null);
  for (let dia = 1; dia <= totalDias; dia++) celulas.push(new Date(ano, mesIndex, dia));
  return celulas;
}

const botaoNavClassName =
  "flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-black/5 bg-white text-zinc-500 transition hover:border-amber-300 hover:text-amber-600 disabled:pointer-events-none disabled:opacity-40";

const PRESETS: { rotulo: string; calcular: () => { inicio: Date; fim: Date } }[] = [
  { rotulo: "Hoje", calcular: () => ({ inicio: inicioDoDia(new Date()), fim: addDias(inicioDoDia(new Date()), 1) }) },
  {
    rotulo: "Ontem",
    calcular: () => ({ inicio: addDias(inicioDoDia(new Date()), -1), fim: inicioDoDia(new Date()) }),
  },
  { rotulo: "Últimas 24h", calcular: () => ({ inicio: new Date(Date.now() - 24 * 60 * 60 * 1000), fim: new Date() }) },
  {
    rotulo: "Esta semana",
    calcular: () => ({ inicio: addDias(inicioDoDia(new Date()), -new Date().getDay()), fim: new Date() }),
  },
  {
    rotulo: "Este mês",
    calcular: () => ({ inicio: new Date(new Date().getFullYear(), new Date().getMonth(), 1), fim: new Date() }),
  },
];

function GradeMes({
  mes,
  selInicio,
  selFim,
  hoverPreview,
  onClickDia,
  onHoverDia,
}: {
  mes: Date;
  selInicio: Date | null;
  selFim: Date | null;
  hoverPreview: Date | null;
  onClickDia: (dia: Date) => void;
  onHoverDia: (dia: Date) => void;
}) {
  const celulas = gerarCelulasDoMes(mes);
  const fimEfetivo = selFim ?? hoverPreview;

  return (
    <div className="w-full min-w-[260px]">
      <p className="mb-3 text-center text-sm font-semibold text-zinc-900">
        {NOMES_MES[mes.getMonth()]} de {mes.getFullYear()}
      </p>
      <div className="grid grid-cols-7 text-center text-xs font-medium text-zinc-400">
        {DIAS_SEMANA.map((d, i) => (
          <div key={i} className="py-1">
            {d}
          </div>
        ))}
        {celulas.map((dia, i) => {
          if (!dia) return <div key={i} className="h-10 w-10" />;

          const ehEndpoint = mesmoDia(dia, selInicio) || mesmoDia(dia, selFim);
          const emBanda = !!selInicio && !!fimEfetivo && dia >= selInicio && dia <= fimEfetivo;
          const beiraEsquerda = mesmoDia(dia, selInicio);
          const beiraDireita = mesmoDia(dia, fimEfetivo);

          return (
            <button
              key={i}
              type="button"
              onClick={() => onClickDia(dia)}
              onMouseEnter={() => onHoverDia(dia)}
              className={[
                "h-10 w-10 text-sm transition",
                emBanda ? "bg-amber-50" : "",
                beiraEsquerda ? "rounded-l-full" : "",
                beiraDireita ? "rounded-r-full" : "",
              ].join(" ")}
            >
              <span
                className={[
                  "flex h-full w-full items-center justify-center rounded-full",
                  ehEndpoint ? "bg-zinc-900 font-medium text-white" : "text-zinc-700 hover:bg-zinc-200",
                ].join(" ")}
              >
                {dia.getDate()}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Filtro de período com hora (inicio/fim), no estilo do seletor de datas do Airbnb: pill de
 * gatilho + painel com dois meses lado a lado, seleção por clique (primeiro clique = início,
 * segundo = fim, com preview do intervalo no hover). Hora de cada ponta é um campo separado, já
 * que o padrão do Airbnb não tem — só data. "‹"/"›" fora do painel deslocam o período pela
 * própria duração (ex: 12:00-13:00 -> 13:00-14:00), como antes.
 */
export function DateRangeFilter({ inicio, fim }: { inicio: string; fim: string }) {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);

  const [aberto, setAberto] = useState(false);
  const [mesVisivel, setMesVisivel] = useState(() => inicioDoDia(datetimeLocalParaDate(inicio)));
  const [selInicio, setSelInicio] = useState<Date | null>(null);
  const [selFim, setSelFim] = useState<Date | null>(null);
  const [horaInicio, setHoraInicio] = useState("00:00");
  const [horaFim, setHoraFim] = useState("00:00");
  const [hoverPreview, setHoverPreview] = useState<Date | null>(null);

  useEffect(() => {
    if (!aberto) return;

    function aoClicarFora(evento: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(evento.target as Node)) {
        setAberto(false);
      }
    }
    function aoTeclar(evento: KeyboardEvent) {
      if (evento.key === "Escape") setAberto(false);
    }

    document.addEventListener("mousedown", aoClicarFora);
    document.addEventListener("keydown", aoTeclar);
    return () => {
      document.removeEventListener("mousedown", aoClicarFora);
      document.removeEventListener("keydown", aoTeclar);
    };
  }, [aberto]);

  function navegar(novoInicio: string, novoFim: string) {
    const params = new URLSearchParams({ inicio: novoInicio, fim: novoFim });
    router.push(`/?${params.toString()}`);
  }

  function deslocar(direcao: 1 | -1) {
    const dtInicio = datetimeLocalParaDate(inicio);
    const dtFim = datetimeLocalParaDate(fim);
    const duracaoMs = dtFim.getTime() - dtInicio.getTime();
    if (duracaoMs <= 0) return;

    const novoInicio = new Date(dtInicio.getTime() + direcao * duracaoMs);
    const novoFim = new Date(dtFim.getTime() + direcao * duracaoMs);
    navegar(dateParaDatetimeLocal(novoInicio, horaDe(novoInicio)), dateParaDatetimeLocal(novoFim, horaDe(novoFim)));
  }

  function abrirPopover() {
    const dtInicio = datetimeLocalParaDate(inicio);
    const dtFim = datetimeLocalParaDate(fim);
    setSelInicio(inicioDoDia(dtInicio));
    setSelFim(inicioDoDia(dtFim));
    setHoraInicio(horaDe(dtInicio));
    setHoraFim(horaDe(dtFim));
    setMesVisivel(inicioDoDia(dtInicio));
    setAberto(true);
  }

  function aoClicarDia(dia: Date) {
    if (!selInicio || selFim) {
      setSelInicio(dia);
      setSelFim(null);
      return;
    }
    if (dia < selInicio) {
      setSelInicio(dia);
      setSelFim(null);
      return;
    }
    setSelFim(dia);
  }

  const podeAplicar =
    !!selInicio && !!selFim && dateParaDatetimeLocal(selInicio, horaInicio) < dateParaDatetimeLocal(selFim, horaFim);

  function aplicar() {
    if (!selInicio || !selFim) return;
    navegar(dateParaDatetimeLocal(selInicio, horaInicio), dateParaDatetimeLocal(selFim, horaFim));
    setAberto(false);
  }

  function aplicarPreset(calcular: () => { inicio: Date; fim: Date }) {
    const { inicio: novoInicio, fim: novoFim } = calcular();
    navegar(dateParaDatetimeLocal(novoInicio, horaDe(novoInicio)), dateParaDatetimeLocal(novoFim, horaDe(novoFim)));
    setAberto(false);
  }

  const dtInicioAplicado = datetimeLocalParaDate(inicio);
  const dtFimAplicado = datetimeLocalParaDate(fim);
  const rotuloPill = `${pad(dtInicioAplicado.getDate())}/${pad(dtInicioAplicado.getMonth() + 1)} ${horaDe(dtInicioAplicado)} – ${pad(dtFimAplicado.getDate())}/${pad(dtFimAplicado.getMonth() + 1)} ${horaDe(dtFimAplicado)}`;

  return (
    <div className="relative flex items-center gap-3" ref={containerRef}>
      <button
        type="button"
        onClick={() => deslocar(-1)}
        aria-label="Período anterior"
        title="Período anterior"
        className={botaoNavClassName}
      >
        ‹
      </button>

      <button
        type="button"
        onClick={() => (aberto ? setAberto(false) : abrirPopover())}
        className="flex items-center gap-2 rounded-full border border-black/5 bg-zinc-50 px-4 py-2 text-sm text-zinc-800 outline-none transition hover:border-amber-300 hover:bg-white"
      >
        <CalendarioIcon className="h-4 w-4 text-zinc-400" />
        {rotuloPill}
      </button>

      <button
        type="button"
        onClick={() => deslocar(1)}
        aria-label="Próximo período"
        title="Próximo período"
        className={botaoNavClassName}
      >
        ›
      </button>

      {aberto && (
        <div className="absolute right-0 top-full z-50 mt-2 w-max max-w-[95vw] overflow-x-auto rounded-3xl border border-black/5 bg-white p-6 shadow-xl shadow-black/10">
          <div className="flex items-center gap-4">
            <button
              type="button"
              onClick={() => setMesVisivel((m) => addMeses(m, -1))}
              aria-label="Mês anterior"
              className={botaoNavClassName}
            >
              ‹
            </button>

            <div className="flex gap-8">
              <GradeMes
                mes={mesVisivel}
                selInicio={selInicio}
                selFim={selFim}
                hoverPreview={hoverPreview}
                onClickDia={aoClicarDia}
                onHoverDia={setHoverPreview}
              />
              <GradeMes
                mes={addMeses(mesVisivel, 1)}
                selInicio={selInicio}
                selFim={selFim}
                hoverPreview={hoverPreview}
                onClickDia={aoClicarDia}
                onHoverDia={setHoverPreview}
              />
            </div>

            <button
              type="button"
              onClick={() => setMesVisivel((m) => addMeses(m, 1))}
              aria-label="Próximo mês"
              className={botaoNavClassName}
            >
              ›
            </button>
          </div>

          <div className="mt-5 flex flex-wrap items-center gap-6 border-t border-black/5 pt-4">
            <span className="flex items-center gap-2">
              <label htmlFor="hora-inicio-filtro" className="text-sm text-zinc-500">
                Hora inicial
              </label>
              <input
                id="hora-inicio-filtro"
                type="time"
                value={horaInicio}
                onChange={(evento) => setHoraInicio(evento.target.value)}
                className="rounded-full border border-black/5 bg-zinc-50 px-3 py-1.5 text-sm text-zinc-800 outline-none focus:border-amber-300 focus:bg-white focus:ring-2 focus:ring-amber-100"
              />
            </span>
            <span className="flex items-center gap-2">
              <label htmlFor="hora-fim-filtro" className="text-sm text-zinc-500">
                Hora final
              </label>
              <input
                id="hora-fim-filtro"
                type="time"
                value={horaFim}
                onChange={(evento) => setHoraFim(evento.target.value)}
                className="rounded-full border border-black/5 bg-zinc-50 px-3 py-1.5 text-sm text-zinc-800 outline-none focus:border-amber-300 focus:bg-white focus:ring-2 focus:ring-amber-100"
              />
            </span>
          </div>

          <div className="mt-4 flex flex-wrap gap-2 border-t border-black/5 pt-4">
            {PRESETS.map((preset) => (
              <button
                key={preset.rotulo}
                type="button"
                onClick={() => aplicarPreset(preset.calcular)}
                className="rounded-full border border-black/5 px-3 py-1.5 text-sm text-zinc-600 transition hover:border-amber-300 hover:text-amber-600"
              >
                {preset.rotulo}
              </button>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-end gap-3 border-t border-black/5 pt-4">
            <button
              type="button"
              onClick={() => setAberto(false)}
              className="text-sm font-medium text-zinc-500 underline-offset-2 hover:underline"
            >
              Cancelar
            </button>
            <button
              type="button"
              onClick={aplicar}
              disabled={!podeAplicar}
              className="rounded-full bg-zinc-900 px-5 py-2 text-sm font-medium text-white transition hover:bg-zinc-700 disabled:pointer-events-none disabled:opacity-40"
            >
              Aplicar
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function CalendarioIcon({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 20 20" fill="none" className={className} aria-hidden="true">
      <rect x="3" y="4" width="14" height="13" rx="2" stroke="currentColor" strokeWidth="1.5" />
      <path d="M3 8h14M7 2.5v3M13 2.5v3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}
