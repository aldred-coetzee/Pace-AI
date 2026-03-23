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

# ── 1. Install Python packages ──────────────────────────────────────
echo "Installing pace-ai and dependencies..."
pip install -e "${REPO_ROOT}/pace-ai/"
pip install -e "${REPO_ROOT}/strava-mcp/"
pip install -e "${REPO_ROOT}/garmin-mcp/"
pip install -e "${REPO_ROOT}/notion-mcp/"
# withings-mcp requires Python 3.12+ (withings-sync>=5.0) — skip if unavailable
pip install -e "${REPO_ROOT}/withings-mcp/" 2>/dev/null || echo "Skipping withings-mcp (requires Python 3.12+)"

# ── 2. Clone private data repo ──────────────────────────────────────
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

# ── 3. Load credentials from private repo's .env ────────────────────
if [ -f "${DATA_DIR}/.env" ]; then
    echo "Loading credentials from pace-ai-data/.env..."
    set -a
    source "${DATA_DIR}/.env"
    set +a
else
    echo "WARNING: No .env found in pace-ai-data. Data sync will not work."
    echo "Create pace-ai-data/.env with API credentials (see README in that repo)."
fi

# ── 4. Set PACE_AI_DB ───────────────────────────────────────────────
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
