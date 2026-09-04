from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import acd, asr, clientes, metricas, pdd
from app.scheduler.scheduler import start_scheduler, stop_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="Relatorios API",
    description="API de relatórios de telefonia (ASR, ACD, PDD) integrada ao NextRouter SoftSwitch.",
    lifespan=lifespan,
)

app.include_router(asr.router)
app.include_router(acd.router)
app.include_router(pdd.router)
app.include_router(clientes.router)
app.include_router(metricas.router)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
