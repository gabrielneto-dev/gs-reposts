from datetime import date, time

from pydantic import BaseModel, Field


class Periodo(BaseModel):
    data_inicio: date | None = None
    data_fim: date | None = None
    hora_inicio: time | None = None
    hora_fim: time | None = None


class Disposicao(BaseModel):
    """Uma fatia da "pizza" do ASR: um código de resultado de chamada e sua participação."""

    codigo: str = Field(..., description="Código SIP predominante do grupo (ex: 200, 487, 486, 503)")
    descricao: str
    quantidade: int
    percentual: float
    exato: bool = Field(..., description="True para 200/ANSWERED (contagem exata); False para os demais (amostrados)")


class ASRAnaliseResponse(BaseModel):
    """ASR (Answer Seizure Ratio) de um período, com o detalhamento completo por código
    (200 OK, 487, 486, 503...) — a "pizza" de resultados de chamada."""

    cliente_id: int | None = None
    periodo: Periodo

    total_atendidas: int
    total_falhas: int
    total_chamadas: int
    asr_percentual: float = Field(..., description="total_atendidas / total_chamadas * 100 (exato)")

    disposicoes: list[Disposicao] = Field(
        ...,
        description=(
            "Detalhamento por código. 200/ANSWERED é sempre exato; os demais são exatos apenas "
            "quando `exato=true` foi pedido, senão vêm de uma amostra das falhas."
        ),
    )
    tamanho_amostra_falhas: int = Field(..., description="Quantos registros de falha foram inspecionados")
    exato: bool = Field(..., description="Se true, `disposicoes` cobre 100% das falhas do período (sem amostragem)")
    truncado: bool = Field(
        False, description="Só relevante com exato=true: se true, bateu no limite de segurança antes de esgotar o período"
    )
