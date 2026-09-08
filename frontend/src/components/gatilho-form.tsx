"use client";

import { useActionState, useState } from "react";

import { atualizarGatilho, criarGatilho, type ResultadoAcaoGatilho } from "@/lib/gatilhos-actions";
import type {
  CombinadorCondicoes,
  DirecaoGatilho,
  Gatilho,
  MetricaGatilho,
  PeriodoReferenciaGatilho,
} from "@/lib/gatilhos";

const METRICAS: { value: MetricaGatilho; label: string }[] = [
  { value: "asr_percentual", label: "ASR" },
  { value: "acd_segundos", label: "ACD" },
  { value: "pdd_medio_segundos", label: "PDD" },
];

const PERIODOS: { value: PeriodoReferenciaGatilho; label: string }[] = [
  { value: "media_ontem", label: "Média de ontem" },
  { value: "media_semanal", label: "Média semanal (7 dias)" },
  { value: "media_mensal", label: "Média mensal (30 dias)" },
];

const DIRECOES: { value: DirecaoGatilho; label: string }[] = [
  { value: "queda", label: "Queda" },
  { value: "aumento", label: "Aumento" },
  { value: "qualquer", label: "Qualquer direção" },
];

type CondicaoRascunho = {
  metrica: MetricaGatilho;
  periodo_referencia: PeriodoReferenciaGatilho;
  direcao: DirecaoGatilho;
  percentual_limite: number;
};

const CONDICAO_PADRAO: CondicaoRascunho = {
  metrica: "asr_percentual",
  periodo_referencia: "media_semanal",
  direcao: "queda",
  percentual_limite: 20,
};

const ESTADO_INICIAL: ResultadoAcaoGatilho = { ok: false };

const campoClasse =
  "rounded-xl border border-black/5 bg-zinc-50 px-3.5 py-2.5 text-sm text-zinc-800 outline-none transition focus:border-amber-300 focus:bg-white focus:ring-2 focus:ring-amber-100";
const campoClasseSm =
  "w-full rounded-lg border border-black/5 bg-white px-2.5 py-2 text-sm text-zinc-800 outline-none transition focus:border-amber-300 focus:ring-2 focus:ring-amber-100";

export function GatilhoForm({ gatilhoExistente }: { gatilhoExistente?: Gatilho }) {
  const editando = gatilhoExistente !== undefined;
  const acao = editando ? atualizarGatilho.bind(null, gatilhoExistente.id) : criarGatilho;
  const [estado, submeter, pendente] = useActionState(acao, ESTADO_INICIAL);

  const [nome, setNome] = useState(gatilhoExistente?.nome ?? "");
  const [escopoIndividual, setEscopoIndividual] = useState(gatilhoExistente?.cliente_id != null);
  const [clienteId, setClienteId] = useState(gatilhoExistente?.cliente_id?.toString() ?? "");
  const [combinador, setCombinador] = useState<CombinadorCondicoes>(gatilhoExistente?.combinador ?? "e");
  const [ativo, setAtivo] = useState(gatilhoExistente?.ativo ?? true);
  const [condicoes, setCondicoes] = useState<CondicaoRascunho[]>(
    gatilhoExistente?.condicoes.map((c) => ({
      metrica: c.metrica,
      periodo_referencia: c.periodo_referencia,
      direcao: c.direcao,
      percentual_limite: c.percentual_limite,
    })) ?? [CONDICAO_PADRAO],
  );

  // Depois de criar com sucesso, limpa o formulário pra permitir cadastrar a próxima regra — só
  // se aplica à criação (editar mantém os campos como estão, o usuário fecha o card). Ajustado
  // durante o render (guardado por comparação com o último `estado` visto), não em efeito — evitar
  // side effects diretos no corpo de um useEffect é a prática recomendada pelo React.
  const [ultimoEstadoVisto, setUltimoEstadoVisto] = useState(estado);
  if (estado !== ultimoEstadoVisto) {
    setUltimoEstadoVisto(estado);
    if (estado.ok && !editando) {
      setNome("");
      setEscopoIndividual(false);
      setClienteId("");
      setCombinador("e");
      setCondicoes([CONDICAO_PADRAO]);
    }
  }

  function atualizarCondicao(indice: number, campo: keyof CondicaoRascunho, valor: string) {
    setCondicoes((atuais) =>
      atuais.map((c, i) =>
        i === indice ? { ...c, [campo]: campo === "percentual_limite" ? Number(valor) : valor } : c,
      ),
    );
  }

  function removerCondicao(indice: number) {
    setCondicoes((atuais) => atuais.filter((_, i) => i !== indice));
  }

  function adicionarCondicao() {
    setCondicoes((atuais) => [...atuais, CONDICAO_PADRAO]);
  }

  return (
    <form action={submeter} className="space-y-5">
      <input type="hidden" name="condicoes" value={JSON.stringify(condicoes)} />

      <div className="grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-zinc-700">Nome da regra</span>
          <input
            name="nome"
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            required
            placeholder="Ex.: ASR caiu vs média semanal"
            className={campoClasse}
          />
        </label>

        <label className="flex flex-col gap-1.5 text-sm">
          <span className="font-medium text-zinc-700">Combinação das condições</span>
          <select
            name="combinador"
            value={combinador}
            onChange={(e) => setCombinador(e.target.value as CombinadorCondicoes)}
            className={campoClasse}
          >
            <option value="e">E (todas as condições precisam bater)</option>
            <option value="ou">OU (qualquer uma basta)</option>
          </select>
        </label>
      </div>

      {!editando && (
        <div className="grid gap-4 sm:grid-cols-2">
          <label className="flex items-center gap-2 text-sm text-zinc-700">
            <input
              type="checkbox"
              checked={escopoIndividual}
              onChange={(e) => setEscopoIndividual(e.target.checked)}
            />
            Regra individual (só pra um cliente específico)
          </label>
          {escopoIndividual && (
            <label className="flex flex-col gap-1.5 text-sm">
              <span className="font-medium text-zinc-700">ID do cliente</span>
              <input
                name="cliente_id"
                type="number"
                value={clienteId}
                onChange={(e) => setClienteId(e.target.value)}
                required={escopoIndividual}
                className={campoClasse}
              />
            </label>
          )}
        </div>
      )}

      {editando && (
        <label className="flex items-center gap-2 text-sm text-zinc-700">
          <input type="checkbox" name="ativo" checked={ativo} onChange={(e) => setAtivo(e.target.checked)} />
          Ativo
        </label>
      )}

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-zinc-700">Condições</span>
          <button
            type="button"
            onClick={adicionarCondicao}
            className="text-xs font-medium text-amber-600 hover:text-amber-700"
          >
            + adicionar condição
          </button>
        </div>

        {condicoes.map((condicao, indice) => (
          <div
            key={indice}
            className="grid grid-cols-2 gap-3 rounded-2xl border border-black/5 bg-zinc-50 p-4 sm:grid-cols-5 sm:items-end"
          >
            <label className="flex flex-col gap-1 text-xs text-zinc-500">
              Métrica
              <select
                value={condicao.metrica}
                onChange={(e) => atualizarCondicao(indice, "metrica", e.target.value)}
                className={campoClasseSm}
              >
                {METRICAS.map((m) => (
                  <option key={m.value} value={m.value}>
                    {m.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs text-zinc-500">
              Referência
              <select
                value={condicao.periodo_referencia}
                onChange={(e) => atualizarCondicao(indice, "periodo_referencia", e.target.value)}
                className={campoClasseSm}
              >
                {PERIODOS.map((p) => (
                  <option key={p.value} value={p.value}>
                    {p.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs text-zinc-500">
              Direção
              <select
                value={condicao.direcao}
                onChange={(e) => atualizarCondicao(indice, "direcao", e.target.value)}
                className={campoClasseSm}
              >
                {DIRECOES.map((d) => (
                  <option key={d.value} value={d.value}>
                    {d.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1 text-xs text-zinc-500">
              Limite (%)
              <input
                type="number"
                min={0.01}
                step={0.01}
                value={condicao.percentual_limite}
                onChange={(e) => atualizarCondicao(indice, "percentual_limite", e.target.value)}
                className={campoClasseSm}
              />
            </label>
            <button
              type="button"
              onClick={() => removerCondicao(indice)}
              disabled={condicoes.length === 1}
              className="justify-self-start text-xs font-medium text-rose-500 hover:text-rose-600 disabled:cursor-not-allowed disabled:text-zinc-300"
            >
              remover
            </button>
          </div>
        ))}
      </div>

      {estado.erro && <p className="text-sm text-rose-600">{estado.erro}</p>}

      <button
        type="submit"
        disabled={pendente}
        className="rounded-full bg-zinc-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-zinc-800 disabled:opacity-50"
      >
        {pendente ? "Salvando..." : editando ? "Salvar alterações" : "Criar gatilho"}
      </button>
    </form>
  );
}
