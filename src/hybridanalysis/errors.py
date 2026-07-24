"""Exception hierarchy for the Hybrid Analysis client."""

from __future__ import annotations


class HybridAnalysisError(Exception):
    """Base class for every error raised by this package."""


class ConfigError(HybridAnalysisError):
    """Raised when the API key or configuration cannot be resolved."""


class NetworkError(HybridAnalysisError):
    """Raised when the request fails before a response (timeout, connection)."""


class APIError(HybridAnalysisError):
    """Raised when the API returns an unsuccessful HTTP status.

    Carries the HTTP ``status_code`` and the raw response ``body`` so callers can
    inspect what the service returned.
    """

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"API request failed with status {status_code}: {body}")


class AuthenticationError(APIError):
    """Raised for 401/403 responses (missing or invalid API key)."""


class NotFoundError(APIError):
    """Raised for 404 responses."""


class RateLimitError(APIError):
    """Raised for 429 responses (submission quota or rate limit exceeded)."""


_ERROR_BY_STATUS: dict[int, type[APIError]] = {
    401: AuthenticationError,
    403: AuthenticationError,
    404: NotFoundError,
    429: RateLimitError,
}


def error_for_status(status_code: int, body: str) -> APIError:
    """Map an HTTP error status to the matching :class:`APIError` subclass."""
    return _ERROR_BY_STATUS.get(status_code, APIError)(status_code, body)
