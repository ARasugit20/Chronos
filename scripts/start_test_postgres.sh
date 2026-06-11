#!/usr/bin/env bash
# Start a lightweight Postgres container for local/CI-style pytest runs.
# Redis is not required — tests use fakeredis (see tests/conftest.py).
set -euo pipefail

CONTAINER_NAME="${CHRONOS_PG_CONTAINER:-chronos-pg}"
POSTGRES_DB="${POSTGRES_DB:-invest_agent}"
POSTGRES_USER="${POSTGRES_USER:-invest}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-invest_local}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"

cmd="${1:-start}"

case "$cmd" in
  start)
    if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
      docker start "$CONTAINER_NAME" >/dev/null 2>&1 || true
      echo "Container $CONTAINER_NAME already exists — started if it was stopped."
    else
      docker run -d --name "$CONTAINER_NAME" \
        -p "${POSTGRES_PORT}:5432" \
        -e "POSTGRES_DB=$POSTGRES_DB" \
        -e "POSTGRES_USER=$POSTGRES_USER" \
        -e "POSTGRES_PASSWORD=$POSTGRES_PASSWORD" \
        postgres:16-alpine
      echo "Created and started $CONTAINER_NAME on port $POSTGRES_PORT"
    fi
    for _ in $(seq 1 30); do
      if docker exec "$CONTAINER_NAME" pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" >/dev/null 2>&1; then
        echo "Postgres is ready."
        exit 0
      fi
      sleep 1
    done
    echo "Postgres did not become ready in time." >&2
    exit 1
    ;;
  stop)
    docker stop "$CONTAINER_NAME" 2>/dev/null || echo "Container $CONTAINER_NAME is not running."
    ;;
  rm)
    docker rm -f "$CONTAINER_NAME" 2>/dev/null || echo "Container $CONTAINER_NAME not found."
    ;;
  status)
    docker ps -a --filter "name=^${CONTAINER_NAME}$" --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'
    ;;
  *)
    echo "Usage: $0 {start|stop|rm|status}" >&2
    exit 1
    ;;
esac
