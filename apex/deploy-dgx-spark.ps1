<#
.SYNOPSIS
Deploy APEX from GitHub to a DGX Spark over SSH.

.DESCRIPTION
Run this script from Windows PowerShell. It connects to the Spark, clones or
updates the APEX repository, creates a Linux Python virtual environment,
installs APEX, runs its tests, creates a dedicated workspace, discovers the
model served by vLLM, and configures APEX to use it.

.EXAMPLE
.\deploy-dgx-spark.ps1

.EXAMPLE
.\deploy-dgx-spark.ps1 -SparkHost spark-fdc5.local

.EXAMPLE
.\deploy-dgx-spark.ps1 -Branch main -SkipTests
#>

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$SparkHost = "spark-fdc5",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$SparkUser = "ross",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$RepoUrl = "https://github.com/evanunrue-art/apex-agent.git",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$Branch = "main",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$InstallDir = "/home/ross/apps/apex-agent",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$WorkspaceDir = "/home/ross/apex-workspace",

    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$VllmEndpoint = "http://127.0.0.1:8000",

    [Parameter()]
    [switch]$SkipTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ssh = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $ssh) {
    throw "OpenSSH was not found. Install 'OpenSSH Client' in Windows Optional Features."
}

# These values become arguments to a remote Bash process. Restrict them to
# characters that cannot alter the remote shell command.
$remoteValues = [ordered]@{
    SparkHost    = $SparkHost
    SparkUser    = $SparkUser
    RepoUrl      = $RepoUrl
    Branch       = $Branch
    InstallDir   = $InstallDir
    WorkspaceDir = $WorkspaceDir
    VllmEndpoint = $VllmEndpoint
}

foreach ($item in $remoteValues.GetEnumerator()) {
    if ($item.Value -notmatch '^[A-Za-z0-9._~/:@+-]+$') {
        throw "$($item.Key) contains unsupported characters: $($item.Value)"
    }
}

$runTests = "1"
if ($SkipTests) {
    $runTests = "0"
}

$target = "${SparkUser}@${SparkHost}"

$remoteScript = @'
set -Eeuo pipefail

REPO_URL="$1"
BRANCH="$2"
INSTALL_DIR="$3"
WORKSPACE_DIR="$4"
VLLM_ENDPOINT="$5"
RUN_TESTS="$6"
VENV_DIR="$INSTALL_DIR/.venv"

log() {
    printf '\n\033[1;36m[APEX DEPLOY]\033[0m %s\n' "$1"
}

fail() {
    printf '\n\033[1;31m[APEX DEPLOY FAILED]\033[0m %s\n' "$1" >&2
    exit 1
}

command -v git >/dev/null 2>&1 || fail "Git is missing. Run: sudo apt update && sudo apt install -y git"
command -v python3 >/dev/null 2>&1 || fail "Python 3 is missing. Install Python 3.10 or newer."
command -v curl >/dev/null 2>&1 || fail "curl is missing. Run: sudo apt update && sudo apt install -y curl"

log "Checking Python"
python3 -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
    || fail "APEX requires Python 3.10 or newer."

log "Deploying repository"
mkdir -p "$(dirname "$INSTALL_DIR")" "$WORKSPACE_DIR"

if [ -d "$INSTALL_DIR/.git" ]; then
    if ! git -C "$INSTALL_DIR" diff --quiet || ! git -C "$INSTALL_DIR" diff --cached --quiet; then
        fail "The Spark checkout has uncommitted changes. Commit or stash them before deploying."
    fi

    git -C "$INSTALL_DIR" remote set-url origin "$REPO_URL"
    git -C "$INSTALL_DIR" fetch --prune origin "$BRANCH"

    if git -C "$INSTALL_DIR" show-ref --verify --quiet "refs/heads/$BRANCH"; then
        git -C "$INSTALL_DIR" checkout "$BRANCH"
    else
        git -C "$INSTALL_DIR" checkout --track -b "$BRANCH" "origin/$BRANCH"
    fi

    git -C "$INSTALL_DIR" pull --ff-only origin "$BRANCH"
elif [ -e "$INSTALL_DIR" ]; then
    fail "$INSTALL_DIR exists but is not a Git repository. Move it aside or choose another -InstallDir."
else
    git clone --branch "$BRANCH" --single-branch "$REPO_URL" "$INSTALL_DIR"
fi

log "Creating Python environment"
if ! python3 -m venv "$VENV_DIR"; then
    fail "Could not create a virtual environment. Run: sudo apt update && sudo apt install -y python3-venv"
fi

"$VENV_DIR/bin/python" -m pip install --upgrade pip setuptools wheel
"$VENV_DIR/bin/python" -m pip install -e "$INSTALL_DIR"

if [ "$RUN_TESTS" = "1" ]; then
    log "Running repository tests"
    (
        cd "$INSTALL_DIR"
        "$VENV_DIR/bin/python" -m unittest discover -s tests
    )
fi

log "Preparing the APEX workspace"
if [ ! -f "$WORKSPACE_DIR/.apex/config.yaml" ]; then
    "$VENV_DIR/bin/apex" init --workspace "$WORKSPACE_DIR"
fi

BASE_ENDPOINT="${VLLM_ENDPOINT%/}"
case "$BASE_ENDPOINT" in
    */v1) MODELS_URL="$BASE_ENDPOINT/models" ;;
    *)    MODELS_URL="$BASE_ENDPOINT/v1/models" ;;
esac

log "Discovering the model served by vLLM"
if ! MODEL_JSON="$(curl --fail --silent --show-error --max-time 10 "$MODELS_URL")"; then
    fail "No vLLM API responded at $MODELS_URL. Confirm the vLLM server is running on the Spark."
fi

if ! MODEL_ID="$(printf '%s' "$MODEL_JSON" | "$VENV_DIR/bin/python" -c 'import json,sys; models=json.load(sys.stdin).get("data", []); print(models[0]["id"] if models else "")')"; then
    fail "The vLLM models response was not valid JSON."
fi

if [ -z "$MODEL_ID" ]; then
    fail "vLLM responded but advertised no models at $MODELS_URL."
fi

export APEX_CONFIG_PATH="$WORKSPACE_DIR/.apex/config.yaml"
export APEX_VLLM_ENDPOINT="$BASE_ENDPOINT"
export APEX_LOCAL_MODEL="$MODEL_ID"

"$VENV_DIR/bin/python" <<'PY'
import os
from pathlib import Path

import yaml

config_path = Path(os.environ["APEX_CONFIG_PATH"])
with config_path.open("r", encoding="utf-8") as handle:
    config = yaml.safe_load(handle) or {}

config["primary_provider"] = "vllm"
config["local_dgx_endpoint"] = os.environ["APEX_VLLM_ENDPOINT"]
config["local_model"] = os.environ["APEX_LOCAL_MODEL"]

with config_path.open("w", encoding="utf-8") as handle:
    yaml.safe_dump(config, handle, sort_keys=False)
PY

log "Verifying APEX and the local model endpoint"
(
    cd "$WORKSPACE_DIR"
    "$VENV_DIR/bin/apex" --help >/dev/null
    "$VENV_DIR/bin/apex" dgx
)

COMMIT="$(git -C "$INSTALL_DIR" rev-parse --short HEAD)"

printf '\n\033[1;32mAPEX deployment complete.\033[0m\n'
printf 'Commit:    %s\n' "$COMMIT"
printf 'Install:   %s\n' "$INSTALL_DIR"
printf 'Workspace: %s\n' "$WORKSPACE_DIR"
printf 'vLLM:      %s\n' "$BASE_ENDPOINT"
printf 'Model:     %s\n' "$MODEL_ID"
printf '\nStart a Spark shell with:\n  ssh %s\n' "${USER}@$(hostname)"
printf '\nThen run:\n  cd %s\n  source %s/bin/activate\n  apex ask "Confirm you are using the local DGX Spark model."\n' "$WORKSPACE_DIR" "$VENV_DIR"
'@

# Encoding the remote program avoids PowerShell/Windows line-ending and quote
# corruption when handing a Bash script to OpenSSH.
$remoteScript = $remoteScript -replace "`r`n", "`n"
$scriptBytes = [System.Text.Encoding]::UTF8.GetBytes($remoteScript)
$payload = [Convert]::ToBase64String($scriptBytes)

$remoteCommand = "printf '%s' '$payload' | base64 --decode | bash -s -- $RepoUrl $Branch $InstallDir $WorkspaceDir $VllmEndpoint $runTests"

Write-Host "Deploying APEX to $target ..." -ForegroundColor Cyan
Write-Host "You may be asked for the Spark SSH password." -ForegroundColor DarkGray

& $ssh.Source $target $remoteCommand

if ($LASTEXITCODE -ne 0) {
    throw "Remote deployment failed with exit code $LASTEXITCODE. Read the APEX DEPLOY FAILED message above."
}

Write-Host ""
Write-Host "Deployment succeeded." -ForegroundColor Green
Write-Host ""
Write-Host "To launch the dashboard:" -ForegroundColor Cyan
Write-Host "  ssh $target"
Write-Host "  cd $WorkspaceDir"
Write-Host "  source $InstallDir/.venv/bin/activate"
Write-Host "  apex serve"
Write-Host ""
Write-Host "Then, in a second PowerShell window:" -ForegroundColor Cyan
Write-Host "  ssh -N -L 7860:127.0.0.1:7860 $target"
Write-Host "  Open http://127.0.0.1:7860"
