#!/usr/bin/env bash
# CI/local integration test runner with stable env defaults.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$ROOT/scripts/run_backend_tests.py" "$@"
