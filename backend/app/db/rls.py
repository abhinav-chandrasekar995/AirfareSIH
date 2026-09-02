"""Row Level Security session binding.

Build prompt Sec.6 requires RLS enforced at the data layer, not merely in the frontend
or the API dependency graph. The policies themselves live in the Alembic migration; this
module binds the current request's principal onto the database session so those policies
have something to evaluate.

The application connects as a NOSUPERUSER, NOBYPASSRLS role, so a missing or wrong
`app.role` setting fails closed - the query returns nothing rather than everything.
"""
from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import Role


async def apply_principal(session: AsyncSession, role: Role, key_id: int | None = None) -> None:
    """Set the RLS context for this transaction.

    `set_config(..., true)` scopes the setting to the transaction, so a pooled
    connection cannot leak one caller's privileges into the next request.
    """
    await session.execute(
        text("SELECT set_config('app.role', :role, true)"),
        {"role": role.value},
    )
    await session.execute(
        text("SELECT set_config('app.key_id', :key_id, true)"),
        {"key_id": str(key_id) if key_id is not None else ""},
    )


async def current_context(session: AsyncSession) -> dict[str, str]:
    """Read back the active RLS context - used by the security tests."""
    result = await session.execute(
        text(
            "SELECT current_setting('app.role', true) AS role, "
            "current_setting('app.key_id', true) AS key_id"
        )
    )
    row = result.mappings().one()
    return {"role": row["role"] or "", "key_id": row["key_id"] or ""}
