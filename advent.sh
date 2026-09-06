#!/usr/bin/env bash
# Copyright (c) 2026 Athena Decisions Systems SAS.
#
# Control script for the Adventure app (mirrors xcape.sh / golden-path).
#   ./advent.sh <command> [dev|prod]
#
# Commands: start stop restart logs ps build health smoke test deploy
set -euo pipefail
cd "$(dirname "$0")"

CMD="${1:-help}"
ENVIRON="${2:-dev}"
case "$ENVIRON" in
  dev)  COMPOSE="docker compose -f docker-compose.dev.yml" ;;
  prod) COMPOSE="docker compose -f docker-compose.server.yml" ;;
  *) echo "unknown environment: $ENVIRON (use dev|prod)"; exit 1 ;;
esac
BACKEND_PORT="${BACKEND_PORT:-8040}"

case "$CMD" in
  start)   $COMPOSE up -d --build ;;
  stop)    $COMPOSE down ;;
  restart) $COMPOSE down && $COMPOSE up -d --build ;;
  build)   $COMPOSE build ;;
  logs)    shift 2 2>/dev/null || true; $COMPOSE logs -f "$@" ;;
  ps)      $COMPOSE ps ;;
  health)
    curl -fsS "http://localhost:${BACKEND_PORT}/health" && echo ;;
  smoke)
    SMOKE_BASE_URL="http://localhost:${BACKEND_PORT}" python3 scripts/smoke_test.py ;;
  test)
    ( cd backend && python -m pytest tests -q ) ;;
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
    echo "usage: ./advent.sh {start|stop|restart|build|logs|ps|health|smoke|test|deploy} [dev|prod]" ;;
esac
