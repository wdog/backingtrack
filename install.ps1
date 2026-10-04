# backingtrack — installer per Windows (PowerShell)
#
#   irm https://raw.githubusercontent.com/wdog/backingtrack/main/install.ps1 | iex
#
# Variabili opzionali: $env:BT_BASS=1, $env:BT_NO_SAMPLES=1, $env:BT_REF="main"
$ErrorActionPreference = "Stop"
$Repo = "wdog/backingtrack"
$Ref = if ($env:BT_REF) { $env:BT_REF } else { "main" }
$Zip = "https://github.com/$Repo/archive/$Ref.zip"

function Step($m) { Write-Host "`n> $m" -ForegroundColor DarkYellow }
function Ok($m)   { Write-Host "  v $m" -ForegroundColor Green }
function Die($m)  { Write-Host "`nx $m" -ForegroundColor Red; exit 1 }
function Have($c) { [bool](Get-Command $c -ErrorAction SilentlyContinue) }

Write-Host "`n  backingtrack - rock · blues · rockabilly`n" -ForegroundColor DarkYellow

Step "Controllo il sistema"
$Py = $null
foreach ($c in @("py", "python", "python3")) {
    if (Have $c) {
        & $c -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $Py = $c; break }
    }
}
if (-not $Py) {
    if (Have winget) { winget install -e --id Python.Python.3.12; Die "Python installato: riapri PowerShell e rilancia" }
    Die "serve Python 3.8+ (https://www.python.org/downloads/)"
}
Ok "python: $(& $Py --version)"

if (Have ffmpeg) { Ok "ffmpeg trovato" }
elseif (Have winget) {
    winget install -e --id Gyan.FFmpeg
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
    if (-not (Have ffmpeg)) { Die "ffmpeg installato: riapri PowerShell e rilancia" }
    Ok "ffmpeg installato"
}
else { Die "installa ffmpeg (winget install Gyan.FFmpeg / choco install ffmpeg) e rilancia" }

Step "Installo backingtrack"
$Data = Join-Path $env:LOCALAPPDATA "backingtrack"
$Venv = Join-Path $Data "venv"
& $Py -m venv $Venv
$VPy = Join-Path $Venv "Scripts\python.exe"
& $VPy -m pip install -q --upgrade pip
& $VPy -m pip install -q --upgrade $Zip
$Scripts = Join-Path $Venv "Scripts"
$UserPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($UserPath -notlike "*$Scripts*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$Scripts", "User")
    $env:Path += ";$Scripts"
}
$Bt = Join-Path $Scripts "backingtrack.exe"
Ok "installato in $Venv"

if ($env:BT_NO_SAMPLES -ne "1") {
    Step "Scarico i campioni (chitarre + batteria + casse, ~460 MB)"
    if ($env:BT_BASS -eq "1") { & $Bt setup --bass } else { & $Bt setup }
}

Step "Fatto! Apri un nuovo terminale e prova:"
Write-Host "    backingtrack new mia_canzone.yaml"
Write-Host "    backingtrack mia_canzone.yaml --mp3`n"
