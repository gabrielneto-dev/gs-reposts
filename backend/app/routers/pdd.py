from datetime import date, time

from fastapi import APIRouter, HTTPException, Query

from app.clients.nextrouter import NextRouterAPIError, get_disconnection_full, get_disconnection_sample, periodo_params
from app.schemas.asr import Periodo
from app.schemas.pdd import PDDResponse

router = APIRouter(prefix="/api/pdd", tags=["PDD"])


@router.get("", response_model=PDDResponse)
async def analise_pdd(
    cliente_id: int | None = Query(None, description="ID do cliente. Omitido, traz o total da base."),
    data_inicio: date | None = Query(None, description="Data inicial do período (YYYY-MM-DD)"),
    data_fim: date | None = Query(None, description="Data final do período (YYYY-MM-DD)"),
    hora_inicio: time | None = Query(None, description="Hora inicial do período (HH:MM:SS)"),
    hora_fim: time | None = Query(None, description="Hora final do período (HH:MM:SS)"),
    amostra: int = Query(
        1000,
        ge=1,
        le=5000,
        description=(
            "Quantidade de chamadas com falha usadas para estimar o PDD médio. Ignorado se exato=true. "
            "Estreite o período (data/hora) para deixar a amostra mais representativa, ou aumente esse valor."
        ),
    ),
    exato: bool = Query(
        False,
        description=(
            "Se true, ignora `amostra` e pagina TODAS as chamadas com falha do período pra uma média "
            "de PDD 100% exata. Pode levar de segundos a minutos em períodos grandes ou clientes com "
            "muito volume — use com cuidado."
        ),
    ),
) -> PDDResponse:
    """PDD (Post Dial Delay / tempo até a primeira resposta) por período e cliente.

    Amostrado por padrão (rápido). Passe `exato=true` para uma média 100% exata, paginando todas
    as chamadas com falha do período — mais lento e mais pesado na API do softswitch quanto maior
    o volume. O campo `pdd` só existe em chamadas com falha (/api/cdrDisconnection); não há
    agregado/média pronta na API.
    """

    try:
        if exato:
            payload = await get_disconnection_full(
                cliente_id=cliente_id, periodo=periodo_params(data_inicio, data_fim, hora_inicio, hora_fim)
            )
        else:
            payload = await get_disconnection_sample(
                cliente_id=cliente_id,
                periodo=periodo_params(data_inicio, data_fim, hora_inicio, hora_fim),
                limit=amostra,
            )
    except NextRouterAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    registros = payload.get("data", [])
    pdd_valores = [float(r["pdd"]) for r in registros if r.get("pdd") is not None]
    pdd_medio_segundos = (sum(pdd_valores) / len(pdd_valores)) if pdd_valores else None

    return PDDResponse(
        cliente_id=cliente_id,
        periodo=Periodo(data_inicio=data_inicio, data_fim=data_fim, hora_inicio=hora_inicio, hora_fim=hora_fim),
        pdd_medio_segundos=round(pdd_medio_segundos, 2) if pdd_medio_segundos is not None else None,
        tamanho_amostra=len(pdd_valores),
        total_falhas_periodo=payload.get("total_records", 0),
        exato=exato,
        truncado=payload.get("truncado", False),
    )
