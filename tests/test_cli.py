"""Tests for the Click CLI, driven against the real local server."""

from __future__ import annotations

import json
import runpy
import sys
from pathlib import Path

import pytest
from click.testing import CliRunner, Result

from hybridanalysis.cli import _build_client, _LazyClient, _resolve_config, cli, main
from hybridanalysis.config import DEFAULT_BASE_URL

from .api_server import VALID_KEY, LocalAPIServer

runner = CliRunner()


def run(server: LocalAPIServer, *args: str) -> Result:
    base = ["--api-key", VALID_KEY, "--base-url", server.base_url]
    return runner.invoke(cli, [*base, *args])


NOARG_JSON: list[tuple[tuple[str, ...], str]] = [
    (("system", "version"), "/system/version"),
    (("system", "environments"), "/system/environments"),
    (("system", "action-scripts"), "/system/action-scripts"),
    (("system", "stats"), "/system/stats"),
    (("system", "configuration"), "/system/configuration"),
    (("system", "queue-size"), "/system/queue-size"),
    (("system", "total-submissions"), "/system/total-submissions"),
    (("key", "current"), "/key/current"),
    (("key", "submission-quota"), "/key/submission-quota"),
    (("feed", "detonation"), "/feed/detonation"),
    (("feed", "quick-scan"), "/feed/quick-scan"),
    (("abuse-reports", "feed"), "/abuse-reports/feed"),
    (("quick-scan", "state"), "/quick-scan/state"),
]

ARG_JSON: list[tuple[tuple[str, ...], str]] = [
    (("overview", "get", "abc"), "/overview/abc"),
    (("overview", "summary", "abc"), "/overview/abc/summary"),
    (("overview", "refresh", "abc"), "/overview/abc/refresh"),
    (("search", "hash", "deadbeef"), "/search/hash"),
    (("quick-scan", "get", "id1"), "/quick-scan/id1"),
    (("report", "state", "job1"), "/report/job1/state"),
    (("report", "summary", "job1"), "/report/job1/summary"),
    (("report", "json", "job1"), "/report/job1/report/json"),
    (("report", "children", "job1"), "/report/job1/children"),
    (("report", "screenshots", "job1"), "/report/job1/screenshots"),
    (("report", "memory-dumps-list", "job1"), "/report/job1/memory-dumps-list"),
    (
        ("report", "memory-dump-extracted-strings", "job1", "mem.dmp"),
        "/report/job1/memory-dump/extracted-strings",
    ),
    (("file-collection", "get", "c1"), "/file-collection/c1"),
]

FIELDS_JSON: list[tuple[tuple[str, ...], str]] = [
    (("search", "terms", "filetype=peexe"), "/search/terms"),
    (("abuse-reports", "new", "abc123", "mistake"), "/abuse-reports/new"),
    (
        ("quick-scan", "convert-to-full", "id1", "environment_id=100"),
        "/quick-scan/id1/convert-to-full",
    ),
    (("quick-scan", "url", "http://x.test", "--scan-type", "all"), "/quick-scan/url"),
    (("submit", "url", "http://x.test", "environment_id=100"), "/submit/url"),
    (("submit", "hash-for-url", "http://x.test"), "/submit/hash-for-url"),
    (("submit", "dropped-file", "job1", "abc123"), "/submit/dropped-file"),
    (("file-collection", "create", "collection_name=col"), "/file-collection/create"),
    (("file-collection", "search", "tag=ransomware"), "/file-collection/search"),
]

DELETE_CMDS: list[tuple[str, ...]] = [
    ("file-collection", "delete", "c1"),
    ("file-collection", "remove-file", "c1", "h1"),
]

BINARY_CMDS: list[tuple[str, ...]] = [
    ("overview", "sample", "abc"),
    ("report", "sample", "job1"),
    ("report", "pcap", "job1"),
    ("report", "certificate", "job1"),
    ("report", "dropped-file", "job1", "h1"),
    ("report", "dropped-file-raw", "job1", "h1"),
    ("report", "dropped-files", "job1"),
    ("file-collection", "download", "c1"),
]

TEXT_CMDS: list[tuple[tuple[str, ...], str]] = [
    (("report", "memory-strings", "job1"), "memory-strings"),
    (("report", "memory-dump-hex-dump", "job1", "mem.dmp"), "hex-dump"),
]


@pytest.mark.parametrize(("args", "expected_path"), NOARG_JSON + ARG_JSON)
def test_json_commands(server: LocalAPIServer, args: tuple[str, ...], expected_path: str) -> None:
    result = run(server, *args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["path"] == expected_path


@pytest.mark.parametrize(("args", "expected_path"), FIELDS_JSON)
def test_fields_commands(server: LocalAPIServer, args: tuple[str, ...], expected_path: str) -> None:
    result = run(server, *args)
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["path"] == expected_path


@pytest.mark.parametrize("args", DELETE_CMDS)
def test_delete_commands_print_null(server: LocalAPIServer, args: tuple[str, ...]) -> None:
    result = run(server, *args)
    assert result.exit_code == 0, result.output
    assert result.output.strip() == "null"


@pytest.mark.parametrize(("args", "needle"), TEXT_CMDS)
def test_text_commands(server: LocalAPIServer, args: tuple[str, ...], needle: str) -> None:
    result = run(server, *args)
    assert result.exit_code == 0, result.output
    assert needle in result.output


@pytest.mark.parametrize("args", BINARY_CMDS)
def test_binary_commands_write_file(
    server: LocalAPIServer, tmp_path: Path, args: tuple[str, ...]
) -> None:
    out = tmp_path / "artifact.bin"
    result = run(server, *args, "--out", str(out))
    assert result.exit_code == 0, result.output
    assert out.read_bytes() == b"BINARY-DATA"
    assert "Wrote" in result.output


def test_binary_command_to_stdout(server: LocalAPIServer) -> None:
    result = run(server, "overview", "sample", "abc")
    assert result.exit_code == 0
    assert result.stdout_bytes == b"BINARY-DATA"


def test_download_selected_with_hashes(server: LocalAPIServer, tmp_path: Path) -> None:
    out = tmp_path / "sel.zip"
    result = run(
        server, "file-collection", "download-selected", "c1", "h1", "h2", "--out", str(out)
    )
    assert result.exit_code == 0, result.output
    assert out.read_bytes() == b"BINARY-DATA"
    assert server.requests[-1].form["hashes[]"] == ["h1", "h2"]


def test_file_upload_commands(server: LocalAPIServer, tmp_path: Path) -> None:
    sample = tmp_path / "s.bin"
    sample.write_bytes(b"data")
    for args in (
        ("quick-scan", "file", str(sample), "--scan-type", "all"),
        ("submit", "file", str(sample)),
        ("file-collection", "add-file", "c1", str(sample)),
    ):
        result = run(server, *args)
        assert result.exit_code == 0, result.output


def test_format_toon_output(server: LocalAPIServer) -> None:
    result = run(server, "system", "version", "-f", "toon")
    assert result.exit_code == 0, result.output
    assert "path:" in result.output  # TOON renders keys without JSON braces


def test_format_sarif_derives_source_from_argument(server: LocalAPIServer) -> None:
    result = run(server, "overview", "get", "abc", "--format", "sarif")
    assert result.exit_code == 0, result.output
    doc = json.loads(result.output)
    assert doc["version"] == "2.1.0"
    assert doc["runs"][0]["tool"]["driver"]["name"] == "hybridanalysis"


def test_sarif_rejected_on_non_analysis_command(server: LocalAPIServer) -> None:
    result = run(server, "system", "version", "--format", "sarif")
    assert result.exit_code == 2
    assert "sarif" in result.output


def test_bad_field_pair_errors(server: LocalAPIServer) -> None:
    result = run(server, "search", "terms", "novalue")
    assert result.exit_code == 2
    assert "KEY=VALUE" in result.output


def test_api_error_maps_to_click_error(server: LocalAPIServer) -> None:
    result = run(server, "overview", "get", "trigger-404")
    assert result.exit_code == 1
    assert "404" in result.output


@pytest.mark.parametrize(
    "args", [["--help"], ["system", "--help"], ["report", "summary", "--help"]]
)
def test_help_needs_no_credentials(args: list[str]) -> None:
    result = runner.invoke(cli, args, env={"HYBRIDANALYSIS": "", "HYBRIDANALYSIS_URL": ""})
    assert result.exit_code == 0, result.output
    assert "Usage:" in result.output


def test_lazy_client_builds_once_and_closes(server: LocalAPIServer) -> None:
    lazy = _LazyClient(VALID_KEY, server.base_url, None)
    assert lazy.system.version()["path"] == "/system/version"  # builds
    assert lazy.key.current()["path"] == "/key/current"  # reuses cached client
    lazy.close()  # closes the built client


def test_lazy_client_close_without_build() -> None:
    _LazyClient("k", None, None).close()  # never built -> no-op, no network


def test_resolve_config_api_key_default_base_url() -> None:
    assert _resolve_config("k", None, None).base_url == DEFAULT_BASE_URL


def test_resolve_config_explicit_base_url() -> None:
    assert _resolve_config("k", "https://x.test/api/", None).base_url == "https://x.test/api"


def test_resolve_config_from_file_no_override(tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f'[hybridanalysis]\napi_key = "{VALID_KEY}"\n')
    assert _resolve_config(None, None, str(path)).base_url == DEFAULT_BASE_URL


def test_build_client_from_file_with_override(server: LocalAPIServer, tmp_path: Path) -> None:
    path = tmp_path / "config.toml"
    path.write_text(f'[hybridanalysis]\napi_key = "{VALID_KEY}"\n')
    client = _build_client(None, server.base_url, str(path))
    try:
        assert client.system.version()["path"] == "/system/version"
    finally:
        client.close()


def test_main_help_via_runpy() -> None:
    original = sys.argv
    sys.argv = ["hybridanalysis", "--help"]
    try:
        with pytest.raises(SystemExit) as info:
            runpy.run_module("hybridanalysis", run_name="__main__")
    finally:
        sys.argv = original
    assert info.value.code == 0


def test_main_callable() -> None:
    original = sys.argv
    sys.argv = ["hybridanalysis", "--help"]
    try:
        with pytest.raises(SystemExit) as info:
            main()
    finally:
        sys.argv = original
    assert info.value.code == 0
