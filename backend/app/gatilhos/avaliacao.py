import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.config import settings
from app.db.base import get_session
from app.db.models import (
    AlertaDisparado,
    Cliente,
    CombinadorCondicoes,
    CondicaoGatilho,
    DirecaoGatilho,
    Gatilho,
    MetricaCliente,
    PeriodoReferenciaGatilho,
)
from app.gatilhos.referencias import MediaReferencia, calcular_medias_referencia

logger = logging.getLogger(__name__)


@dataclass
class ResultadoCondicao:
    """Snapshot de uma condição avaliada — vira uma entrada de `alertas_disparados.metricas_avaliadas`,
    pra a central de alertas mostrar *por que* o gatilho disparou sem precisar recalcular nada."""

    condicao: CondicaoGatilho
    atual: float | None
    referencia: float | None
    percentual_variacao: float | None
    bateu: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "metrica": self.condicao.metrica.value,
            "periodo_referencia": self.condicao.periodo_referencia.value,
            "direcao": self.condicao.direcao.value,
            "percentual_limite": float(self.condicao.percentual_limite),
            "atual": self.atual,
            "referencia": self.referencia,
            "percentual_variacao": self.percentual_variacao,
            "bateu": self.bateu,
        }


async def _carregar_gatilhos_aplicaveis(session, cliente_ids: list[int]) -> list[Gatilho]:
    """Globais (`cliente_id IS NULL`) + individuais dos clientes desta janela — sempre juntos."""

    stmt = (
        select(Gatilho)
        .where(Gatilho.ativo.is_(True), (Gatilho.cliente_id.is_(None)) | (Gatilho.cliente_id.in_(cliente_ids)))
        .options(selectinload(Gatilho.condicoes))
    )
    return list((await session.execute(stmt)).scalars().all())


def _gatilhos_do_cliente(gatilhos: list[Gatilho], cliente_id: int) -> list[Gatilho]:
    return [g for g in gatilhos if g.cliente_id is None or g.cliente_id == cliente_id]


async def _carregar_metricas_da_janela(
    session, janela_id: int, cliente_ids: list[int]
) -> dict[int, MetricaCliente]:
    stmt = select(MetricaCliente).where(
        MetricaCliente.janela_id == janela_id, MetricaCliente.cliente_id.in_(cliente_ids)
    )
    linhas = (await session.execute(stmt)).scalars().all()
    return {linha.cliente_id: linha for linha in linhas}


def _avaliar_condicao(
    condicao: CondicaoGatilho,
    atual_metrica: MetricaCliente,
    referencias: dict[PeriodoReferenciaGatilho, dict[int, MediaReferencia]],
    cliente_id: int,
) -> ResultadoCondicao:
    atual = getattr(atual_metrica, condicao.metrica.value)
    referencia_do_periodo = referencias.get(condicao.periodo_referencia, {}).get(cliente_id)
    referencia = getattr(referencia_do_periodo, condicao.metrica.value) if referencia_do_periodo else None

    # Sem dado atual, sem histórico de referência (cliente novo) ou referência zero (divisão por
    # zero) — a condição simplesmente não bate, nunca lança exceção.
    if atual is None or referencia_do_periodo is None or referencia_do_periodo.amostras == 0 or not referencia:
        return ResultadoCondicao(
            condicao=condicao, atual=float(atual) if atual is not None else None,
            referencia=referencia, percentual_variacao=None, bateu=False,
        )

    atual = float(atual)
    referencia = float(referencia)
    variacao_percentual = (atual - referencia) / referencia * 100

    if condicao.direcao == DirecaoGatilho.AUMENTO:
        bateu = variacao_percentual >= float(condicao.percentual_limite)
    elif condicao.direcao == DirecaoGatilho.QUEDA:
        bateu = -variacao_percentual >= float(condicao.percentual_limite)
    else:
        bateu = abs(variacao_percentual) >= float(condicao.percentual_limite)

    return ResultadoCondicao(
        condicao=condicao, atual=atual, referencia=referencia,
        percentual_variacao=variacao_percentual, bateu=bateu,
    )


async def _notificar_frontend_alertas(payloads: list[dict[str, Any]]) -> None:
    """Mesma filosofia best-effort de `scheduler.jobs._notificar_frontend`: falha aqui nunca deve
    propagar."""

    url = settings.frontend_alertas_webhook_url
    if not url:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={"alertas": payloads})
    except httpx.HTTPError as exc:
        logger.warning("Falha ao notificar o frontend sobre alertas via webhook (%s): %s", url, exc)


async def _notificar_webhook_externo(payloads: list[dict[str, Any]]) -> None:
    url = settings.alerta_webhook_url
    if not url:
        return
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            await client.post(url, json={"alertas": payloads})
    except httpx.HTTPError as exc:
        logger.warning("Falha ao notificar webhook externo de alertas (%s): %s", url, exc)


async def avaliar_gatilhos_da_janela(janela_id: int, cliente_ids: list[int]) -> None:
    """Chamado depois do commit da coleta de uma janela, em sessão própria (a sessão da coleta já
    fechou). Nunca deve derrubar o job de coleta nem corromper as métricas já persistidas — quem
    chama envolve isso num try/except amplo."""

    if not cliente_ids:
        return

    async with get_session() as session:
        gatilhos = await _carregar_gatilhos_aplicaveis(session, cliente_ids)
        if not gatilhos:
            return

        periodos_usados = {condicao.periodo_referencia for g in gatilhos for condicao in g.condicoes}
        if not periodos_usados:
            return

        metricas_da_janela = await _carregar_metricas_da_janela(session, janela_id, cliente_ids)
        if not metricas_da_janela:
            return

        # Ponto no tempo usado como "hoje" pras janelas móveis de referência: o fim da própria
        # janela avaliada (não o relógio da máquina) — assim a avaliação dá o mesmo resultado se
        # rodada ao vivo logo após a coleta ou manualmente bem depois, pra uma janela antiga.
        referencia_agora: datetime = next(iter(metricas_da_janela.values())).fim_janela

        referencias = {
            periodo: await calcular_medias_referencia(session, periodo, set(cliente_ids), referencia_agora)
            for periodo in periodos_usados
        }

        novos_alertas: list[AlertaDisparado] = []
        for cliente_id in cliente_ids:
            atual = metricas_da_janela.get(cliente_id)
            if atual is None:
                continue
            for gatilho in _gatilhos_do_cliente(gatilhos, cliente_id):
                if not gatilho.condicoes:
                    continue
                resultados = [_avaliar_condicao(c, atual, referencias, cliente_id) for c in gatilho.condicoes]
                bateu = (
                    all(r.bateu for r in resultados)
                    if gatilho.combinador == CombinadorCondicoes.E
                    else any(r.bateu for r in resultados)
                )
                if bateu:
                    novos_alertas.append(
                        AlertaDisparado(
                            gatilho_id=gatilho.id,
                            cliente_id=cliente_id,
                            janela_id=janela_id,
                            metricas_avaliadas=[r.as_dict() for r in resultados],
                            severidade=gatilho.severidade,
                        )
                    )

        if not novos_alertas:
            return

        session.add_all(novos_alertas)
        await session.commit()

        nomes_gatilho = {g.id: g.nome for g in gatilhos}
        clientes_stmt = select(Cliente.cliente_id, Cliente.nome).where(
            Cliente.cliente_id.in_({alerta.cliente_id for alerta in novos_alertas})
        )
        nomes_cliente = dict((await session.execute(clientes_stmt)).all())

        payloads = [
            {
                "alerta_id": alerta.id,
                "gatilho_id": alerta.gatilho_id,
                "gatilho_nome": nomes_gatilho.get(alerta.gatilho_id),
                "cliente_id": alerta.cliente_id,
                "cliente_nome": nomes_cliente.get(alerta.cliente_id),
                "janela_id": alerta.janela_id,
                "metricas_avaliadas": alerta.metricas_avaliadas,
                "severidade": alerta.severidade.value,
                "disparado_em": alerta.disparado_em.isoformat(),
            }
            for alerta in novos_alertas
        ]

    logger.info("Gatilhos avaliados na janela %s: %s alerta(s) disparado(s)", janela_id, len(payloads))
    await _notificar_frontend_alertas(payloads)
    await _notificar_webhook_externo(payloads)
