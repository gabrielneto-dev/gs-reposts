from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func, select

from app.config import settings
from app.db.base import get_session
from app.db.models import AlertaDisparado, Cliente, Gatilho, Janela
from app.routers.metricas import _inicio_do_dia
from app.schemas.alertas import (
    AlertaDisparadoResponse,
    AlertasNaoVistosResponse,
    AlertasResponse,
    ClienteComAlertaNaoVisto,
    MarcarVistoResponse,
)

router = APIRouter(prefix="/api/alertas", tags=["Alertas"])

MAX_REGISTROS = 2000


@router.get("", response_model=AlertasResponse)
async def listar_alertas(
    cliente_id: int | None = Query(None, description="Filtra por cliente"),
    gatilho_id: int | None = Query(None, description="Filtra por regra"),
    visto: bool | None = Query(None, description="Filtra por visto/não visto"),
    data_inicio: date | None = Query(None, description="Só alertas disparados a partir dessa data"),
    data_fim: date | None = Query(None, description="Só alertas disparados até essa data (dia inteiro)"),
    limit: int = Query(200, ge=1, le=MAX_REGISTROS, description="Máximo de alertas retornados"),
) -> AlertasResponse:
    """Histórico de alertas disparados — central de alertas. Ordenado do mais recente pro mais
    antigo, com o nome da regra/cliente e o período da janela já resolvidos (sem round-trip extra
    no frontend)."""

    async with get_session() as session:
        stmt = (
            select(AlertaDisparado, Gatilho.nome, Cliente.nome, Janela.inicio_janela, Janela.fim_janela)
            .join(Gatilho, Gatilho.id == AlertaDisparado.gatilho_id)
            .join(Cliente, Cliente.cliente_id == AlertaDisparado.cliente_id)
            .join(Janela, Janela.id == AlertaDisparado.janela_id)
        )
        if cliente_id is not None:
            stmt = stmt.where(AlertaDisparado.cliente_id == cliente_id)
        if gatilho_id is not None:
            stmt = stmt.where(AlertaDisparado.gatilho_id == gatilho_id)
        if visto is not None:
            stmt = stmt.where(AlertaDisparado.visto == visto)
        if data_inicio is not None:
            stmt = stmt.where(AlertaDisparado.disparado_em >= _inicio_do_dia(data_inicio))
        if data_fim is not None:
            stmt = stmt.where(AlertaDisparado.disparado_em < _inicio_do_dia(data_fim + timedelta(days=1)))
        stmt = stmt.order_by(AlertaDisparado.disparado_em.desc()).limit(limit)

        linhas = (await session.execute(stmt)).all()

    alertas = [
        AlertaDisparadoResponse(
            id=alerta.id,
            gatilho_id=alerta.gatilho_id,
            gatilho_nome=gatilho_nome,
            cliente_id=alerta.cliente_id,
            cliente_nome=cliente_nome,
            janela_id=alerta.janela_id,
            inicio_janela=inicio_janela,
            fim_janela=fim_janela,
            metricas_avaliadas=alerta.metricas_avaliadas,
            disparado_em=alerta.disparado_em,
            visto=alerta.visto,
            visto_em=alerta.visto_em,
        )
        for alerta, gatilho_nome, cliente_nome, inicio_janela, fim_janela in linhas
    ]
    return AlertasResponse(registros=len(alertas), alertas=alertas)


@router.get("/nao-vistos", response_model=AlertasNaoVistosResponse)
async def alertas_nao_vistos() -> AlertasNaoVistosResponse:
    """Retorno leve — só cliente_id + disparo mais recente ainda não visto — feito pra alimentar o
    badge da tabela de clientes sem puxar o corpo completo dos alertas. Sem limite de tempo: um
    alerta continua aparecendo até alguém marcar como visto, não some sozinho depois de um tempo."""

    async with get_session() as session:
        stmt = (
            select(
                AlertaDisparado.cliente_id,
                func.max(AlertaDisparado.disparado_em).label("ultimo_alerta_nao_visto_em"),
            )
            .where(AlertaDisparado.visto.is_(False))
            .group_by(AlertaDisparado.cliente_id)
        )
        linhas = (await session.execute(stmt)).all()

    return AlertasNaoVistosResponse(
        alertas=[ClienteComAlertaNaoVisto(cliente_id=cid, ultimo_alerta_nao_visto_em=ultimo) for cid, ultimo in linhas]
    )


@router.post("/marcar-todos-vistos", response_model=MarcarVistoResponse)
async def marcar_todos_vistos(
    cliente_id: int | None = Query(None, description="Marca só os alertas desse cliente; sem isso, marca todos"),
) -> MarcarVistoResponse:
    agora = datetime.now(ZoneInfo(settings.scheduler_timezone))

    async with get_session() as session:
        stmt = select(AlertaDisparado).where(AlertaDisparado.visto.is_(False))
        if cliente_id is not None:
            stmt = stmt.where(AlertaDisparado.cliente_id == cliente_id)
        alertas = (await session.execute(stmt)).scalars().all()

        for alerta in alertas:
            alerta.visto = True
            alerta.visto_em = agora

        await session.commit()

    return MarcarVistoResponse(registros_marcados=len(alertas))


@router.post("/{alerta_id}/marcar-visto", response_model=AlertaDisparadoResponse)
async def marcar_alerta_visto(alerta_id: int) -> AlertaDisparadoResponse:
    """Idempotente: marcar um alerta já visto de novo só mantém o `visto_em` original."""

    async with get_session() as session:
        stmt = (
            select(AlertaDisparado, Gatilho.nome, Cliente.nome, Janela.inicio_janela, Janela.fim_janela)
            .join(Gatilho, Gatilho.id == AlertaDisparado.gatilho_id)
            .join(Cliente, Cliente.cliente_id == AlertaDisparado.cliente_id)
            .join(Janela, Janela.id == AlertaDisparado.janela_id)
            .where(AlertaDisparado.id == alerta_id)
        )
        linha = (await session.execute(stmt)).first()
        if linha is None:
            raise HTTPException(404, f"Alerta {alerta_id} não encontrado")

        alerta, gatilho_nome, cliente_nome, inicio_janela, fim_janela = linha
        if not alerta.visto:
            alerta.visto = True
            alerta.visto_em = datetime.now(ZoneInfo(settings.scheduler_timezone))
            await session.commit()

        return AlertaDisparadoResponse(
            id=alerta.id,
            gatilho_id=alerta.gatilho_id,
            gatilho_nome=gatilho_nome,
            cliente_id=alerta.cliente_id,
            cliente_nome=cliente_nome,
            janela_id=alerta.janela_id,
            inicio_janela=inicio_janela,
            fim_janela=fim_janela,
            metricas_avaliadas=alerta.metricas_avaliadas,
            disparado_em=alerta.disparado_em,
            visto=alerta.visto,
            visto_em=alerta.visto_em,
        )
