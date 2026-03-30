#!/usr/bin/env bash
set -euo pipefail

REGISTRY="registry.lindstromhome.cc"
IMAGE="game-dashboard"

# Resolve version from git
TAG=$(git describe --tags --exact-match 2>/dev/null || true)

if [[ -n "$TAG" ]]; then
  VERSION="${TAG#v}"
else
  LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "0.0.0")
  SHORT_SHA=$(git rev-parse --short HEAD)
  VERSION="${LATEST_TAG#v}-${SHORT_SHA}"
fi

FULL_IMAGE="${REGISTRY}/${IMAGE}:${VERSION}"

echo "Building ${FULL_IMAGE}"
docker build -t "${FULL_IMAGE}" .

if [[ -n "$TAG" ]]; then
  LATEST="${REGISTRY}/${IMAGE}:latest"
  docker tag "${FULL_IMAGE}" "${LATEST}"
  echo "Pushing ${FULL_IMAGE} and ${LATEST}"
  docker push "${FULL_IMAGE}"
  docker push "${LATEST}"
else
  echo "Pushing ${FULL_IMAGE}"
  docker push "${FULL_IMAGE}"
fi

echo "Done: ${FULL_IMAGE}"
