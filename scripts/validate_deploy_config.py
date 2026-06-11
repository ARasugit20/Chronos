#!/usr/bin/env python3
"""Validate Chronos deploy configuration files for Render readiness."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


def _read(relative_path: str) -> str:
    path = ROOT / relative_path
    if not path.exists():
        raise AssertionError(f"Missing required file: {relative_path}")
    return path.read_text(encoding="utf-8")


def _require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        raise AssertionError(f"{label} is missing {needle!r}")


def validate_render_yaml() -> None:
    render_yaml = _read("render.yaml")
    for needle in [
        "name: chronos-api",
        "name: chronos-worker",
        "name: chronos-redis",
        "name: chronos-frontend",
        "name: chronos-db",
        "key: NEWS_SOURCE",
        "value: finnhub",
        "key: NEWS_API_KEY",
        "key: CORS_ORIGINS",
        'value: \'["https://chronos-frontend.onrender.com"]\'',
        "routes:",
        "source: /*",
        "destination: /index.html",
        "key: VITE_API_URL",
        "property: host",
    ]:
        _require(render_yaml, needle, "render.yaml")


def validate_backend_env_example() -> None:
    env_example = _read("backend/.env.example")
    for needle in [
        "NEWS_SOURCE=finnhub",
        "NEWS_API_KEY=your_finnhub_api_key_here",
        "NEWS_API_URL=https://finnhub.io/api/v1",
        "SECRET_KEY=generate_a_random_64_char_string",
        "ADMIN_PASSWORD=set_a_strong_password",
        "CORS_ORIGINS=",
        "PAPER_TRADING_MODE=true",
        "PRICE_SOURCE=mock",
    ]:
        _require(env_example, needle, "backend/.env.example")


def validate_runtime_config() -> None:
    config = _read("backend/app/config.py")
    for needle in [
        "frontend_url: str",
        "environment: str",
        '@field_validator("cors_origins", mode="before")',
        "json.loads(v)",
    ]:
        _require(config, needle, "backend/app/config.py")


def validate_frontend_env_example() -> None:
    env_example = _read("frontend/.env.example")
    _require(env_example, "VITE_API_URL=", "frontend/.env.example")


def main() -> int:
    checks = [
        validate_render_yaml,
        validate_backend_env_example,
        validate_runtime_config,
        validate_frontend_env_example,
    ]
    failures: list[str] = []
    for check in checks:
        try:
            check()
        except AssertionError as exc:
            failures.append(str(exc))

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print("Deploy configuration validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
