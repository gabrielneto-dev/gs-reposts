from fastapi import FastAPI

from app.routers import acd, asr, clientes, pdd

app = FastAPI(
    title="Relatorios API",
    description="API de relatórios de telefonia (ASR, ACD, PDD) integrada ao NextRouter SoftSwitch.",
)

app.include_router(asr.router)
app.include_router(acd.router)
app.include_router(pdd.router)
app.include_router(clientes.router)


@app.get("/health", tags=["Health"])
async def health() -> dict[str, str]:
    return {"status": "ok"}
