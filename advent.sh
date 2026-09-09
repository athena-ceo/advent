#!/usr/bin/env bash
# Copyright (c) 2026 Athena Decisions Systems SAS.
#
# Control script for the Adventure app (mirrors xcape.sh / golden-path).
#   ./advent.sh <command> [dev|prod]
#
# Commands: start stop restart logs ps build urls health smoke test deploy
set -euo pipefail
cd "$(dirname "$0")"

CMD="${1:-help}"
ENVIRON="${2:-dev}"
case "$ENVIRON" in
  dev)  COMPOSE="docker compose -f docker-compose.dev.yml" ;;
  prod) COMPOSE="docker compose -f docker-compose.server.yml" ;;
  *) echo "unknown environment: $ENVIRON (use dev|prod)"; exit 1 ;;
esac

# Pick up any port overrides from .env (the same file docker compose reads).
if [ -f .env ]; then set -a; . ./.env; set +a; fi
BACKEND_PORT="${BACKEND_PORT:-8040}"
FRONTEND_PORT="${FRONTEND_PORT:-3040}"

print_urls() {
  echo ""
  echo "  Frontend:   http://localhost:${FRONTEND_PORT}"
  echo "  API docs:   http://localhost:${BACKEND_PORT}/docs      (Swagger UI)"
  echo "  Health:     http://localhost:${BACKEND_PORT}/health"
  if [ "$ENVIRON" = "prod" ]; then
    echo "  Public:     https://apps.athenadecisions.com/advent/"
  fi
  echo ""
}

case "$CMD" in
  start)   $COMPOSE up -d --build && print_urls ;;
  stop)    $COMPOSE down ;;
  restart) $COMPOSE down && $COMPOSE up -d --build && print_urls ;;
  build)   $COMPOSE build ;;
  logs)    shift 2 2>/dev/null || true; $COMPOSE logs -f "$@" ;;
  ps)      $COMPOSE ps && print_urls ;;
  urls)    print_urls ;;
  health)
    curl -fsS "http://localhost:${BACKEND_PORT}/health" && echo ;;
  smoke)
    SMOKE_BASE_URL="http://localhost:${BACKEND_PORT}" python3 scripts/smoke_test.py ;;
  test)
    ( cd backend && python -m pytest tests -q ) ;;
  sync)
    # Push the pre-generated image banks (built on a GPU/MPS box) to the prod
    # host, where docker-compose.server.yml mounts them into the backend.
    # Needs ADVENT_DEPLOY_SSH (user@host) and ADVENT_DEPLOY_DIR (the repo dir on
    # the server) in .env. Composites are NOT synced -- the server rebuilds them
    # lazily from the scene + sprite plates.
    : "${ADVENT_DEPLOY_SSH:?set ADVENT_DEPLOY_SSH=user@host in .env}"
    : "${ADVENT_DEPLOY_DIR:?set ADVENT_DEPLOY_DIR=/path/to/advent on the server in .env}"
    # Runs from THIS (dev) machine and pushes up to the server over SSH -- the
    # server never connects back. Create the target dirs in case the app repo
    # isn't checked out on the server yet (staging the banks ahead of deploy).
    ssh "${ADVENT_DEPLOY_SSH}" "mkdir -p '${ADVENT_DEPLOY_DIR}/scene-cache' '${ADVENT_DEPLOY_DIR}/sprite-cache'"
    for dir in scene-cache sprite-cache; do
      if [ -d "$dir" ]; then
        echo "==> rsync $dir -> ${ADVENT_DEPLOY_SSH}:${ADVENT_DEPLOY_DIR}/$dir"
        # Portable flags: macOS ships openrsync (no --info=progress2).
        rsync -rlptv --delete "$dir/" \
          "${ADVENT_DEPLOY_SSH}:${ADVENT_DEPLOY_DIR}/$dir/"
      fi
    done
    echo "done. (restart prod to pick up new mounts if this is the first sync:"
    echo "  ssh ${ADVENT_DEPLOY_SSH} 'cd ${ADVENT_DEPLOY_DIR} && ./advent.sh restart prod')" ;;
  deploy)
    if [ "$ENVIRON" != "prod" ]; then echo "deploy requires prod"; exit 1; fi
    echo "==> git pull"; git pull --ff-only
    echo "==> build + up"; $COMPOSE up -d --build
    echo "==> waiting for health"
    for i in $(seq 1 30); do
      if curl -fsS "http://localhost:${BACKEND_PORT}/health" >/dev/null 2>&1; then
        echo "healthy"; exit 0
      fi
      sleep 2
    done
    echo "health check failed"; $COMPOSE logs --tail 50 backend; exit 1 ;;
  *)
    echo "usage: ./advent.sh {start|stop|restart|build|logs|ps|urls|health|smoke|test|sync|deploy} [dev|prod]" ;;
esac
