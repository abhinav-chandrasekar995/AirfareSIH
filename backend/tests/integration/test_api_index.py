"""Integration tests for the index API: envelope shape, data-mode field, and route
index 404 behaviour. Requires a live database (see tests/conftest.py::requires_db)."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from tests.conftest import requires_db


@pytest.fixture
async def client():
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@requires_db
async def test_national_index_returns_envelope_shape(client: AsyncClient):
    response = await client.get("/api/v1/index", params={"level": "NATIONAL"})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"data", "meta", "methodology_version", "disclaimer"}
    assert "data_mode" in body["meta"]
    assert body["meta"]["data_mode"] in {"LIVE", "CACHED", "REPLAY"}


@requires_db
async def test_unknown_route_returns_404(client: AsyncClient):
    response = await client.get("/api/v1/index/route/ZZZ-ZZZ")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


@requires_db
async def test_rate_limit_headers_present(client: AsyncClient):
    response = await client.get("/api/v1/routes")
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
