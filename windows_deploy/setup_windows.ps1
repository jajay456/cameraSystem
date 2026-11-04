param(
  [switch]$SkipPrerequisites
)
$ErrorActionPreference = "Stop"
$root = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location $root

function Require-Command($name, $hint) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    throw "$name is required. $hint"
  }
}

function Install-WingetPackage($id, $name) {
  if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
    Write-Host "Installing $name ($id)..."
    winget install --id $id --exact --accept-source-agreements --accept-package-agreements
  }
}

if (-not $SkipPrerequisites) {
  Require-Command "winget" "Install App Installer from the Microsoft Store."
  Install-WingetPackage "Python.Python.3.11" "python"
  Install-WingetPackage "OpenJS.NodeJS.LTS" "node"
  Install-WingetPackage "EclipseAdoptium.Temurin.21.JDK" "java"
  Install-WingetPackage "Gyan.FFmpeg.Shared" "ffmpeg"
  Install-WingetPackage "Cloudflare.cloudflared" "cloudflared"
  Install-WingetPackage "NSSM.NSSM" "nssm"
  if (-not (Get-Command firebase -ErrorAction SilentlyContinue)) {
    npm install --global firebase-tools
  }
  if (-not (Get-Command mediamtx -ErrorAction SilentlyContinue)) {
    throw "MediaMTX was not found. Download mediamtx.exe from https://github.com/bluenviron/mediamtx/releases, add its folder to PATH, then rerun this script."
  }
}

$env:Path = @(
  [Environment]::GetEnvironmentVariable("Path", "Machine"),
  [Environment]::GetEnvironmentVariable("Path", "User"),
  $env:Path
) -join ";"

Require-Command "python" "Install Python 3.11 and enable 'Add to PATH'."
Require-Command "node" "Install Node.js LTS."
Require-Command "npm" "Install Node.js LTS."
Require-Command "ffmpeg" "Install FFmpeg and add its bin directory to PATH."
Require-Command "mediamtx" "Install MediaMTX and add it to PATH."
Require-Command "java" "Install Java 21 or newer."
Require-Command "cloudflared" "Install cloudflared."
Require-Command "firebase" "Install Firebase CLI with: npm install --global firebase-tools."
Require-Command "nssm" "Install NSSM and add its folder to PATH."

if (-not (Test-Path ".env")) {
  Copy-Item ".env.example" ".env"
  Write-Warning "Created .env. Fill CAMERA_RTSP_URL, R2 credentials, TEST_API_KEY, and FIRESTORE settings before continuing."
  exit 2
}

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  python -m venv .venv
}
& .venv\Scripts\python.exe -m pip install --upgrade pip
& .venv\Scripts\pip.exe install -r requirements.txt
& npm install --prefix functions
& npm run build --prefix functions

if (-not (Test-Path "firebase.json")) {
  throw "firebase.json is missing."
}

Write-Host "Dependencies and builds passed."
Write-Host "Next: configure a named Cloudflare tunnel, then run windows_deploy\install_local_services.bat as Administrator."
Write-Host "No production deploy was run."
