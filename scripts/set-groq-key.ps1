$Root = Split-Path -Parent $PSScriptRoot
$BackendEnv = Join-Path $Root "backend\.env"

$key = Read-Host "Paste your Groq API key"
if (-not $key -or $key.Trim().Length -lt 10) {
    Write-Error "No valid Groq API key was provided."
    exit 1
}

@"
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/hcp_crm
GROQ_API_KEY=$($key.Trim())
GROQ_MODEL=gemma2-9b-it
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
"@ | Set-Content -LiteralPath $BackendEnv -Encoding UTF8

Write-Host "Groq key saved to backend\.env. Do not commit this file."

