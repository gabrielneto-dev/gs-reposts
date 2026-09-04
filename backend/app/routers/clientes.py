import asyncio
from datetime import date, time, timedelta

from fastapi import APIRouter, HTTPException, Query

from app.clients.nextrouter import (
    NextRouterAPIError,
    get_cdr_aggregate,
    get_contacts,
    get_disconnection_sample,
    periodo_params,
    scan_active_customer_ids,
)
from app.schemas.asr import Periodo
from app.schemas.cliente import (
    ClienteAtividadeResponse,
    ClienteBase,
    ClienteBuscaResponse,
    ClienteComRecorrencia,
    ClienteComSimilaridade,
    ClienteComVolume,
    ClienteListaResponse,
    ClienteRecorrenciaResponse,
)
from app.utils.fuzzy import similaridade_nome

router = APIRouter(prefix="/api/clientes", tags=["Clientes"])

TAMANHO_PAGINA_BUSCA = 500
MAX_PAGINAS_BUSCA = 40  # limite de segurança: até 20.000 clientes escaneados por busca/lookup
MAX_DIAS_RECORRENCIA = 31  # limite de segurança pra /recorrencia
CONCORRENCIA_MAXIMA_DIAS = 5  # dias escaneados em paralelo, pra não martelar a API de produção


def _cliente_base(item: dict) -> ClienteBase:
    contact = item.get("contact") or {}
    address = item.get("address") or {}

    return ClienteBase(
        id=item["id"],
        tipo=item.get("type", ""),
        tipo_descricao=item.get("type_desc", ""),
        nome_fantasia=item.get("nome_fantasia", ""),
        razao_social=item.get("razao_social", ""),
        telefone=contact.get("mobile") or contact.get("phone1") or None,
        email=contact.get("email1") or None,
        cidade=address.get("city") or None,
        estado=address.get("state") or None,
        status=item.get("status", 0),
        usuarios=item.get("users", []),
    )


async def _buscar_clientes_por_id(ids: set[int]) -> dict[int, dict]:
    """Pagina /api/contacts procurando os itens crus (dict) cujos ids estão em `ids`, parando
    assim que todos forem encontrados ou a base acabar."""

    faltando = set(ids)
    encontrados: dict[int, dict] = {}

    for pagina in range(MAX_PAGINAS_BUSCA):
        if not faltando:
            break
        payload = await get_contacts(start=pagina * TAMANHO_PAGINA_BUSCA, limit=TAMANHO_PAGINA_BUSCA)
        itens = payload.get("data", [])
        for item in itens:
            if item["id"] in faltando:
                encontrados[item["id"]] = item
                faltando.discard(item["id"])
        if len(itens) < TAMANHO_PAGINA_BUSCA:
            break

    return encontrados


async def _ranking_do_dia(
    dia: date, hora_inicio: time | None, hora_fim: time | None, amostra_atividade: int, semaforo: asyncio.Semaphore
) -> tuple[date, list[tuple[int, int]]]:
    async with semaforo:
        ranking = await scan_active_customer_ids(
            periodo=periodo_params(dia, dia, hora_inicio, hora_fim), limite_scan=amostra_atividade
        )
    return dia, ranking


async def _atividade_exata_do_dia(
    cliente_id: int, dia: date, hora_inicio: time | None, hora_fim: time | None, semaforo: asyncio.Semaphore
) -> tuple[date, int]:
    """Checa se UM cliente específico teve atividade num dia, sem baixar chamada nenhuma: usa
    limit=1 em /api/cdr e /api/cdrDisconnection e olha só o total_records (exato, não amostrado)."""

    periodo = periodo_params(dia, dia, hora_inicio, hora_fim)
    async with semaforo:
        atendidas, falhas = await asyncio.gather(
            get_cdr_aggregate(cliente_id=cliente_id, periodo=periodo),
            get_disconnection_sample(cliente_id=cliente_id, periodo=periodo, limit=1),
        )
    return dia, atendidas["total_records"] + falhas["total_records"]


@router.get("", response_model=ClienteListaResponse)
async def listar_clientes(
    start: int = Query(0, ge=0, description="Deslocamento (offset) para paginação"),
    limit: int = Query(50, ge=1, le=500, description="Clientes por página"),
) -> ClienteListaResponse:
    """Listagem crua dos clientes/assinantes cadastrados na plataforma (agenda de contatos),
    paginada, na ordem que a API do NextRouter retorna. Sem relação com uso/atividade."""

    try:
        payload = await get_contacts(start=start, limit=limit)
    except NextRouterAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    clientes = [_cliente_base(item) for item in payload.get("data", [])]
    return ClienteListaResponse(
        offset=payload.get("offset", start),
        limit=payload.get("limit", limit),
        registros=payload.get("records", len(clientes)),
        clientes=clientes,
    )


@router.get("/busca", response_model=ClienteBuscaResponse)
async def buscar_clientes_por_nome(
    nome: str = Query(..., description="Termo buscado no nome fantasia ou na razão social"),
    limiar: float = Query(60.0, ge=0, le=100, description="Similaridade mínima (%) para considerar um resultado"),
    max_resultados: int = Query(20, ge=1, le=200, description="Máximo de resultados, ordenados por similaridade"),
) -> ClienteBuscaResponse:
    """Busca aproximada (fuzzy) por nome/razão social — tolera nomes parciais e pequenas
    diferenças de digitação. Não tem relação com uso/atividade."""

    encontrados: list[ClienteComSimilaridade] = []
    pagina = 0
    aviso: str | None = None

    while pagina < MAX_PAGINAS_BUSCA:
        try:
            payload = await get_contacts(start=pagina * TAMANHO_PAGINA_BUSCA, limit=TAMANHO_PAGINA_BUSCA)
        except NextRouterAPIError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        itens = payload.get("data", [])
        for item in itens:
            score = max(
                similaridade_nome(nome, item.get("nome_fantasia", "")),
                similaridade_nome(nome, item.get("razao_social", "")),
            )
            if score >= limiar:
                encontrados.append(ClienteComSimilaridade(**_cliente_base(item).model_dump(), similaridade=score))

        pagina += 1
        if len(itens) < TAMANHO_PAGINA_BUSCA:
            break
    else:
        aviso = (
            f"Busca interrompida após escanear {MAX_PAGINAS_BUSCA * TAMANHO_PAGINA_BUSCA} clientes "
            "(limite de segurança). Pode haver mais resultados na base."
        )

    encontrados.sort(key=lambda c: c.similaridade, reverse=True)
    encontrados = encontrados[:max_resultados]

    return ClienteBuscaResponse(registros=len(encontrados), clientes=encontrados, aviso=aviso)


@router.get("/atividade", response_model=ClienteAtividadeResponse)
async def clientes_ativos_no_periodo(
    data_inicio: date = Query(..., description="Início do período"),
    data_fim: date | None = Query(None, description="Fim do período (padrão: igual a data_inicio)"),
    hora_inicio: time | None = Query(None, description="Hora inicial do período (HH:MM)"),
    hora_fim: time | None = Query(None, description="Hora final do período (HH:MM)"),
    amostra_atividade: int = Query(
        3000,
        ge=1,
        le=10000,
        description=(
            "Registros escaneados por endpoint (cdr e cdrDisconnection) pra detectar quem teve "
            "atividade. Em janelas longas (dias/semanas) pode não representar o período inteiro de "
            "forma uniforme — prefira janelas curtas, aumente esse valor, ou use /recorrencia."
        ),
    ),
    limit: int = Query(50, ge=1, le=500, description="Nº máximo de clientes retornados, ordenados por volume"),
) -> ClienteAtividadeResponse:
    """Clientes com chamada (atendida ou falha) em UMA janela de data/hora, ordenados por volume
    na amostra. Detecção por amostragem — a API não tem um "distinct customer" pronto."""

    periodo = periodo_params(data_inicio, data_fim or data_inicio, hora_inicio, hora_fim)

    try:
        ranking = await scan_active_customer_ids(periodo=periodo, limite_scan=amostra_atividade)
    except NextRouterAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    selecionados = ranking[:limit]

    try:
        itens_por_id = await _buscar_clientes_por_id({cid for cid, _ in selecionados})
    except NextRouterAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    clientes = [
        ClienteComVolume(**_cliente_base(itens_por_id[cid]).model_dump(), chamadas_na_amostra=contagem)
        for cid, contagem in selecionados
        if cid in itens_por_id
    ]

    dias = (data_fim - data_inicio).days if data_fim else 0
    aviso = (
        "Detecção de atividade é por amostragem (escaneia até "
        f"{amostra_atividade} registros por endpoint, não o período inteiro). Em janelas de mais de "
        "1 dia pode não representar todo o intervalo uniformemente — prefira janelas curtas, aumente "
        "`amostra_atividade`, ou use /api/clientes/recorrencia."
        if dias >= 1
        else None
    )

    return ClienteAtividadeResponse(
        periodo=Periodo(data_inicio=data_inicio, data_fim=data_fim or data_inicio, hora_inicio=hora_inicio, hora_fim=hora_fim),
        registros=len(clientes),
        clientes=clientes,
        aviso=aviso,
    )


@router.get("/recorrencia", response_model=ClienteRecorrenciaResponse)
async def clientes_recorrentes(
    dias_minimos: int = Query(..., ge=1, description="Nº mínimo de dias distintos com atividade dentro do período"),
    janela_dias: int | None = Query(
        None,
        ge=1,
        le=31,
        description=(
            "Atalho: verifica os últimos `janela_dias` dias a partir de hoje (inclusive), sem "
            "precisar informar data_inicio/data_fim. Ex: janela_dias=7 + dias_minimos=3 = 'usou "
            "pelo menos 3 dos últimos 7 dias'. Não combine com data_inicio/data_fim."
        ),
    ),
    data_inicio: date | None = Query(None, description="Início do período. Alternativa a janela_dias."),
    data_fim: date | None = Query(None, description="Fim do período. Alternativa a janela_dias."),
    cliente_id: int | None = Query(
        None,
        description=(
            "Se informado, checa só esse cliente (leve e exato: usa limit=1 por dia, sem baixar "
            "chamada nenhuma, sem amostragem). Se omitido, descobre todos os clientes recorrentes "
            "da base (mais pesado, por amostragem)."
        ),
    ),
    hora_inicio: time | None = Query(None, description="Hora inicial aplicada em CADA dia do período (HH:MM)"),
    hora_fim: time | None = Query(None, description="Hora final aplicada em CADA dia do período (HH:MM)"),
    amostra_atividade: int = Query(
        3000,
        ge=1,
        le=10000,
        description="Registros escaneados por endpoint (cdr e cdrDisconnection), por dia do período. Ignorado se cliente_id for passado.",
    ),
    limit: int = Query(50, ge=1, le=500, description="Nº máximo de clientes retornados, ordenados por dias ativos"),
) -> ClienteRecorrenciaResponse:
    """Clientes com atividade em pelo menos `dias_minimos` dias DISTINTOS dentro do período.

    O período vem de `janela_dias` (últimos N dias a partir de hoje) OU de `data_inicio`+`data_fim`
    explícitos — informe um dos dois, não os dois juntos.

    Com `cliente_id`: checagem leve e exata (limit=1 por dia, sem amostragem) — é só "esse cliente
    usou nesse dia ou não". Sem `cliente_id`: descobre todos os clientes recorrentes da base,
    escaneando dia a dia por amostragem (mais pesado, mais preciso que /atividade em períodos longos)."""

    if janela_dias is not None:
        if data_inicio is not None or data_fim is not None:
            raise HTTPException(400, "Use janela_dias OU data_inicio/data_fim, não os dois")
        data_fim = date.today()
        data_inicio = data_fim - timedelta(days=janela_dias - 1)
    elif data_inicio is None or data_fim is None:
        raise HTTPException(400, "Informe janela_dias OU (data_inicio e data_fim)")

    if data_fim < data_inicio:
        raise HTTPException(400, "data_fim não pode ser anterior a data_inicio")

    total_dias = (data_fim - data_inicio).days + 1
    if total_dias > MAX_DIAS_RECORRENCIA:
        raise HTTPException(400, f"Período de {total_dias} dias excede o limite de {MAX_DIAS_RECORRENCIA} dias")
    if dias_minimos > total_dias:
        raise HTTPException(400, f"dias_minimos ({dias_minimos}) não pode ser maior que o período ({total_dias} dias)")

    dias_do_periodo = [data_inicio + timedelta(days=i) for i in range(total_dias)]
    semaforo = asyncio.Semaphore(CONCORRENCIA_MAXIMA_DIAS)

    if cliente_id is not None:
        try:
            resultados_exatos = await asyncio.gather(
                *[_atividade_exata_do_dia(cliente_id, dia, hora_inicio, hora_fim, semaforo) for dia in dias_do_periodo]
            )
        except NextRouterAPIError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        datas_ativas = [dia for dia, total in resultados_exatos if total > 0]
        total_chamadas = sum(total for _, total in resultados_exatos)

        clientes: list[ClienteComRecorrencia] = []
        if len(datas_ativas) >= dias_minimos:
            try:
                itens_por_id = await _buscar_clientes_por_id({cliente_id})
            except NextRouterAPIError as exc:
                raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

            if cliente_id in itens_por_id:
                clientes = [
                    ClienteComRecorrencia(
                        **_cliente_base(itens_por_id[cliente_id]).model_dump(),
                        chamadas_na_amostra=total_chamadas,
                        dias_ativos=len(datas_ativas),
                        datas_ativas=datas_ativas,
                    )
                ]

        return ClienteRecorrenciaResponse(
            data_inicio=data_inicio,
            data_fim=data_fim,
            dias_minimos=dias_minimos,
            registros=len(clientes),
            clientes=clientes,
            aviso="Checagem exata (não amostrada) — cliente_id foi informado.",
        )

    try:
        resultados = await asyncio.gather(
            *[_ranking_do_dia(dia, hora_inicio, hora_fim, amostra_atividade, semaforo) for dia in dias_do_periodo]
        )
    except NextRouterAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    datas_por_cliente: dict[int, list[date]] = {}
    chamadas_por_cliente: dict[int, int] = {}
    for dia, ranking in resultados:
        for cid, contagem in ranking:
            datas_por_cliente.setdefault(cid, []).append(dia)
            chamadas_por_cliente[cid] = chamadas_por_cliente.get(cid, 0) + contagem

    recorrentes = [cid for cid, datas in datas_por_cliente.items() if len(datas) >= dias_minimos]
    recorrentes.sort(key=lambda cid: len(datas_por_cliente[cid]), reverse=True)
    recorrentes = recorrentes[:limit]

    try:
        itens_por_id = await _buscar_clientes_por_id(set(recorrentes))
    except NextRouterAPIError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    clientes = [
        ClienteComRecorrencia(
            **_cliente_base(itens_por_id[cid]).model_dump(),
            chamadas_na_amostra=chamadas_por_cliente[cid],
            dias_ativos=len(datas_por_cliente[cid]),
            datas_ativas=sorted(datas_por_cliente[cid]),
        )
        for cid in recorrentes
        if cid in itens_por_id
    ]

    aviso = (
        f"Detecção por amostragem (até {amostra_atividade} registros/endpoint por dia) — clientes de "
        "baixo volume podem não aparecer em todos os dias em que realmente tiveram atividade. Pra um "
        "cliente específico, passe cliente_id pra uma checagem exata e mais leve."
    )

    return ClienteRecorrenciaResponse(
        data_inicio=data_inicio, data_fim=data_fim, dias_minimos=dias_minimos, registros=len(clientes), clientes=clientes, aviso=aviso
    )
