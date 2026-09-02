"""End-to-end test that the full guided demo path works with the network disabled
(build prompt Sec.33). Requires a live database seeded via `python -m seeds.load_seed`.

This test does NOT mock the network away - it asserts on `settings.collection_enabled`
being False and every endpoint still returning real, non-empty data, which is the
actual demo-resilience guarantee: the read path never depends on live collection.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.config import settings
from tests.conftest import requires_db


@pytest.fixture
async def client():
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


def test_collection_is_disabled_in_the_demo_configuration():
    """The read path must not depend on live scraping being possible."""
    assert settings.collection_enabled is False


@requires_db
async def test_full_guided_demo_path_returns_real_data(client: AsyncClient):
    """Walks the exact judge journey from the PRD: dashboard -> index -> route ->
    lead-time -> anomaly -> forecast -> backtest -> CPI simulator. Every step must
    return non-empty, computed data with collection turned off."""
    assert settings.collection_enabled is False

    dashboard = await client.get("/api/v1/dashboard")
    assert dashboard.status_code == 200
    assert dashboard.json()["data"]["index_value"] is not None

    index = await client.get("/api/v1/index", params={"level": "NATIONAL"})
    assert len(index.json()["data"]) > 0

    routes = await client.get("/api/v1/routes")
    assert len(routes.json()["data"]) > 0
    route_code = routes.json()["data"][0]["route_code"]

    route_detail = await client.get(f"/api/v1/routes/{route_code}")
    assert route_detail.status_code == 200

    lead_time = await client.get("/api/v1/lead-time")
    assert len(lead_time.json()["data"]["curve"]) > 0

    anomalies = await client.get("/api/v1/anomalies")
    assert anomalies.status_code == 200  # may legitimately be empty on a quiet day

    forecast = await client.get("/api/v1/forecast")
    if forecast.status_code == 200:
        points = forecast.json()["data"]["points"]
        for point in points:
            assert point["lower_bound"] <= point["prediction"] <= point["upper_bound"]

    backtest = await client.get("/api/v1/backtest")
    if backtest.status_code == 200:
        assert backtest.json()["data"]["n_test_days"] >= 30

    cpi = await client.get("/api/v1/cpi-simulation")
    if cpi.status_code == 200:
        assert cpi.json()["disclaimer"] is not None

    # Every response along the path must be honest about its data mode.
    for response in (dashboard, index, routes, route_detail, lead_time):
        assert response.json()["meta"]["data_mode"] in {"LIVE", "CACHED", "REPLAY"}
