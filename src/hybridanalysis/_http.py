"""HTTP plumbing shared by the sync and async transports.

Client construction options and response handling live here once, so the only
difference between the two transports is ``httpx.Client`` vs ``httpx.AsyncClient``
and the ``await``.
"""

from __future__ import annotations

from typing import Any, Literal

import httpx

from .config import Config
from .errors import error_for_status

Parse = Literal["json", "text", "bytes"]


def client_kwargs(config: Config) -> dict[str, Any]:
    """Keyword arguments shared by ``httpx.Client`` and ``httpx.AsyncClient``."""
    return {
        "base_url": config.base_url,
        "headers": {"api-key": config.api_key, "User-Agent": config.user_agent},
        "timeout": config.timeout,
    }


def parse_response(response: httpx.Response, parse: Parse) -> Any:
    """Return the response body in the requested form, raising on error status."""
    if response.status_code >= 400:
        raise error_for_status(response.status_code, response.text)
    if parse == "bytes":
        return response.content
    if parse == "text":
        return response.text
    if not response.content:
        return None
    return response.json()
