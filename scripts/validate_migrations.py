#!/usr/bin/env python3
"""Validate Alembic migration chain integrity for CI."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"


def main() -> int:
    ini_path = BACKEND / "alembic.ini"
    if not ini_path.exists():
        print("FAIL: backend/alembic.ini not found", file=sys.stderr)
        return 1

    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(ini_path))
    script = ScriptDirectory.from_config(config)
    heads = script.get_heads()
    if len(heads) != 1:
        print(f"FAIL: expected one Alembic head, found {heads}", file=sys.stderr)
        return 1

    revisions = list(script.walk_revisions())
    if not revisions:
        print("FAIL: no Alembic revisions found", file=sys.stderr)
        return 1

    print(f"Alembic migration chain valid ({len(revisions)} revisions, head={heads[0]}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
