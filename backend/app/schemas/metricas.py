from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MetricaJanela(BaseModel):
    """ASR/ACD/PDD exatos de um cliente numa janela já coletada pelo scheduler."""

    model_config = ConfigDict(from_attributes=True)

    inicio_janela: datetime
    fim_janela: datetime
    total_atendidas: int
    total_falhas: int
    asr_percentual: float
    acd_segundos: float | None = None
    pdd_medio_segundos: float | None = None
    ocorrencias_descoberta: int = Field(..., description="Ocorrências na amostra de descoberta (não o total real)")
    truncado: bool


class ClienteResumo(BaseModel):
    """Resumo de um cliente: ASR/ACD/PDD da coleta mais recente disponível."""

    model_config = ConfigDict(from_attributes=True)

    cliente_id: int
    nome: str | None = None
    inicio_janela: datetime
    fim_janela: datetime
    total_atendidas: int
    total_falhas: int
    asr_percentual: float
    acd_segundos: float | None = None
    pdd_medio_segundos: float | None = None
    volume_periodo: int = Field(..., description="Total de chamadas (atendidas + falhas) somado de todas as janelas do período filtrado")


class ClientesResumoResponse(BaseModel):
    """Um cliente por linha — pronta pra tabela de listagem."""

    inicio: datetime = Field(..., description="Início do período ao qual esta listagem está filtrada (default: início de hoje)")
    fim: datetime = Field(..., description="Fim do período ao qual esta listagem está filtrada (default: início de amanhã)")
    registros: int
    clientes: list[ClienteResumo]


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
    inicio_janela: datetime
    fim_janela: datetime
    situacao: str
    limite_amostra_descoberta: int
    clientes_descobertos: int
    clientes_processados: int
    mensagem_erro: str | None = None
    iniciado_em: datetime
    finalizado_em: datetime | None = None


class JanelasResponse(BaseModel):
    registros: int
    janelas: list[JanelaColeta]


class SlotJanela(BaseModel):
    """Um dos 15 slots canônicos de um dia (00-07, hora em hora 07-20, 20-00). `situacao` inclui os
    valores reais de `SituacaoJanela` mais dois estados sintéticos que não existem no banco:
    `faltando` (já passou e não tem `Janela` nenhuma — pode disparar manualmente) e `futuro`
    (ainda não chegou — bloqueado)."""

    inicio_janela: datetime
    fim_janela: datetime
    situacao: str
    janela_id: int | None = None
    clientes_descobertos: int | None = None
    clientes_processados: int | None = None
    mensagem_erro: str | None = None
    pode_disparar: bool


class DiaGrade(BaseModel):
    data: str = Field(..., description="Data no formato YYYY-MM-DD (fuso operacional)")
    janelas: list[SlotJanela]


class GradeJanelasResponse(BaseModel):
    dias: list[DiaGrade]


class DispararJanelaRequest(BaseModel):
    inicio_janela: datetime
    fim_janela: datetime


class DispararJanelaResponse(BaseModel):
    ok: bool
    mensagem: str
