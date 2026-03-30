#!/usr/bin/env bash
# Push updated games.json to the beelink
# Usage: ./bin/update-data.sh [beelink-host]
set -euo pipefail

BEELINK="${1:-beelink}"
INSTALL_DIR="/opt/game-dashboard"
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DATA_FILE="${SCRIPT_DIR}/public/data/games.json"

if [ ! -f "${DATA_FILE}" ]; then
  echo "ERROR: ${DATA_FILE} not found. Run the scan/fetch/merge pipeline first."
  exit 1
fi

echo "Copying games.json to ${BEELINK}:${INSTALL_DIR}/data/"
scp "${DATA_FILE}" "${BEELINK}:${INSTALL_DIR}/data/games.json"
echo "Done! Dashboard will serve updated data immediately (no restart needed)."
