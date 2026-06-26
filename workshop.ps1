#Requires -Version 5.1
# If you get "running scripts is disabled", run once:
#   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser

param(
    [Parameter(Position = 0)]
    [string]$Command = "help"
)

$BACKEND_HOST = "127.0.0.1"
$BACKEND_PORT = 8040
$FRONTEND_PORT = 3040
$DOMAIN = "digital-native"

if (Test-Path .env) {
    Get-Content .env | ForEach-Object {
        if ($_ -match '^DEMO_DOMAIN=(.+)') { $script:DOMAIN = $Matches[1].Trim() }
        if ($_ -match '^BACKEND_HOST=(.+)') { $script:BACKEND_HOST = $Matches[1].Trim() }
        if ($_ -match '^BACKEND_PORT=(.+)') { $script:BACKEND_PORT = $Matches[1].Trim() }
        if ($_ -match '^FRONTEND_PORT=(.+)') { $script:FRONTEND_PORT = $Matches[1].Trim() }
    }
}

function Confirm-Uv {
    if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
        Write-Host "Error: uv not found. Install it from https://docs.astral.sh/uv/getting-started/installation/"
        Write-Host "After installing, restart your terminal so it's on your PATH."
        exit 1
    }
}

function Show-Help {
    Write-Host ""
    Write-Host "  Redis Iris Workshop"
    Write-Host "  ─────────────────────────────────────────"
    Write-Host ""
    Write-Host "  Setup:"
    Write-Host "    .\workshop.ps1 install          Install backend + frontend dependencies"
    Write-Host "    .\workshop.ps1 dev              Run backend + frontend"
    Write-Host ""
    Write-Host "  Data (run in module order):"
    Write-Host "    .\workshop.ps1 seed-data        Module 0 — Load policies into Redis for Simple RAG"
    Write-Host "    .\workshop.ps1 setup-surface    Module 3 — Create Context Surface + agent key"
    Write-Host "    .\workshop.ps1 load-data        Module 3 — Load all entities via Context Surfaces"
    Write-Host "    .\workshop.ps1 seed-langcache   Module 4 — Seed one LangCache entry"
    Write-Host "    .\workshop.ps1 seed-memories    Module 5 — Seed long-term memories"
    Write-Host ""
    Write-Host "  Utilities:"
    Write-Host "    .\workshop.ps1 status           Check which modules are active"
    Write-Host "    .\workshop.ps1 reset            Flush Redis + re-seed everything"
    Write-Host ""
}

switch ($Command) {
    "help" {
        Show-Help
    }
    "install" {
        Confirm-Uv
        uv sync
        Push-Location frontend
        npm install
        Pop-Location
    }
    "backend" {
        Confirm-Uv
        uv run uvicorn backend.app.main:app --reload --host $BACKEND_HOST --port $BACKEND_PORT
    }
    "frontend" {
        Push-Location frontend
        npm run dev -- --host 0.0.0.0 --port $FRONTEND_PORT
        Pop-Location
    }
    "dev" {
        Write-Host ""
        Write-Host "  ======================================================"
        Write-Host "   Redis Iris Workshop"
        Write-Host ""
        Write-Host "   Workshop Guide:  https://redis-iris-workshop.vercel.app"
        Write-Host "   App:             http://localhost:$FRONTEND_PORT"
        Write-Host "   API:             http://localhost:$BACKEND_PORT"
        Write-Host "  ======================================================"
        Write-Host ""
        Write-Host "  Press Ctrl+C to stop both servers."
        Write-Host ""

        Confirm-Uv
        $uvPath = (Get-Command uv).Source
        $npmCmd = Get-Command npm.cmd -ErrorAction SilentlyContinue
        if (-not $npmCmd) { $npmCmd = Get-Command npm -ErrorAction SilentlyContinue }
        if (-not $npmCmd) { Write-Host "Error: npm not found. Install Node.js from https://nodejs.org/"; exit 1 }
        $npmPath = $npmCmd.Source

        $backendProc = Start-Process -NoNewWindow -PassThru -FilePath $uvPath `
            -ArgumentList "run", "uvicorn", "backend.app.main:app", "--reload", "--host", $BACKEND_HOST, "--port", $BACKEND_PORT
        $frontendProc = Start-Process -NoNewWindow -PassThru -FilePath "cmd.exe" `
            -ArgumentList "/c", "`"$npmPath`"", "run", "dev", "--", "--host", "0.0.0.0", "--port", $FRONTEND_PORT `
            -WorkingDirectory (Join-Path $PWD "frontend")

        try {
            while (-not $backendProc.HasExited -and -not $frontendProc.HasExited) {
                Start-Sleep -Milliseconds 500
            }
        }
        finally {
            if (-not $backendProc.HasExited) { Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue }
            if (-not $frontendProc.HasExited) { Stop-Process -Id $frontendProc.Id -Force -ErrorAction SilentlyContinue }
        }
    }
    "seed-data" {
        Confirm-Uv
        uv run python scripts/seed_data.py --domain $DOMAIN
    }
    "setup-surface" {
        Confirm-Uv
        uv run python scripts/setup_surface.py --domain $DOMAIN
    }
    "load-data" {
        Confirm-Uv
        uv run python scripts/load_data.py --domain $DOMAIN
    }
    "setup-context" {
        Confirm-Uv
        uv run python scripts/setup_surface.py --domain $DOMAIN
        if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
        uv run python scripts/load_data.py --domain $DOMAIN
    }
    "seed-langcache" {
        Confirm-Uv
        uv run python -m scripts.seed_langcache --domain $DOMAIN
    }
    "seed-memories" {
        Confirm-Uv
        uv run python -m scripts.seed_memories --domain $DOMAIN
    }
    "status" {
        try {
            $response = Invoke-RestMethod -Uri "http://${BACKEND_HOST}:${BACKEND_PORT}/api/status"
            $response | ConvertTo-Json -Depth 10
        }
        catch {
            Write-Host "Could not reach the API. Is the server running? (.\workshop.ps1 dev)"
        }
    }
    "flush-redis" {
        Confirm-Uv
        uv run python scripts/flush_redis.py
    }
    "reset" {
        Confirm-Uv
        uv run python scripts/flush_redis.py
        Write-Host "Re-seeding policy data..."
        uv run python scripts/seed_data.py --domain $DOMAIN
        Write-Host ""
        Write-Host "Reset complete. Run '.\workshop.ps1 dev' to start."
    }
    "generate-models" {
        Confirm-Uv
        uv run python scripts/generate_models.py --domain $DOMAIN
    }
    "generate-data" {
        Confirm-Uv
        uv run python scripts/generate_data.py --domain $DOMAIN
    }
    default {
        Write-Host "Unknown command: $Command"
        Write-Host ""
        Show-Help
    }
}
