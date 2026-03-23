#!/usr/bin/env bash
# cloud-setup.sh — Bootstrap Pace-AI in Claude Code's cloud environment.
#
# Installs all MCP server packages, clones the private data repo,
# and sets PACE_AI_DB to point at the coaching database.
#
# Required env vars:
#   GITHUB_TOKEN — GitHub PAT with repo scope (set in Claude Code secrets)
#
# Optional env vars (for data sync):
#   STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, STRAVA_ACCESS_TOKEN, STRAVA_REFRESH_TOKEN
#   GARMIN_EMAIL, GARMIN_PASSWORD
#   NOTION_TOKEN, NOTION_DIARY_DATABASE_ID
#   WITHINGS_CONFIG_FOLDER

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
DATA_DIR="${REPO_ROOT}/pace-ai-data"

echo "=== Pace-AI Cloud Setup ==="

# ── 1. Install Python packages ──────────────────────────────────────
echo "Installing pace-ai and dependencies..."
pip install -e "${REPO_ROOT}/pace-ai/"
pip install -e "${REPO_ROOT}/strava-mcp/"
pip install -e "${REPO_ROOT}/garmin-mcp/"
pip install -e "${REPO_ROOT}/withings-mcp/"
pip install -e "${REPO_ROOT}/notion-mcp/"

# ── 2. Clone private data repo ──────────────────────────────────────
if [ -d "${DATA_DIR}/.git" ]; then
    echo "pace-ai-data already cloned, pulling latest..."
    cd "${DATA_DIR}" && git pull && cd "${REPO_ROOT}"
elif [ -n "${GITHUB_TOKEN:-}" ]; then
    echo "Cloning pace-ai-data..."
    git clone "https://${GITHUB_TOKEN}@github.com/aldred-coetzee/pace-ai-data.git" "${DATA_DIR}"
else
    echo "WARNING: GITHUB_TOKEN not set — cannot clone pace-ai-data."
    echo "The database will be created fresh. Set GITHUB_TOKEN in Claude Code secrets to persist data."
    mkdir -p "${DATA_DIR}"
fi

# ── 3. Set PACE_AI_DB ───────────────────────────────────────────────
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
