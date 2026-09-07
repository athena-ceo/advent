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
    echo "usage: ./advent.sh {start|stop|restart|build|logs|ps|urls|health|smoke|test|deploy} [dev|prod]" ;;
esac
