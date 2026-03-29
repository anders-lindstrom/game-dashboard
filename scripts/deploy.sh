#!/bin/bash
# Deploy game dashboard to beelink
# Usage: ./scripts/deploy.sh [beelink-host] [deploy-path]
#
# Example: ./scripts/deploy.sh beelink /opt/game-dashboard
#
# Data pipeline: scan_games -> fetch_igdb/fetch_rawg -> merge_sources -> deploy
# Each fetch writes to its own cache file; merge combines them into games.json

set -e

BEELINK_HOST="${1:-beelink}"
DEPLOY_PATH="${2:-/opt/game-dashboard}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Step 1: Scan game directories ==="
python "$SCRIPT_DIR/scan_games.py"

echo ""
echo "=== Step 2: Fetch game data ==="

# Try IGDB first (more reliable), RAWG if available
if [ -n "$TWITCH_CLIENT_ID" ] || grep -q "TWITCH_CLIENT_ID" "$SCRIPT_DIR/.env" 2>/dev/null; then
    echo "--- Fetching from IGDB ---"
    python "$SCRIPT_DIR/fetch_igdb.py"
else
    echo "--- Skipping IGDB (no Twitch credentials) ---"
fi

if [ -n "$RAWG_API_KEY" ] || grep -q "RAWG_API_KEY" "$SCRIPT_DIR/.env" 2>/dev/null; then
    echo "--- Fetching from RAWG ---"
    python "$SCRIPT_DIR/fetch_rawg.py"
else
    echo "--- Skipping RAWG (no API key) ---"
fi

echo ""
echo "=== Step 3: Merge sources ==="
python "$SCRIPT_DIR/merge_sources.py"

echo ""
echo "=== Step 4: Sync project to beelink ==="
rsync -avz --exclude node_modules --exclude .git \
    "$PROJECT_DIR/" "$BEELINK_HOST:$DEPLOY_PATH/"

echo ""
echo "=== Step 5: Build and start Docker on beelink ==="
ssh "$BEELINK_HOST" "cd $DEPLOY_PATH && docker compose up -d --build"

echo ""
echo "=== Done! Dashboard available at http://$BEELINK_HOST:3080 ==="
