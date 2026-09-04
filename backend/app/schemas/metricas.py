from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MetricaJanela(BaseModel):
    """ASR/ACD/PDD exatos de um cliente numa janela já coletada pelo scheduler."""

    model_config = ConfigDict(from_attributes=True)

    window_start: datetime
    window_end: datetime
    total_atendidas: int
    total_falhas: int
    asr_percentual: float
    acd_segundos: float | None = None
    pdd_medio_segundos: float | None = None
    occurrences_discovery: int = Field(..., description="Ocorrências na amostra de descoberta (não o total real)")
    truncado: bool


class ClienteMetricasResponse(BaseModel):
    """Histórico de um cliente — dados já coletados, sem chamar o softswitch nesta consulta."""

    cliente_id: int
    nome: str | None = None
    registros: int
    metricas: list[MetricaJanela]
    aviso: str | None = None


class JanelaColeta(BaseModel):
    """Uma execução do scheduler (não os dados de cliente em si — ver /clientes/{cliente_id})."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    window_start: datetime
    window_end: datetime
    status: str
    discovery_sample_limit: int
    clients_discovered: int
    clients_processed: int
    error_message: str | None = None
    started_at: datetime
    finished_at: datetime | None = None


class JanelasResponse(BaseModel):
    registros: int
    janelas: list[JanelaColeta]
