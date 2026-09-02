"""RLS enforcement and API authorization boundaries (build prompt Sec.6).

These prove the boundary is enforced at the DATABASE, not merely by the FastAPI
dependency: a session bound to the PUBLIC role must see zero rows from an ADMIN-only
table even if a bug in the API layer forgot to check the role.
"""
from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text

from app.core.constants import Role
from app.db.models import ApiKey, AuditLog
from app.db.rls import apply_principal, current_context
from app.db.session import SessionLocal
from tests.conftest import requires_db


@pytest.fixture
async def client():
    from app.main import create_app

    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@requires_db
async def test_rls_context_round_trips_through_set_config():
    async with SessionLocal() as session:
        await apply_principal(session, Role.ANALYST, key_id=42)
        ctx = await current_context(session)
        assert ctx["role"] == "ANALYST"
        assert ctx["key_id"] == "42"


@requires_db
async def test_public_role_cannot_read_api_keys_table_at_the_database_level():
    """This is the load-bearing test: RLS must fail closed regardless of what the API
    layer does. A PUBLIC-role session querying api_keys directly must see nothing."""
    async with SessionLocal() as session:
        await apply_principal(session, Role.PUBLIC)
        rows = (await session.execute(select(ApiKey))).scalars().all()
        assert rows == []


@requires_db
async def test_public_role_cannot_read_audit_log_at_the_database_level():
    async with SessionLocal() as session:
        await apply_principal(session, Role.PUBLIC)
        rows = (await session.execute(select(AuditLog))).scalars().all()
        assert rows == []


@requires_db
async def test_missing_role_setting_fails_closed_not_open():
    """No app.role set at all must behave like the least-privileged role, not the
    most-privileged one - the RLS design failure mode is 'see nothing', not 'see all'."""
    async with SessionLocal() as session:
        await session.execute(text("SELECT set_config('app.role', '', true)"))
        rows = (await session.execute(select(ApiKey))).scalars().all()
        assert rows == []


@requires_db
async def test_admin_endpoint_rejects_unauthenticated_request(client: AsyncClient):
    """A missing key resolves to the ANONYMOUS/PUBLIC principal (public reads are
    intentionally allowed without credentials), so hitting an ADMIN-only endpoint is a
    privilege failure (403 Forbidden) rather than an identity failure (401
    Unauthorized) - see middleware/auth.py:ANONYMOUS and require_role()."""
    response = await client.post("/api/v1/admin/collection/trigger", params={"source_code": "indigo"})
    assert response.status_code == 403


@requires_db
async def test_admin_endpoint_rejects_public_role_key(client: AsyncClient):
    """A valid but under-privileged key must be forbidden, not merely unauthenticated -
    the two failure modes are different and both must be tested."""
    # This test assumes a seeded PUBLIC-role demo key is available via the fixture
    # environment; see seeds/load_seed.py for how such a key is minted.
    import os

    public_key = os.environ.get("TEST_PUBLIC_API_KEY")
    if not public_key:
        pytest.skip("TEST_PUBLIC_API_KEY not set")
    response = await client.post(
        "/api/v1/admin/collection/trigger",
        params={"source_code": "indigo"},
        headers={"X-API-Key": public_key},
    )
    assert response.status_code == 403


@requires_db
async def test_manual_collection_trigger_writes_an_audit_log_entry(client: AsyncClient):
    import os

    admin_key = os.environ.get("TEST_ADMIN_API_KEY")
    if not admin_key:
        pytest.skip("TEST_ADMIN_API_KEY not set")

    response = await client.post(
        "/api/v1/admin/collection/trigger",
        params={"source_code": "indigo"},
        headers={"X-API-Key": admin_key},
    )
    assert response.status_code == 200

    audit_response = await client.get("/api/v1/admin/audit-log", headers={"X-API-Key": admin_key})
    actions = [row["action"] for row in audit_response.json()["data"]]
    assert "MANUAL_SCRAPE_TRIGGERED" in actions
