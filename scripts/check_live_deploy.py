#!/usr/bin/env python3
"""Smoke-check a deployed Chronos API.

The script is intentionally dependency-free so it can run from a laptop,
GitHub Actions, or a Render shell without installing backend packages.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


def _url(base_url: str, path: str) -> str:
    return urllib.parse.urljoin(base_url.rstrip("/") + "/", path.lstrip("/"))


def _get_json(url: str, timeout: float) -> dict[str, Any]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            payload = response.read().decode("utf-8")
            return json.loads(payload)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"{url} returned HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Could not reach {url}: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"{url} did not return JSON") from exc


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke-check a Chronos API deployment.")
    parser.add_argument("base_url", help="API base URL, e.g. https://chronos-api.onrender.com")
    parser.add_argument("--timeout", type=float, default=15.0)
    parser.add_argument("--require-live-news", action="store_true")
    parser.add_argument("--require-signals", action="store_true")
    args = parser.parse_args()

    health_url = _url(args.base_url, "/api/v1/health")
    health = _get_json(health_url, args.timeout)
    print(json.dumps({"health_url": health_url, **health}, indent=2, sort_keys=True))

    failures: list[str] = []
    if args.require_live_news and not health.get("live_news_ready"):
        failures.append("live_news_ready is false")
    if health.get("status") == "degraded":
        failures.append(f"health is degraded: {health.get('alerts', [])}")

    if args.require_signals:
        signals_url = _url(args.base_url, "/api/v1/signals/live")
        signals = _get_json(signals_url, args.timeout)
        data = signals.get("data", [])
        print(json.dumps({"signals_url": signals_url, "signal_count": len(data)}, indent=2))
        if not data:
            failures.append("signals/live returned no signals")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1

    print("Chronos deploy smoke check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
