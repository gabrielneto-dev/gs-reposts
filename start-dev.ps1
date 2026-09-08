# Sobe backend (FastAPI/uvicorn) e frontend (Next.js) em janelas separadas do PowerShell.
# Uso:  .\start-dev.ps1
# Se der erro de "execution policy", rode uma vez:
#   powershell -ExecutionPolicy Bypass -File .\start-dev.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

$backendPython = Join-Path $root "backend\.venv\Scripts\python.exe"
if (-not (Test-Path $backendPython)) {
    Write-Error "Venv do backend nao encontrado em $backendPython. Rode primeiro: cd backend; python -m venv .venv; .venv\Scripts\pip install -r requirements.txt"
    exit 1
}

$pgService = Get-Service -Name "postgresql-x64-17" -ErrorAction SilentlyContinue
if ($pgService -and $pgService.Status -ne "Running") {
    Write-Warning "Servico do Postgres (postgresql-x64-17) nao esta rodando - o backend (banco + scheduler) vai falhar ao conectar."
}

Write-Host "Subindo backend em nova janela (porta 8000, docs em /docs)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\backend'; & '$backendPython' -m uvicorn app.main:app --reload"
)

Write-Host "Subindo frontend em nova janela (porta 3000)" -ForegroundColor Cyan
Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "Set-Location '$root\frontend'; npm run dev"
)

Write-Host "Pronto. Feche as janelas (ou Ctrl+C dentro delas) para parar cada servidor." -ForegroundColor Green
