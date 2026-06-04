import pytest

pytest.importorskip("fastapi")


def test_ws_module_exports_router() -> None:
    from app.ws import signal_ws

    assert signal_ws.router is not None
