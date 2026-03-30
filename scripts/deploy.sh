#!/bin/bash
# Full pipeline: scan games, fetch data, merge, push to beelink
# Usage: ./scripts/deploy.sh [beelink-host]
set -e

BEELINK_HOST="${1:-beelink}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "=== Step 1: Scan game directories ==="
python "$SCRIPT_DIR/scan_games.py"

echo ""
echo "=== Step 2: Fetch game data ==="

if [ -n "${TWITCH_CLIENT_ID:-}" ] || grep -q "TWITCH_CLIENT_ID" "$SCRIPT_DIR/.env" 2>/dev/null; then
    echo "--- Fetching from IGDB ---"
    python "$SCRIPT_DIR/fetch_igdb.py"
else
    echo "--- Skipping IGDB (no Twitch credentials) ---"
fi

if [ -n "${RAWG_API_KEY:-}" ] || grep -q "RAWG_API_KEY" "$SCRIPT_DIR/.env" 2>/dev/null; then
    echo "--- Fetching from RAWG ---"
    python "$SCRIPT_DIR/fetch_rawg.py"
else
    echo "--- Skipping RAWG (no API key) ---"
fi

echo ""
echo "=== Step 3: Merge sources ==="
python "$SCRIPT_DIR/merge_sources.py"

echo ""
echo "=== Step 4: Push data to beelink ==="
bash "$PROJECT_DIR/bin/update-data.sh" "$BEELINK_HOST"

echo ""
echo "=== Done! ==="
