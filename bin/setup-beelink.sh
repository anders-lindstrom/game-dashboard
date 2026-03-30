#!/usr/bin/env bash
# Setup game-dashboard on the beelink (run ON the beelink)
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/anders-lindstrom/game-dashboard/main/bin/setup-beelink.sh | bash
#   # or clone the repo and run: ./bin/setup-beelink.sh
set -euo pipefail

INSTALL_DIR="/opt/game-dashboard"
REGISTRY="registry.lindstromhome.cc"
IMAGE="${REGISTRY}/game-dashboard:latest"
REPO="https://raw.githubusercontent.com/anders-lindstrom/game-dashboard/main"

echo "=== Game Dashboard - Beelink Setup ==="

# Create install directory
sudo mkdir -p "${INSTALL_DIR}/data"
sudo chown "$(id -u):$(id -g)" "${INSTALL_DIR}" "${INSTALL_DIR}/data"

# Download docker-compose.yml
echo "Fetching docker-compose.yml..."
curl -fsSL "${REPO}/docker-compose.yml" -o "${INSTALL_DIR}/docker-compose.yml"

# Seed with an empty games.json if none exists
if [ ! -f "${INSTALL_DIR}/data/games.json" ]; then
  echo "Creating empty games.json (update from Windows with: scp public/data/games.json beelink:${INSTALL_DIR}/data/)"
  echo "[]" > "${INSTALL_DIR}/data/games.json"
fi

# Login to registry if not already
if ! docker pull "${IMAGE}" 2>/dev/null; then
  echo "Need to login to registry first:"
  docker login "${REGISTRY}"
fi

# Pull and start
cd "${INSTALL_DIR}"
docker compose pull
docker compose up -d

echo ""
echo "=== Done! ==="
echo "Dashboard: http://$(hostname -I | awk '{print $1}'):3080"
echo ""
echo "To update game data from Windows:"
echo "  scp public/data/games.json $(whoami)@$(hostname):${INSTALL_DIR}/data/"
echo ""
echo "To update the app after a new release:"
echo "  cd ${INSTALL_DIR} && docker compose pull && docker compose up -d"
