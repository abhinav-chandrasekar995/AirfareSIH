"""CPI disclaimer injection.

Build prompt Sec.15 requires the disclaimer in every relevant API response. It is
already a field on the analytics result object (D-015); this middleware is the second
layer, guaranteeing that any response from a CPI path carries it even if a future
endpoint forgets. Two independent mechanisms, because misreading the simulator as an
official CPI claim is the single largest credibility risk in the product.
"""
from __future__ import annotations

import json

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.analytics.cpi import DISCLAIMER

CPI_PATH_MARKERS = ("/cpi-simulation", "/cpi_simulation")


class CpiDisclaimerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if not any(marker in request.url.path for marker in CPI_PATH_MARKERS):
            return response
        if response.status_code >= 400 or response.media_type != "application/json":
            return response

        body = b"".join([chunk async for chunk in response.body_iterator])
        try:
            payload = json.loads(body)
        except (json.JSONDecodeError, UnicodeDecodeError):
            return Response(
                content=body,
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type=response.media_type,
            )

        if isinstance(payload, dict) and not payload.get("disclaimer"):
            payload["disclaimer"] = DISCLAIMER

        new_body = json.dumps(payload, default=str).encode()
        headers = dict(response.headers)
        headers["content-length"] = str(len(new_body))
        return Response(
            content=new_body,
            status_code=response.status_code,
            headers=headers,
            media_type="application/json",
        )
