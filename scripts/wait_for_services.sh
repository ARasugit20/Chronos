#!/usr/bin/env bash
# Wait for Postgres and Redis before running integration tests.
set -euo pipefail

wait_for_port() {
  local host="$1"
  local port="$2"
  local label="$3"
  for _ in $(seq 1 30); do
    if python3 -c "import socket; s=socket.socket(); s.settimeout(1); s.connect(('$host', $port)); s.close()" 2>/dev/null; then
      echo "$label is ready on $host:$port"
      return 0
    fi
    sleep 1
  done
  echo "$label not ready on $host:$port" >&2
  return 1
}

wait_for_port "${POSTGRES_HOST:-localhost}" "${POSTGRES_PORT:-5432}" "postgres"
wait_for_port "${REDIS_HOST:-localhost}" "${REDIS_PORT:-6379}" "redis"
