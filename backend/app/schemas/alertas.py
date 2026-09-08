from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.db.models import SeveridadeGatilho


class AlertaDisparadoResponse(BaseModel):
    id: int
    gatilho_id: int
    gatilho_nome: str
    cliente_id: int
    cliente_nome: str | None = None
    janela_id: int
    inicio_janela: datetime
    fim_janela: datetime
    metricas_avaliadas: list[dict[str, Any]]
    severidade: SeveridadeGatilho
    disparado_em: datetime
    visto: bool
    visto_em: datetime | None = None


class AlertasResponse(BaseModel):
    registros: int
    alertas: list[AlertaDisparadoResponse]


class ClienteComAlertaNaoVisto(BaseModel):
    cliente_id: int
    severidade_maxima: SeveridadeGatilho
    ultimo_alerta_nao_visto_em: datetime


class AlertasNaoVistosResponse(BaseModel):
    alertas: list[ClienteComAlertaNaoVisto]


class MarcarVistoResponse(BaseModel):
    registros_marcados: int
