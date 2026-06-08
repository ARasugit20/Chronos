#!/usr/bin/env bash
# CI/local integration test runner with stable env defaults.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

export DATABASE_URL="${DATABASE_URL:-postgresql+asyncpg://invest:invest_local@localhost:5432/invest_agent}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379/0}"
export ENVIRONMENT="${ENVIRONMENT:-test}"
export PYTHONPATH="${PYTHONPATH:-$ROOT/backend}"

# shellcheck source=scripts/wait_for_services.sh
source "$ROOT/scripts/wait_for_services.sh"

cd "$ROOT/backend"
echo "Running pytest in $PWD"
exec python -m pytest "$@"
