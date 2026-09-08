from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.base import get_session
from app.db.models import Cliente, CondicaoGatilho, Gatilho
from app.schemas.gatilhos import CondicaoGatilhoCreate, GatilhoCreate, GatilhoResponse, GatilhosResponse, GatilhoUpdate

router = APIRouter(prefix="/api/gatilhos", tags=["Gatilhos"])


def _condicoes_orm(dados: list[CondicaoGatilhoCreate]) -> list[CondicaoGatilho]:
    return [
        CondicaoGatilho(
            metrica=c.metrica,
            periodo_referencia=c.periodo_referencia,
            direcao=c.direcao,
            percentual_limite=c.percentual_limite,
        )
        for c in dados
    ]


@router.post("", response_model=GatilhoResponse, status_code=201)
async def criar_gatilho(dados: GatilhoCreate) -> Gatilho:
    """Cria uma regra de gatilho (global se `cliente_id` for nulo, individual caso contrário) com
    suas condições. Globais e individuais são sempre avaliadas juntas pra um cliente."""

    async with get_session() as session:
        if dados.cliente_id is not None:
            cliente = await session.get(Cliente, dados.cliente_id)
            if cliente is None:
                raise HTTPException(404, f"Cliente {dados.cliente_id} não tem nenhuma coleta registrada")

        gatilho = Gatilho(
            nome=dados.nome,
            cliente_id=dados.cliente_id,
            combinador=dados.combinador,
            ativo=dados.ativo,
            severidade=dados.severidade,
            condicoes=_condicoes_orm(dados.condicoes),
        )
        session.add(gatilho)
        await session.commit()
        await session.refresh(gatilho, attribute_names=["condicoes"])
        return gatilho


@router.get("", response_model=GatilhosResponse)
async def listar_gatilhos(
    cliente_id: int | None = Query(
        None, description="Inclui as regras individuais desse cliente, além das globais"
    ),
    ativo: bool | None = Query(None, description="Filtra por regras ativas/inativas"),
) -> GatilhosResponse:
    async with get_session() as session:
        stmt = select(Gatilho).options(selectinload(Gatilho.condicoes))
        if cliente_id is not None:
            stmt = stmt.where((Gatilho.cliente_id.is_(None)) | (Gatilho.cliente_id == cliente_id))
        if ativo is not None:
            stmt = stmt.where(Gatilho.ativo == ativo)
        stmt = stmt.order_by(Gatilho.criado_em.desc())

        linhas = (await session.execute(stmt)).scalars().all()

    return GatilhosResponse(registros=len(linhas), gatilhos=[GatilhoResponse.model_validate(g) for g in linhas])


@router.get("/{gatilho_id}", response_model=GatilhoResponse)
async def obter_gatilho(gatilho_id: int) -> Gatilho:
    async with get_session() as session:
        stmt = select(Gatilho).where(Gatilho.id == gatilho_id).options(selectinload(Gatilho.condicoes))
        gatilho = (await session.execute(stmt)).scalar_one_or_none()
        if gatilho is None:
            raise HTTPException(404, f"Gatilho {gatilho_id} não encontrado")
        return gatilho


@router.put("/{gatilho_id}", response_model=GatilhoResponse)
async def atualizar_gatilho(gatilho_id: int, dados: GatilhoUpdate) -> Gatilho:
    """Substitui nome/combinador/ativo e a lista de condições inteira (as condições antigas são
    apagadas via cascade — mais simples e correto pra CRUD aninhado do que um merge campo a campo)."""

    async with get_session() as session:
        stmt = select(Gatilho).where(Gatilho.id == gatilho_id).options(selectinload(Gatilho.condicoes))
        gatilho = (await session.execute(stmt)).scalar_one_or_none()
        if gatilho is None:
            raise HTTPException(404, f"Gatilho {gatilho_id} não encontrado")

        gatilho.nome = dados.nome
        gatilho.combinador = dados.combinador
        gatilho.ativo = dados.ativo
        gatilho.severidade = dados.severidade
        gatilho.condicoes = _condicoes_orm(dados.condicoes)

        await session.commit()
        # `atualizado_em` usa onupdate=func.now() (computado pelo Postgres): sempre que o UPDATE
        # muda algo de verdade, o SQLAlchemy marca esse atributo como expirado. Sem incluí-lo aqui,
        # a serialização da resposta (que acontece já fora deste `async with`, com a sessão
        # fechada) tenta recarregar um atributo expirado sem sessão e quebra com
        # DetachedInstanceError -> 500 — mesmo com o commit já persistido com sucesso.
        await session.refresh(gatilho, attribute_names=["condicoes", "atualizado_em"])
        return gatilho


@router.delete("/{gatilho_id}", status_code=204)
async def desativar_gatilho(gatilho_id: int) -> None:
    """Soft delete (`ativo=False`): uma regra que já disparou tem histórico em `alertas_disparados`
    referenciando-a, então apagar a linha de verdade é bloqueado por FK de propósito."""

    async with get_session() as session:
        gatilho = await session.get(Gatilho, gatilho_id)
        if gatilho is None:
            raise HTTPException(404, f"Gatilho {gatilho_id} não encontrado")
        gatilho.ativo = False
        await session.commit()
