from datetime import date, time

from fastapi import APIRouter, HTTPException, Query

from app.clients.nextrouter import NextRouterAPIError, get_cdr_aggregate, periodo_params
from app.schemas.acd import ACDResponse
from app.schemas.asr import Periodo

router = APIRouter(prefix="/api/acd", tags=["ACD"])


@router.get("", response_model=ACDResponse)
async def analise_acd(
    cliente_id: int | None = Query(None, description="ID do cliente. Omitido, traz o total da base."),
    data_inicio: date | None = Query(None, description="Data inicial do período (YYYY-MM-DD)"),
    data_fim: date | None = Query(None, description="Data final do período (YYYY-MM-DD)"),
    hora_inicio: time | None = Query(None, description="Hora inicial do período (HH:MM:SS)"),
    hora_fim: time | None = Query(None, description="Hora final do período (HH:MM:SS)"),
) -> ACDResponse:
    """ACD (Average Call Duration / tempo médio falado) por período e cliente.

    Exato: vem do agregado de /api/cdr (`total_time` / `total_records`), sem amostragem.
    """

    try:
        payload = await get_cdr_aggregate(
            cliente_id=cliente_id,
            periodo=periodo_params(data_inicio, data_fim, hora_inicio, hora_fim),
        )
    except NextRouterAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    total_atendidas = payload["total_records"]
    total_time = payload.get("total_time")
    acd_segundos = (total_time / total_atendidas) if total_time and total_atendidas > 0 else None

    return ACDResponse(
        cliente_id=cliente_id,
        periodo=Periodo(data_inicio=data_inicio, data_fim=data_fim, hora_inicio=hora_inicio, hora_fim=hora_fim),
        total_atendidas=total_atendidas,
        acd_segundos=round(acd_segundos, 2) if acd_segundos is not None else None,
    )
