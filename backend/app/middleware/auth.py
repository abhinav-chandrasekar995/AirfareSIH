"""API key authentication and role-based authorisation.

Authorisation is a FastAPI dependency applied at the router level, and every protected
query additionally runs under a database session whose RLS role is set from the
principal (see `db/rls.py`). Frontend role checks are presentation only and are never
the enforcement point (build prompt Sec.6).
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, Header, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.constants import Role
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.security import extract_prefix, verify_key
from app.db.models import ApiKey
from app.db.rls import apply_principal
from app.db.session import get_session


@dataclass(frozen=True)
class Principal:
    key_id: int | None
    label: str
    role: Role
    rate_limit_per_min: int

    @property
    def is_anonymous(self) -> bool:
        return self.key_id is None


ANONYMOUS = Principal(
    key_id=None,
    label="anonymous",
    role=Role.PUBLIC,
    rate_limit_per_min=settings.public_rate_limit_per_min,
)


async def resolve_principal(
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
) -> Principal:
    """Resolve the caller and bind the RLS role for the rest of this request's session.

    This is the one place in the codebase allowed to look up `api_keys` before the
    caller's identity is known - the same bootstrap problem every authentication system
    has (a login check must read the credentials table before it knows who is asking).
    The lookup below runs under a deliberately narrow, code-controlled ADMIN elevation
    (the query is fixed and scoped to `key_prefix = :prefix`, never attacker-influenced
    beyond that one equality), and is immediately replaced by the caller's real,
    verified role for every query the route handler goes on to make on this same
    session (build prompt Sec.6: RLS is the actual boundary, not this dependency).
    """
    if not x_api_key:
        await apply_principal(session, ANONYMOUS.role)
        request.state.principal = ANONYMOUS
        return ANONYMOUS

    prefix = extract_prefix(x_api_key)

    await apply_principal(session, Role.ADMIN)
    result = await session.execute(
        select(ApiKey).where(ApiKey.key_prefix == prefix, ApiKey.is_active.is_(True))
    )
    record = result.scalar_one_or_none()

    if record is None or not verify_key(x_api_key, record.key_hash):
        await apply_principal(session, ANONYMOUS.role)
        raise UnauthorizedError("invalid or inactive API key")

    principal = Principal(
        key_id=record.key_id,
        label=record.owner_name,
        role=Role(record.role),
        rate_limit_per_min=record.rate_limit_per_min,
    )
    await apply_principal(session, principal.role, principal.key_id)
    request.state.principal = principal
    return principal


def require_role(minimum: Role):
    """Dependency factory enforcing a minimum role."""

    async def _guard(principal: Principal = Depends(resolve_principal)) -> Principal:
        if principal.role.rank < minimum.rank:
            raise ForbiddenError(
                f"this endpoint requires the {minimum.value} role; "
                f"the presented credential has {principal.role.value}"
            )
        return principal

    return _guard


require_analyst = require_role(Role.ANALYST)
require_admin = require_role(Role.ADMIN)
