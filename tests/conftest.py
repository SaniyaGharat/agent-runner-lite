"""pytest configuration. PROVIDED IN FULL.

The FastAPI app uses one module-level `store`, so any test that goes through the HTTP client has
to start from a clean one. Tests using `make_run` build their own Store and don't need this, but
the fixture is autouse so you never have to remember which kind you're writing.
"""

from __future__ import annotations

import pytest

from app.store import store as global_store


@pytest.fixture(autouse=True)
def reset_global_store():
    global_store.tasks.clear()
    global_store.runs.clear()
    yield
    global_store.tasks.clear()
    global_store.runs.clear()


@pytest.fixture
def client():
    """A test client for the whole app, for end-to-end tests over HTTP.

        def test_healthz(client):
            assert client.get("/healthz").json() == {"ok": True}

    Needs no running server — it talks to the ASGI app in-process.
    """
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as c:
        yield c
