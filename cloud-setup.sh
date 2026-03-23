#!/usr/bin/env bash
# cloud-setup.sh — Bootstrap Pace-AI in Claude Code's cloud environment.
#
# Installs all MCP server packages, clones the private data repo,
# and loads API credentials from the .env stored in that private repo.
#
# Required env var:
#   GITHUB_TOKEN — Fine-grained PAT scoped to pace-ai-data repo only
#
# All other credentials (Strava, Garmin, Withings, Notion) are stored
# in pace-ai-data/.env and loaded automatically after clone.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="${REPO_ROOT}/pace-ai-data"

echo "=== Pace-AI Cloud Setup ==="

# ── 1. Ensure Python 3.12+ (required by withings-sync) ─────────────
PYTHON_MINOR=$(python3 -c 'import sys; print(sys.version_info.minor)')
if [ "${PYTHON_MINOR}" -lt 12 ]; then
    echo "Python 3.${PYTHON_MINOR} detected — upgrading to 3.12+..."
    apt-get update -qq && apt-get install -y -qq python3.12 python3.12-venv python3.12-dev 2>/dev/null \
        || (add-apt-repository -y ppa:deadsnakes/ppa && apt-get update -qq && apt-get install -y -qq python3.12 python3.12-venv python3.12-dev)
    python3.12 -m ensurepip --upgrade 2>/dev/null || true
    update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1 2>/dev/null || true
    echo "Now using: $(python3 --version)"
fi

# ── 2. Install Python packages ──────────────────────────────────────
echo "Installing pace-ai and dependencies..."
pip install -e "${REPO_ROOT}/pace-ai/"
pip install -e "${REPO_ROOT}/strava-mcp/"
pip install -e "${REPO_ROOT}/garmin-mcp/"
pip install -e "${REPO_ROOT}/withings-mcp/"
pip install -e "${REPO_ROOT}/notion-mcp/"

# ── 3. Clone private data repo ──────────────────────────────────────
if [ -d "${DATA_DIR}/.git" ]; then
    echo "pace-ai-data already cloned, pulling latest..."
    cd "${DATA_DIR}" && git pull && cd "${REPO_ROOT}"
elif [ -n "${GITHUB_TOKEN:-}" ]; then
    echo "Cloning pace-ai-data..."
    git clone "https://${GITHUB_TOKEN}@github.com/aldred-coetzee/pace-ai-data.git" "${DATA_DIR}"
else
    echo "WARNING: GITHUB_TOKEN not set — cannot clone pace-ai-data."
    echo "The database will be created fresh. Set GITHUB_TOKEN in Claude Code env vars to persist data."
    mkdir -p "${DATA_DIR}"
fi

# ── 4. Load credentials from private repo's .env ────────────────────
if [ -f "${DATA_DIR}/.env" ]; then
    echo "Loading credentials from pace-ai-data/.env..."
    set -a
    source "${DATA_DIR}/.env"
    set +a
else
    echo "WARNING: No .env found in pace-ai-data. Data sync will not work."
    echo "Create pace-ai-data/.env with API credentials (see README in that repo)."
fi

# ── 5. Set PACE_AI_DB ───────────────────────────────────────────────
export PACE_AI_DB="${DATA_DIR}/pace_ai.db"
echo "PACE_AI_DB=${PACE_AI_DB}"

echo ""
echo "=== Setup complete ==="
echo "Database: ${PACE_AI_DB}"
echo ""
echo "To sync latest data, run in Python:"
echo "  from pace_ai.database import HistoryDB"
echo "  from pace_ai.tools.sync import sync_all"
echo "  import asyncio"
echo "  db = HistoryDB('${PACE_AI_DB}')"
echo "  asyncio.run(sync_all(db))"
