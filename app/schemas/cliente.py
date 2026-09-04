from datetime import date

from pydantic import BaseModel

from app.schemas.asr import Periodo


class ClienteBase(BaseModel):
    id: int
    tipo: str
    tipo_descricao: str
    nome_fantasia: str
    razao_social: str
    telefone: str | None = None
    email: str | None = None
    cidade: str | None = None
    estado: str | None = None
    status: int
    usuarios: list[str] = []


class ClienteListaResponse(BaseModel):
    offset: int
    limit: int
    registros: int
    clientes: list[ClienteBase]


class ClienteComSimilaridade(ClienteBase):
    similaridade: float


class ClienteBuscaResponse(BaseModel):
    registros: int
    clientes: list[ClienteComSimilaridade]
    aviso: str | None = None


class ClienteComVolume(ClienteBase):
    chamadas_na_amostra: int


class ClienteAtividadeResponse(BaseModel):
    periodo: Periodo
    registros: int
    clientes: list[ClienteComVolume]
    aviso: str | None = None


class ClienteComRecorrencia(ClienteBase):
    chamadas_na_amostra: int
    dias_ativos: int
    datas_ativas: list[date]


class ClienteRecorrenciaResponse(BaseModel):
    data_inicio: date
    data_fim: date
    dias_minimos: int
    registros: int
    clientes: list[ClienteComRecorrencia]
    aviso: str | None = None
