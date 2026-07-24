"""Python library and CLI for the Hybrid Analysis (Falcon Sandbox) API v2."""

from __future__ import annotations

from .aio import AsyncHybridAnalysisClient, AsyncTransport
from .client import HybridAnalysisClient
from .config import Config, load
from .errors import (
    APIError,
    AuthenticationError,
    ConfigError,
    HybridAnalysisError,
    NetworkError,
    NotFoundError,
    RateLimitError,
)
from .formats import to_json, to_sarif, to_toon
from .transport import Transport

__version__ = "0.1.0"

__all__ = [
    "APIError",
    "AsyncHybridAnalysisClient",
    "AsyncTransport",
    "AuthenticationError",
    "Config",
    "ConfigError",
    "HybridAnalysisClient",
    "HybridAnalysisError",
    "NetworkError",
    "NotFoundError",
    "RateLimitError",
    "Transport",
    "__version__",
    "load",
    "to_json",
    "to_sarif",
    "to_toon",
]
