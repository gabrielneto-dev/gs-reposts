import Link from "next/link";

import { DiaJanelas } from "@/components/dia-janelas";
import { SemanaJanelas } from "@/components/semana-janelas";
import { MesJanelas } from "@/components/mes-janelas";
import { getGradeJanelas } from "@/lib/janelas";
import { addDias, addMeses, dataISO, dataISOParaDate, inicioDoDia } from "@/lib/calendario";

type Visao = "dia" | "semana" | "mes";
const VISOES: Visao[] = ["dia", "semana", "mes"];

function primeiroValor(valor: string | string[] | undefined): string | undefined {
  return Array.isArray(valor) ? valor[0] : valor;
}

const botaoNavClassName =
  "flex h-9 w-9 shrink-0 items-center justify-center rounded-full border border-black/5 bg-white text-zinc-500 transition hover:border-amber-300 hover:text-amber-600";

export default async function JanelasPage({ searchParams }: PageProps<"/janelas">) {
  const params = await searchParams;
  const visaoParam = primeiroValor(params.visao);
  const visao: Visao = VISOES.includes(visaoParam as Visao) ? (visaoParam as Visao) : "dia";
  const dataParam = primeiroValor(params.data);
  const dataBase = dataParam ? dataISOParaDate(dataParam) : inicioDoDia(new Date());

  let inicioIntervalo: Date;
  let fimIntervalo: Date;
  if (visao === "semana") {
    inicioIntervalo = addDias(dataBase, -dataBase.getDay());
    fimIntervalo = addDias(inicioIntervalo, 6);
  } else if (visao === "mes") {
    inicioIntervalo = new Date(dataBase.getFullYear(), dataBase.getMonth(), 1);
    fimIntervalo = new Date(dataBase.getFullYear(), dataBase.getMonth() + 1, 0);
  } else {
    inicioIntervalo = dataBase;
    fimIntervalo = dataBase;
  }

  const grade = await getGradeJanelas(dataISO(inicioIntervalo), dataISO(fimIntervalo));

  function hrefPara(v: Visao, data: Date): string {
    return `/janelas?visao=${v}&data=${dataISO(data)}`;
  }

  function deslocar(direcao: 1 | -1): Date {
    if (visao === "semana") return addDias(dataBase, 7 * direcao);
    if (visao === "mes") return addMeses(dataBase, direcao);
    return addDias(dataBase, direcao);
  }

  return (
    <div className="min-h-full flex-1 bg-zinc-50 px-6 py-10 sm:px-10">
      <div className="mx-auto max-w-5xl space-y-6">
        <header>
          <p className="text-xs font-medium uppercase tracking-wide text-amber-600">GS VoIP</p>
          <h1 className="text-2xl font-semibold text-zinc-900">Janelas de coleta</h1>
          <p className="mt-1 text-sm text-zinc-500">
            Status de cada janela (00h–07h, hora em hora 07h–20h, 20h–00h) e disparo manual pra
            horários que já passaram e não coletaram sozinhos.
          </p>
        </header>

        <div className="flex flex-wrap items-center justify-between gap-4">
          <div className="flex gap-1 rounded-full border border-black/5 bg-white p-1">
            {VISOES.map((v) => (
              <Link
                key={v}
                href={hrefPara(v, dataBase)}
                className={`rounded-full px-4 py-1.5 text-sm font-medium capitalize transition ${
                  visao === v ? "bg-zinc-900 text-white" : "text-zinc-500 hover:text-zinc-900"
                }`}
              >
                {v}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <Link href={hrefPara(visao, deslocar(-1))} aria-label="Anterior" className={botaoNavClassName}>
              ‹
            </Link>
            <Link
              href={hrefPara(visao, inicioDoDia(new Date()))}
              className="rounded-full border border-black/5 bg-white px-4 py-2 text-sm text-zinc-600 transition hover:border-amber-300 hover:text-amber-700"
            >
              Hoje
            </Link>
            <Link href={hrefPara(visao, deslocar(1))} aria-label="Próximo" className={botaoNavClassName}>
              ›
            </Link>
          </div>
        </div>

        {visao === "dia" && <DiaJanelas janelas={grade.dias[0]?.janelas ?? []} />}
        {visao === "semana" && <SemanaJanelas dias={grade.dias} />}
        {visao === "mes" && <MesJanelas mes={dataBase} dias={grade.dias} />}
      </div>
    </div>
  );
}
