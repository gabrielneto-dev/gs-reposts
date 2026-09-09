import Link from "next/link";

import { DIAS_SEMANA, dataISO, gerarCelulasDoMes, mesmoDia } from "@/lib/calendario";
import { SITUACAO_COR, type DiaGrade, type SituacaoSlot } from "@/lib/janelas";

function resumo(janelas: DiaGrade["janelas"]): Partial<Record<SituacaoSlot, number>> {
  const contagem: Partial<Record<SituacaoSlot, number>> = {};
  for (const slot of janelas) {
    contagem[slot.situacao] = (contagem[slot.situacao] ?? 0) + 1;
  }
  return contagem;
}

const ORDEM_DESTAQUE: SituacaoSlot[] = ["em_andamento", "falhou", "parcial", "faltando", "concluida", "futuro"];

export function MesJanelas({ mes, dias }: { mes: Date; dias: DiaGrade[] }) {
  const celulas = gerarCelulasDoMes(mes);
  const porData = new Map(dias.map((d) => [d.data, d]));

  return (
    <div className="rounded-3xl border border-black/5 bg-white p-6 shadow-sm shadow-black/[0.03]">
      <div className="grid grid-cols-7 gap-2">
        {DIAS_SEMANA.map((d, i) => (
          <div key={i} className="pb-1 text-center text-xs font-medium text-zinc-400">
            {d}
          </div>
        ))}

        {celulas.map((dia, indice) => {
          if (!dia) return <div key={indice} />;

          const grade = porData.get(dataISO(dia));
          const contagem = grade ? resumo(grade.janelas) : {};
          const destaque = ORDEM_DESTAQUE.find((s) => (contagem[s] ?? 0) > 0);
          const hoje = mesmoDia(dia, new Date());

          return (
            <Link
              key={indice}
              href={`/janelas?visao=dia&data=${dataISO(dia)}`}
              className={`flex min-h-[76px] flex-col gap-1.5 rounded-2xl border p-2 text-left transition hover:border-amber-300 ${
                hoje ? "border-amber-300 bg-amber-50/40" : "border-black/5"
              }`}
            >
              <span className={`text-sm ${hoje ? "font-semibold text-amber-700" : "text-zinc-700"}`}>
                {dia.getDate()}
              </span>
              {destaque && (
                <div className="flex flex-wrap gap-1">
                  {ORDEM_DESTAQUE.filter((s) => (contagem[s] ?? 0) > 0).map((s) => (
                    <span key={s} className={`h-1.5 w-1.5 rounded-full ${SITUACAO_COR[s]}`} title={s} />
                  ))}
                </div>
              )}
            </Link>
          );
        })}
      </div>
    </div>
  );
}
