from pydantic import BaseModel, Field

from app.schemas.asr import Periodo


class PDDResponse(BaseModel):
    """PDD (Post Dial Delay / tempo até a primeira resposta) de um período. Amostrado por padrão;
    exato quando `exato=true` — só existe em chamadas com falha e não tem agregado pronto na API."""

    cliente_id: int | None = None
    periodo: Periodo

    pdd_medio_segundos: float | None = None
    tamanho_amostra: int = Field(..., description="Quantos registros de falha entraram na média")
    total_falhas_periodo: int = Field(..., description="Total real de chamadas com falha no período (população)")
    exato: bool = Field(..., description="Se true, pdd_medio_segundos usa 100% das falhas do período (sem amostragem)")
    truncado: bool = Field(
        False, description="Só relevante com exato=true: se true, bateu no limite de segurança antes de esgotar o período"
    )
