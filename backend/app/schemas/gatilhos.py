from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.db.models import CombinadorCondicoes, DirecaoGatilho, MetricaGatilho, PeriodoReferenciaGatilho


class CondicaoGatilhoCreate(BaseModel):
    metrica: MetricaGatilho
    periodo_referencia: PeriodoReferenciaGatilho
    direcao: DirecaoGatilho
    percentual_limite: float = Field(..., gt=0, description="Limite de variação percentual, ex. 20.0 = 20%")


class CondicaoGatilhoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    metrica: MetricaGatilho
    periodo_referencia: PeriodoReferenciaGatilho
    direcao: DirecaoGatilho
    percentual_limite: float


class GatilhoCreate(BaseModel):
    nome: str
    cliente_id: int | None = Field(
        None, description="Nulo = gatilho global (vale pra todo cliente); preenchido = individual daquele cliente"
    )
    combinador: CombinadorCondicoes = CombinadorCondicoes.E
    ativo: bool = True
    condicoes: list[CondicaoGatilhoCreate] = Field(..., min_length=1)


class GatilhoUpdate(BaseModel):
    nome: str
    combinador: CombinadorCondicoes
    ativo: bool
    condicoes: list[CondicaoGatilhoCreate] = Field(..., min_length=1)


class GatilhoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    cliente_id: int | None = None
    combinador: CombinadorCondicoes
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime
    condicoes: list[CondicaoGatilhoResponse]


class GatilhosResponse(BaseModel):
    registros: int
    gatilhos: list[GatilhoResponse]
