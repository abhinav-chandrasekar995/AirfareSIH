"""Domain exceptions mapped to HTTP responses by the app error handler."""
from __future__ import annotations


class AirfareError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(AirfareError):
    status_code = 404
    code = "not_found"


class ValidationError(AirfareError):
    status_code = 422
    code = "validation_error"


class UnauthorizedError(AirfareError):
    status_code = 401
    code = "unauthorized"


class ForbiddenError(AirfareError):
    status_code = 403
    code = "forbidden"


class RateLimitedError(AirfareError):
    status_code = 429
    code = "rate_limited"


class InsufficientDataError(AirfareError):
    """Raised when a statistic cannot be computed from the observations available.

    Distinct from NotFound: the route exists, the period exists, but publishing a
    number from too few observations would be worse than reporting the gap.
    """

    status_code = 409
    code = "insufficient_data"
