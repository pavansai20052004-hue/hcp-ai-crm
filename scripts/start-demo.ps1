param(
    [switch]$UseSqlite
)

$Root = Split-Path -Parent $PSScriptRoot
$Backend = Join-Path $Root "backend"
$Frontend = Join-Path $Root "frontend"

if ($UseSqlite) {
    $env:DATABASE_URL = "sqlite:///./demo.db"
    Write-Host "Using SQLite demo database."
} else {
    Write-Host "Starting PostgreSQL with Docker Compose..."
    Push-Location $Root
    docker compose up -d db
    Pop-Location
}

if (-not (Test-Path (Join-Path $Backend ".venv"))) {
    Push-Location $Backend
    python -m venv .venv
    .\.venv\Scripts\python -m pip install -r requirements.txt
    Pop-Location
}

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    Push-Location $Frontend
    npm install
    Pop-Location
}

Start-Process -FilePath (Join-Path $Backend ".venv\Scripts\python.exe") `
    -ArgumentList "-m", "uvicorn", "app.main:app", "--reload", "--host", "127.0.0.1", "--port", "8000" `
    -WorkingDirectory $Backend

Start-Process -FilePath "npm.cmd" `
    -ArgumentList "run", "dev", "--", "--host", "127.0.0.1", "--port", "5173" `
    -WorkingDirectory $Frontend

Write-Host "Frontend: http://127.0.0.1:5173"
Write-Host "Backend docs: http://127.0.0.1:8000/docs"

