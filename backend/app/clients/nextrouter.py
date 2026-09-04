import asyncio
from datetime import date, time
from typing import Any

import httpx

from app.config import settings


class NextRouterAPIError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def _base_url() -> str:
    base_url = settings.softswitch_api_url.rstrip("/")
    if not base_url.startswith(("http://", "https://")):
        base_url = f"https://{base_url}"
    return base_url


async def _get(client: httpx.AsyncClient, path: str, cliente_id: int | None, params: dict[str, Any]) -> dict[str, Any]:
    url = f"{_base_url()}/api/{path}/{settings.softswitch_api_token}/{settings.softswitch_api_key}"
    if cliente_id is not None:
        url += f"/{cliente_id}"

    try:
        response = await client.get(url, params=params)
    except httpx.RequestError as exc:
        raise NextRouterAPIError(502, f"Falha ao conectar com a API do softswitch: {exc}") from exc

    if response.status_code >= 400:
        try:
            message = response.json().get("error", response.text)
        except ValueError:
            message = response.text
        raise NextRouterAPIError(response.status_code, message)

    body = response.json()
    if body.get("error"):
        raise NextRouterAPIError(502, body.get("reason", "Erro desconhecido na API do softswitch"))

    return body


def periodo_params(
    data_inicio: date | None, data_fim: date | None, hora_inicio: time | None, hora_fim: time | None
) -> dict[str, Any]:
    params: dict[str, Any] = {}
    if data_inicio is not None:
        params["date_ini"] = data_inicio.isoformat()
    if data_fim is not None:
        params["date_end"] = data_fim.isoformat()
    if hora_inicio is not None:
        params["time_ini"] = hora_inicio.strftime("%H:%M:%S")
    if hora_fim is not None:
        params["time_end"] = hora_fim.strftime("%H:%M:%S")
    return params


async def get_cdr_aggregate(*, cliente_id: int | None, periodo: dict[str, Any]) -> dict[str, Any]:
    """/api/cdr: chamadas atendidas/tarifadas. Com limit=1, `total_records`/`total_time` já vêm
    prontos (exato, sem precisar baixar registro por registro) — base do ACD e do lado "200 OK" do ASR."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        return await _get(client, "cdr", cliente_id, {**periodo, "limit": 1})


async def get_disconnection_sample(*, cliente_id: int | None, periodo: dict[str, Any], limit: int) -> dict[str, Any]:
    """/api/cdrDisconnection: chamadas com falha. `total_records` é exato; os registros individuais
    (até `limit`) são a amostra usada pro PDD e pro detalhamento por código (487, 486, etc.), já que
    a API não tem agregado nem filtro por disposição/sip_code prontos."""

    async with httpx.AsyncClient(timeout=60.0) as client:
        return await _get(client, "cdrDisconnection", cliente_id, {**periodo, "limit": limit})


TAMANHO_PAGINA_EXATO = 10000  # maior limit aceito pela API sem ser cortado silenciosamente pra 200
MAX_PAGINAS_EXATO = 100  # limite de segurança: até 1.000.000 de registros de falha por consulta


async def get_disconnection_full(
    *, cliente_id: int | None, periodo: dict[str, Any], max_paginas: int = MAX_PAGINAS_EXATO
) -> dict[str, Any]:
    """Pagina TODOS os registros de /api/cdrDisconnection do período (sem amostragem), sequencial
    (uma página por vez, pra não martelar a API com várias requisições grandes em paralelo).

    Retorna `total_records` (total real), a lista completa de `data` e `truncado` (True se bateu
    no limite de segurança de páginas antes de esgotar o período)."""

    total_records: int | None = None
    registros: list[dict[str, Any]] = []
    truncado = False

    async with httpx.AsyncClient(timeout=60.0) as client:
        for pagina in range(max_paginas):
            payload = await _get(
                client,
                "cdrDisconnection",
                cliente_id,
                {**periodo, "limit": TAMANHO_PAGINA_EXATO, "start": pagina * TAMANHO_PAGINA_EXATO},
            )
            if total_records is None:
                total_records = payload.get("total_records", 0)

            pagina_registros = payload.get("data", [])
            registros.extend(pagina_registros)

            if len(pagina_registros) < TAMANHO_PAGINA_EXATO:
                break
        else:
            truncado = True

    return {"total_records": total_records or 0, "data": registros, "truncado": truncado}


async def get_asr_data(
    *,
    cliente_id: int | None,
    data_inicio: date | None,
    data_fim: date | None,
    hora_inicio: time | None,
    hora_fim: time | None,
    amostra_falhas: int,
) -> dict[str, Any]:
    """Busca em paralelo o agregado de atendidas (/api/cdr) e a amostra de falhas
    (/api/cdrDisconnection), base para o ASR exato e o detalhamento por código de falha."""

    periodo = periodo_params(data_inicio, data_fim, hora_inicio, hora_fim)

    async with httpx.AsyncClient(timeout=60.0) as client:
        atendidas, falhas = await asyncio.gather(
            _get(client, "cdr", cliente_id, {**periodo, "limit": 1}),
            _get(client, "cdrDisconnection", cliente_id, {**periodo, "limit": amostra_falhas}),
        )

    return {"atendidas": atendidas, "falhas": falhas}


async def get_contacts(*, start: int = 0, limit: int = 50) -> dict[str, Any]:
    """Consulta /api/contacts: agenda com todos os clientes cadastrados na plataforma."""

    async with httpx.AsyncClient(timeout=30.0) as client:
        return await _get(client, "contacts", None, {"start": start, "limit": limit})


async def scan_active_customer_ids(*, periodo: dict[str, Any], limite_scan: int = 3000) -> list[tuple[int, int]]:
    """Amostra /api/cdr e /api/cdrDisconnection SEM filtro de cliente na janela informada e conta
    quantas vezes cada `customer_id` aparece na amostra — proxy de "quem teve tráfego" e de volume
    relativo, sem precisar checar cliente por cliente (a API não tem um "distinct customer" pronto).

    Retorna [(cliente_id, ocorrencias_na_amostra), ...] ordenado do maior volume pro menor. Em
    janelas longas (dias/semanas) a amostra pode não cobrir o período inteiro de forma uniforme.
    """

    async with httpx.AsyncClient(timeout=60.0) as client:
        atendidas, falhas = await asyncio.gather(
            _get(client, "cdr", None, {**periodo, "limit": limite_scan}),
            _get(client, "cdrDisconnection", None, {**periodo, "limit": limite_scan}),
        )

    contagem: dict[int, int] = {}
    for registro in [*atendidas.get("data", []), *falhas.get("data", [])]:
        cid = registro.get("customer_id")
        if cid is None:
            continue
        contagem[cid] = contagem.get(cid, 0) + 1

    return sorted(contagem.items(), key=lambda item: item[1], reverse=True)
