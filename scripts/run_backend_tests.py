#!/usr/bin/env python3
"""Standalone backend test runner for CI and local development.

Uses fakeredis (configured in tests/conftest.py) so only Postgres must be reachable.
"""
from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
from pathlib import Path


def wait_for_port(host: str, port: int, label: str, timeout_seconds: int = 30) -> None:
    deadline = time.monotonic() + timeout_seconds
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                print(f"{label} is ready on {host}:{port}")
                return
        except OSError:
            time.sleep(1)
    raise SystemExit(f"{label} not ready on {host}:{port} after {timeout_seconds}s")


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    backend = root / "backend"

    os.environ.setdefault("ENVIRONMENT", "test")
    os.environ.setdefault("PAPER_AUTO_APPROVE", "false")
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://invest:invest_local@localhost:5432/invest_agent",
    )
    os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
    os.environ["PYTHONPATH"] = str(backend)

    postgres_host = os.environ.get("POSTGRES_HOST", "localhost")
    postgres_port = int(os.environ.get("POSTGRES_PORT", "5432"))
    wait_for_port(postgres_host, postgres_port, "postgres")

    try:
        import fakeredis  # noqa: F401
    except ImportError:
        print("fakeredis is required for tests; install backend[dev]", file=sys.stderr)
        return 1

    pytest_args = argv or ["tests/", "-v", "--tb=short"]
    cmd = [sys.executable, "-m", "pytest", *pytest_args]
    print(f"Running: {' '.join(cmd)} (cwd={backend})")
    return subprocess.call(cmd, cwd=backend)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
