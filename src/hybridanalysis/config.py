"""Configuration loading for the Hybrid Analysis client.

The API key is resolved from the ``HYBRIDANALYSIS`` environment variable or a
local TOML config file, in that order. Everything is injectable (``env`` mapping
and ``config_path``) so callers and tests never rely on process-global state.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .errors import ConfigError

DEFAULT_BASE_URL = "https://hybrid-analysis.com/api/v2"
DEFAULT_USER_AGENT = "Falcon Sandbox"
DEFAULT_TIMEOUT = 60.0

API_KEY_ENV = "HYBRIDANALYSIS"
BASE_URL_ENV = "HYBRIDANALYSIS_URL"
USER_AGENT_ENV = "HYBRIDANALYSIS_USER_AGENT"
TIMEOUT_ENV = "HYBRIDANALYSIS_TIMEOUT"
_CONFIG_SECTION = "hybridanalysis"


@dataclass(frozen=True, slots=True)
class Config:
    """Immutable client configuration."""

    api_key: str = field(repr=False)  # keep the secret out of repr/logs/tracebacks
    base_url: str = DEFAULT_BASE_URL
    user_agent: str = DEFAULT_USER_AGENT
    timeout: float = DEFAULT_TIMEOUT


def _candidate_paths(config_path: Path | None) -> list[Path]:
    if config_path is not None:
        return [config_path]
    return [
        Path.cwd() / ".hybridanalysis.toml",
        Path.home() / ".config" / "hybridanalysis" / "config.toml",
    ]


def _load_file_section(config_path: Path | None) -> Mapping[str, object]:
    for path in _candidate_paths(config_path):
        if not path.is_file():
            continue
        with path.open("rb") as handle:
            try:
                data = tomllib.load(handle)
            except tomllib.TOMLDecodeError as exc:
                raise ConfigError(f"Invalid TOML in {path}: {exc}") from exc
        section = data.get(_CONFIG_SECTION, {})
        if not isinstance(section, dict):
            raise ConfigError(f"'[{_CONFIG_SECTION}]' in {path} must be a table")
        return section
    return {}


def _as_str(value: object, *, field: str) -> str:
    if not isinstance(value, str):
        raise ConfigError(f"Config field '{field}' must be a string")
    return value


def _as_float(value: object, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ConfigError(f"Config field '{field}' must be a number")
    try:
        return float(value)
    except ValueError:
        raise ConfigError(f"Config field '{field}' must be a number, got {value!r}") from None


def _resolve(
    env: Mapping[str, str], env_key: str, section: Mapping[str, object], file_key: str
) -> object:
    """Return the env value (if set and non-empty), else the config-file value."""
    return env.get(env_key) or section.get(file_key)


def load(
    env: Mapping[str, str] | None = None,
    config_path: Path | None = None,
) -> Config:
    """Build a :class:`Config` from the environment and/or a TOML file.

    Each field resolves from its environment variable first, then the matching key
    in the ``[hybridanalysis]`` table, then the default: ``api_key`` (``HYBRIDANALYSIS``,
    required), ``base_url`` (``HYBRIDANALYSIS_URL``), ``user_agent``
    (``HYBRIDANALYSIS_USER_AGENT``) and ``timeout`` (``HYBRIDANALYSIS_TIMEOUT``, seconds).
    """
    env = os.environ if env is None else env
    section = _load_file_section(config_path)

    api_key = env.get(API_KEY_ENV)
    if not api_key:
        raw_key = section.get("api_key")
        api_key = _as_str(raw_key, field="api_key") if raw_key is not None else None
    if not api_key:
        raise ConfigError(
            f"No API key found. Set the {API_KEY_ENV} environment variable or add "
            f"'api_key' under [{_CONFIG_SECTION}] in a config file."
        )

    raw_url = _resolve(env, BASE_URL_ENV, section, "base_url")
    base_url = _as_str(raw_url, field="base_url") if raw_url is not None else DEFAULT_BASE_URL

    raw_ua = _resolve(env, USER_AGENT_ENV, section, "user_agent")
    user_agent = _as_str(raw_ua, field="user_agent") if raw_ua is not None else DEFAULT_USER_AGENT

    raw_timeout = _resolve(env, TIMEOUT_ENV, section, "timeout")
    timeout = (
        _as_float(raw_timeout, field="timeout") if raw_timeout is not None else DEFAULT_TIMEOUT
    )

    return Config(
        api_key=api_key,
        base_url=base_url.rstrip("/"),
        user_agent=user_agent,
        timeout=timeout,
    )
