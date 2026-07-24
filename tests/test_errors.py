"""Tests for the exception hierarchy."""

from __future__ import annotations

import pytest

from hybridanalysis.errors import (
    APIError,
    AuthenticationError,
    HybridAnalysisError,
    NotFoundError,
    RateLimitError,
    error_for_status,
)


def test_api_error_carries_status_and_body() -> None:
    error = APIError(500, "boom")
    assert error.status_code == 500
    assert error.body == "boom"
    assert "500" in str(error)
    assert "boom" in str(error)


def test_error_subclassing() -> None:
    for cls in (APIError, AuthenticationError, NotFoundError, RateLimitError):
        assert issubclass(cls, HybridAnalysisError)
    assert issubclass(AuthenticationError, APIError)


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (401, AuthenticationError),
        (403, AuthenticationError),
        (404, NotFoundError),
        (429, RateLimitError),
        (400, APIError),
        (500, APIError),
    ],
)
def test_error_for_status_maps_known_codes(status: int, expected: type[APIError]) -> None:
    error = error_for_status(status, "body")
    assert type(error) is expected
    assert error.status_code == status
    assert error.body == "body"
