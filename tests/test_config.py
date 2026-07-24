"""Tests for configuration loading (env and TOML file, no patching)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from hybridanalysis.config import (
    API_KEY_ENV,
    BASE_URL_ENV,
    DEFAULT_BASE_URL,
    DEFAULT_TIMEOUT,
    DEFAULT_USER_AGENT,
    TIMEOUT_ENV,
    USER_AGENT_ENV,
    Config,
    load,
)
from hybridanalysis.errors import ConfigError


def test_config_defaults() -> None:
    config = Config(api_key="k")
    assert config.base_url == DEFAULT_BASE_URL
    assert config.user_agent == DEFAULT_USER_AGENT
    assert config.timeout == DEFAULT_TIMEOUT


def test_api_key_not_in_repr() -> None:
    config = Config(api_key="super-secret-key")
    assert "super-secret-key" not in repr(config)
    assert config.api_key == "super-secret-key"


def test_load_from_env_key_and_url() -> None:
    env = {API_KEY_ENV: "env-key", BASE_URL_ENV: "https://example.test/api/v2/"}
    config = load(env=env, config_path=Path("/nonexistent/nope.toml"))
    assert config.api_key == "env-key"
    assert config.base_url == "https://example.test/api/v2"


def test_load_env_key_defaults_base_url() -> None:
    config = load(env={API_KEY_ENV: "env-key"}, config_path=Path("/nonexistent/nope.toml"))
    assert config.base_url == DEFAULT_BASE_URL


def test_load_from_config_file(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[hybridanalysis]\napi_key = "file-key"\nbase_url = "https://f.test/v2"\n')
    config = load(env={}, config_path=path)
    assert config.api_key == "file-key"
    assert config.base_url == "https://f.test/v2"


def test_env_key_takes_precedence_over_file(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[hybridanalysis]\napi_key = "file-key"\n')
    config = load(env={API_KEY_ENV: "env-key"}, config_path=path)
    assert config.api_key == "env-key"


def test_load_from_cwd_file(tmp_path: Path) -> None:
    (tmp_path / ".hybridanalysis.toml").write_text('[hybridanalysis]\napi_key = "cwd-key"\n')
    original = Path.cwd()
    os.chdir(tmp_path)
    try:
        config = load(env={})
    finally:
        os.chdir(original)
    assert config.api_key == "cwd-key"


def test_missing_key_raises(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="No API key"):
        load(env={}, config_path=tmp_path / "absent.toml")


def test_non_string_api_key_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text("[hybridanalysis]\napi_key = 123\n")
    with pytest.raises(ConfigError, match="must be a string"):
        load(env={}, config_path=path)


def test_non_table_section_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('hybridanalysis = "oops"\n')
    with pytest.raises(ConfigError, match="must be a table"):
        load(env={}, config_path=path)


def test_non_string_base_url_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[hybridanalysis]\napi_key = "k"\nbase_url = 5\n')
    with pytest.raises(ConfigError, match="base_url"):
        load(env={}, config_path=path)


def test_malformed_toml_raises_config_error(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[hybridanalysis]\napi_key = "x\n')  # unterminated string
    with pytest.raises(ConfigError, match="Invalid TOML"):
        load(env={}, config_path=path)


def test_timeout_and_user_agent_from_env() -> None:
    env = {API_KEY_ENV: "k", TIMEOUT_ENV: "12.5", USER_AGENT_ENV: "custom-agent"}
    config = load(env=env, config_path=Path("/nonexistent/nope.toml"))
    assert config.timeout == 12.5
    assert config.user_agent == "custom-agent"


def test_timeout_and_user_agent_from_file(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[hybridanalysis]\napi_key = "k"\ntimeout = 30\nuser_agent = "file-agent"\n')
    config = load(env={}, config_path=path)
    assert config.timeout == 30.0
    assert config.user_agent == "file-agent"


def test_defaults_when_unset(tmp_path: Path) -> None:
    config = load(env={API_KEY_ENV: "k"}, config_path=tmp_path / "absent.toml")
    assert config.timeout == DEFAULT_TIMEOUT
    assert config.user_agent == DEFAULT_USER_AGENT


def test_invalid_timeout_env_raises() -> None:
    with pytest.raises(ConfigError, match="timeout"):
        load(env={API_KEY_ENV: "k", TIMEOUT_ENV: "not-a-number"}, config_path=Path("/no.toml"))


def test_non_numeric_timeout_in_file_raises(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text('[hybridanalysis]\napi_key = "k"\ntimeout = true\n')
    with pytest.raises(ConfigError, match="timeout"):
        load(env={}, config_path=path)
