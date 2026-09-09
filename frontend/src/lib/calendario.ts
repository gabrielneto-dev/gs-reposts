export const NOMES_MES = [
  "janeiro", "fevereiro", "março", "abril", "maio", "junho",
  "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
];

export const DIAS_SEMANA = ["D", "S", "T", "Q", "Q", "S", "S"];

export function inicioDoDia(d: Date): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate());
}

export function mesmoDia(a: Date | null, b: Date | null): boolean {
  return (
    !!a && !!b && a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate()
  );
}

export function addMeses(mes: Date, n: number): Date {
  return new Date(mes.getFullYear(), mes.getMonth() + n, 1);
}

export function addDias(d: Date, n: number): Date {
  return new Date(d.getFullYear(), d.getMonth(), d.getDate() + n);
}

/** Células de um mês em grade de 7 colunas — `null` nos espaços antes do dia 1. */
export function gerarCelulasDoMes(mes: Date): (Date | null)[] {
  const ano = mes.getFullYear();
  const mesIndex = mes.getMonth();
  const primeiroDiaSemana = new Date(ano, mesIndex, 1).getDay();
  const totalDias = new Date(ano, mesIndex + 1, 0).getDate();

  const celulas: (Date | null)[] = [];
  for (let i = 0; i < primeiroDiaSemana; i++) celulas.push(null);
  for (let dia = 1; dia <= totalDias; dia++) celulas.push(new Date(ano, mesIndex, dia));
  return celulas;
}

const pad = (n: number) => String(n).padStart(2, "0");

/** Data local (sem fuso) no formato YYYY-MM-DD, pronta pra ir de/pra query param ou pro backend. */
export function dataISO(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

/** "2026-09-09" -> Date local (meia-noite), sem passar pelo parser de fuso do JS. */
export function dataISOParaDate(s: string): Date {
  const [ano, mes, dia] = s.split("-").map(Number);
  return new Date(ano, mes - 1, dia);
}
