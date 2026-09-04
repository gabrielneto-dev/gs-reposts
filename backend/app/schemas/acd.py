from pydantic import BaseModel, Field

from app.schemas.asr import Periodo


class ACDResponse(BaseModel):
    """ACD (Average Call Duration / tempo médio falado) de um período, exato."""

    cliente_id: int | None = None
    periodo: Periodo

    total_atendidas: int
    acd_segundos: float | None = Field(None, description="Duração média das chamadas atendidas, em segundos")
