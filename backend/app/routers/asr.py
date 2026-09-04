from collections import Counter, defaultdict
from datetime import date, time

from fastapi import APIRouter, HTTPException, Query

from app.clients.nextrouter import (
    NextRouterAPIError,
    get_asr_data,
    get_cdr_aggregate,
    get_disconnection_full,
    periodo_params,
)
from app.schemas.asr import ASRAnaliseResponse, Disposicao, Periodo

router = APIRouter(prefix="/api/asr", tags=["ASR"])

DESCRICOES_DISPOSICAO = {
    "CONGESTION": "Congestionamento / indisponível",
    "CANCEL": "Cancelada antes do atendimento",
    "NOANSWER": "Não atendida",
    "PDD": "Timeout de sinalização (PDD)",
    "BUSY": "Ocupado",
    "NOTFOUND": "Número não encontrado",
}


def _agrupar_por_sip(registros_falha: list[dict]) -> dict[str, Counter]:
    por_sip: dict[str, Counter] = defaultdict(Counter)
    for r in registros_falha:
        sip = str(r.get("sip_code") or "?")
        disposicao = r.get("disposition", "DESCONHECIDO")
        por_sip[sip][disposicao] += 1
    return por_sip


def _montar_disposicoes(
    por_sip: dict[str, Counter], total_atendidas: int, total_chamadas: int, total_falhas_inspecionadas: int, exato: bool
) -> list[Disposicao]:
    disposicoes: list[Disposicao] = []

    if total_chamadas > 0:
        disposicoes.append(
            Disposicao(
                codigo="200",
                descricao="ANSWERED (atendida)",
                quantidade=total_atendidas,
                percentual=round(total_atendidas / total_chamadas * 100, 2),
                exato=True,
            )
        )

    grupos = sorted(por_sip.items(), key=lambda item: sum(item[1].values()), reverse=True)
    for sip_code, contagem_disposicao in grupos:
        quantidade = sum(contagem_disposicao.values())
        disposicao_predominante = contagem_disposicao.most_common(1)[0][0]
        disposicoes.append(
            Disposicao(
                codigo=sip_code,
                descricao=DESCRICOES_DISPOSICAO.get(disposicao_predominante, disposicao_predominante),
                quantidade=quantidade,
                percentual=round(quantidade / total_falhas_inspecionadas * 100, 2) if total_falhas_inspecionadas else 0.0,
                exato=exato,
            )
        )

    return disposicoes


@router.get("", response_model=ASRAnaliseResponse)
async def analise_asr(
    cliente_id: int | None = Query(None, description="ID do cliente. Omitido, traz o total da base."),
    data_inicio: date | None = Query(None, description="Data inicial do período (YYYY-MM-DD)"),
    data_fim: date | None = Query(None, description="Data final do período (YYYY-MM-DD)"),
    hora_inicio: time | None = Query(None, description="Hora inicial do período (HH:MM:SS)"),
    hora_fim: time | None = Query(None, description="Hora final do período (HH:MM:SS)"),
    amostra_falhas: int = Query(
        1000,
        ge=1,
        le=5000,
        description="Quantas chamadas com falha usar pra montar o detalhamento por código. Ignorado se exato=true.",
    ),
    exato: bool = Query(
        False,
        description=(
            "Se true, ignora amostra_falhas e pagina TODAS as chamadas com falha do período pra um "
            "detalhamento 100% exato por código. Pode levar de segundos a minutos em períodos grandes "
            "ou clientes com muito volume — use com cuidado."
        ),
    ),
) -> ASRAnaliseResponse:
    """ASR (Answer Seizure Ratio) por período e cliente, com o detalhamento "de pizza" por
    código de resultado (200 OK, 487, 486, 503, etc.).

    `total_atendidas`, `total_falhas`, `total_chamadas` e `asr_percentual` são sempre exatos
    (vêm de agregados da API). O detalhamento por código (`disposicoes`) é amostrado por padrão
    (rápido); passe `exato=true` para uma contagem 100% exata, paginando todas as falhas do
    período — mais lento e mais pesado na API do softswitch quanto maior o volume.
    """

    try:
        if exato:
            atendidas_payload, falhas_payload = (
                await get_cdr_aggregate(cliente_id=cliente_id, periodo=periodo_params(data_inicio, data_fim, hora_inicio, hora_fim)),
                await get_disconnection_full(cliente_id=cliente_id, periodo=periodo_params(data_inicio, data_fim, hora_inicio, hora_fim)),
            )
        else:
            payload = await get_asr_data(
                cliente_id=cliente_id,
                data_inicio=data_inicio,
                data_fim=data_fim,
                hora_inicio=hora_inicio,
                hora_fim=hora_fim,
                amostra_falhas=amostra_falhas,
            )
            atendidas_payload, falhas_payload = payload["atendidas"], payload["falhas"]
    except NextRouterAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    total_atendidas = atendidas_payload["total_records"]
    total_falhas = falhas_payload["total_records"]
    total_chamadas = total_atendidas + total_falhas
    asr_percentual = (total_atendidas / total_chamadas * 100) if total_chamadas > 0 else 0.0

    registros_falha = falhas_payload.get("data", [])
    por_sip = _agrupar_por_sip(registros_falha)

    return ASRAnaliseResponse(
        cliente_id=cliente_id,
        periodo=Periodo(data_inicio=data_inicio, data_fim=data_fim, hora_inicio=hora_inicio, hora_fim=hora_fim),
        total_atendidas=total_atendidas,
        total_falhas=total_falhas,
        total_chamadas=total_chamadas,
        asr_percentual=round(asr_percentual, 2),
        disposicoes=_montar_disposicoes(por_sip, total_atendidas, total_chamadas, len(registros_falha), exato),
        tamanho_amostra_falhas=len(registros_falha),
        exato=exato,
        truncado=falhas_payload.get("truncado", False),
    )
