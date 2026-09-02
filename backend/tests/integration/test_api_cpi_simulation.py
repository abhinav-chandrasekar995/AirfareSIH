"""The CPI disclaimer must be present on every response of this module, enforced by
two independent mechanisms (D-026). This test exercises both."""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.analytics.cpi import DISCLAIMER
from tests.conftest import requires_db


@pytest.fixture
async def client():
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@requires_db
async def test_cpi_simulation_always_carries_the_disclaimer(client: AsyncClient):
    response = await client.get("/api/v1/cpi-simulation", params={"weight": 2.5})
    assert response.status_code == 200
    body = response.json()
    assert body["disclaimer"] == DISCLAIMER


@requires_db
async def test_cpi_simulation_reports_vintage_and_base_year(client: AsyncClient):
    """Build prompt Sec.15: CPI data must always display its vintage and base year -
    never silently mix vintages."""
    response = await client.get("/api/v1/cpi-simulation")
    body = response.json()["data"]
    assert body["cpi_vintage"]
    assert body["cpi_base_year"]


@requires_db
async def test_cpi_simulation_weight_out_of_range_is_rejected(client: AsyncClient):
    response = await client.get("/api/v1/cpi-simulation", params={"weight": 150})
    assert response.status_code == 422
