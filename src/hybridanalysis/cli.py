"""Click command-line interface mirroring the library resource methods."""

from __future__ import annotations

import dataclasses
from pathlib import Path
from typing import Any

import click

from .client import HybridAnalysisClient
from .config import DEFAULT_BASE_URL, Config, load
from .errors import HybridAnalysisError
from .formats import to_json, to_sarif, to_toon


class _CLIGroup(click.Group):
    """Group that turns library errors into clean CLI errors."""

    def invoke(self, ctx: click.Context) -> Any:
        try:
            return super().invoke(ctx)
        except HybridAnalysisError as exc:
            raise click.ClickException(str(exc)) from exc


def _resolve_config(api_key: str | None, base_url: str | None, config_path: str | None) -> Config:
    if api_key:
        base = (base_url or DEFAULT_BASE_URL).rstrip("/")
        return Config(api_key=api_key, base_url=base)
    config = load(config_path=Path(config_path) if config_path else None)
    if base_url:
        config = dataclasses.replace(config, base_url=base_url.rstrip("/"))
    return config


def _build_client(
    api_key: str | None, base_url: str | None, config_path: str | None
) -> HybridAnalysisClient:
    return HybridAnalysisClient(_resolve_config(api_key, base_url, config_path))


class _LazyClient:
    """Builds the real client on first resource access.

    Deferring construction means ``--help`` on a subcommand (which never touches a
    resource) works without any API key or config file.
    """

    def __init__(self, api_key: str | None, base_url: str | None, config_path: str | None) -> None:
        self._params = (api_key, base_url, config_path)
        self._client: HybridAnalysisClient | None = None

    def _ensure(self) -> HybridAnalysisClient:
        if self._client is None:
            self._client = _build_client(*self._params)
        return self._client

    def __getattr__(self, name: str) -> Any:
        return getattr(self._ensure(), name)

    def close(self) -> None:
        if self._client is not None:
            self._client.close()


def _parse_fields(pairs: tuple[str, ...]) -> dict[str, str]:
    fields: dict[str, str] = {}
    for pair in pairs:
        key, sep, value = pair.partition("=")
        if not sep:
            raise click.BadParameter(f"Expected KEY=VALUE, got {pair!r}")
        fields[key] = value
    return fields


def _emit(data: Any, fmt: str, source: str | None = None) -> None:
    if fmt == "toon":
        click.echo(to_toon(data))
    elif fmt == "sarif":
        click.echo(to_sarif(data, source=source))
    else:
        click.echo(to_json(data))


def _emit_text(text: str) -> None:
    click.echo(text)


def _emit_bytes(data: bytes, out: str | None) -> None:
    if out is not None:
        Path(out).write_bytes(data)
        click.echo(f"Wrote {len(data)} bytes to {out}")
    else:
        click.get_binary_stream("stdout").write(data)


_out_option = click.option("-o", "--out", type=click.Path(dir_okay=False), default=None)
_format_option = click.option(
    "-f",
    "--format",
    "fmt",
    type=click.Choice(["json", "toon"]),
    default="json",
    help="Output format.",
)
_format_analysis_option = click.option(
    "-f",
    "--format",
    "fmt",
    type=click.Choice(["json", "toon", "sarif"]),
    default="json",
    help="Output format (sarif maps verdict/signatures to SARIF 2.1.0).",
)


@click.group(cls=_CLIGroup)
@click.option("--api-key", default=None, help="API key (overrides env and config file).")
@click.option("--base-url", default=None, help="Base URL override.")
@click.option(
    "--config",
    "config_path",
    type=click.Path(dir_okay=False),
    default=None,
    help="Path to a TOML config file.",
)
@click.pass_context
def cli(
    ctx: click.Context, api_key: str | None, base_url: str | None, config_path: str | None
) -> None:
    """Interact with the Hybrid Analysis (Falcon Sandbox) API v2."""
    ctx.obj = _LazyClient(api_key, base_url, config_path)
    ctx.call_on_close(ctx.obj.close)


# --- system ---------------------------------------------------------------
@cli.group()
def system() -> None:
    """System information endpoints."""


@system.command("version")
@_format_option
@click.pass_obj
def system_version(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.system.version(), fmt)


@system.command("environments")
@_format_option
@click.pass_obj
def system_environments(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.system.environments(), fmt)


@system.command("action-scripts")
@_format_option
@click.pass_obj
def system_action_scripts(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.system.action_scripts(), fmt)


@system.command("stats")
@_format_option
@click.pass_obj
def system_stats(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.system.stats(), fmt)


@system.command("configuration")
@_format_option
@click.pass_obj
def system_configuration(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.system.configuration(), fmt)


@system.command("queue-size")
@_format_option
@click.pass_obj
def system_queue_size(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.system.queue_size(), fmt)


@system.command("total-submissions")
@_format_option
@click.pass_obj
def system_total_submissions(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.system.total_submissions(), fmt)


# --- key ------------------------------------------------------------------
@cli.group()
def key() -> None:
    """API key endpoints."""


@key.command("current")
@_format_option
@click.pass_obj
def key_current(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.key.current(), fmt)


@key.command("submission-quota")
@_format_option
@click.pass_obj
def key_submission_quota(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.key.submission_quota(), fmt)


# --- feed -----------------------------------------------------------------
@cli.group()
def feed() -> None:
    """Feed endpoints."""


@feed.command("detonation")
@_format_analysis_option
@click.pass_obj
def feed_detonation(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.feed.detonation(), fmt)


@feed.command("quick-scan")
@_format_analysis_option
@click.pass_obj
def feed_quick_scan(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.feed.quick_scan(), fmt)


# --- overview -------------------------------------------------------------
@cli.group()
def overview() -> None:
    """Analysis overview endpoints."""


@overview.command("get")
@click.argument("sha256")
@_format_analysis_option
@click.pass_obj
def overview_get(client: HybridAnalysisClient, sha256: str, fmt: str) -> None:
    _emit(client.overview.get(sha256), fmt, source=sha256)


@overview.command("summary")
@click.argument("sha256")
@_format_analysis_option
@click.pass_obj
def overview_summary(client: HybridAnalysisClient, sha256: str, fmt: str) -> None:
    _emit(client.overview.summary(sha256), fmt, source=sha256)


@overview.command("refresh")
@click.argument("sha256")
@_format_analysis_option
@click.pass_obj
def overview_refresh(client: HybridAnalysisClient, sha256: str, fmt: str) -> None:
    _emit(client.overview.refresh(sha256), fmt, source=sha256)


@overview.command("sample")
@click.argument("sha256")
@_out_option
@click.pass_obj
def overview_sample(client: HybridAnalysisClient, sha256: str, out: str | None) -> None:
    _emit_bytes(client.overview.sample(sha256), out)


# --- search ---------------------------------------------------------------
@cli.group()
def search() -> None:
    """Search endpoints."""


@search.command("hash")
@click.argument("hash_value")
@_format_analysis_option
@click.pass_obj
def search_hash(client: HybridAnalysisClient, hash_value: str, fmt: str) -> None:
    _emit(client.search.hash(hash_value), fmt, source=hash_value)


@search.command("terms")
@click.argument("fields", nargs=-1)
@_format_analysis_option
@click.pass_obj
def search_terms(client: HybridAnalysisClient, fields: tuple[str, ...], fmt: str) -> None:
    _emit(client.search.terms(**_parse_fields(fields)), fmt)


# --- abuse-reports --------------------------------------------------------
@cli.group("abuse-reports")
def abuse_reports() -> None:
    """Report deletion endpoints."""


@abuse_reports.command("new")
@click.argument("sha256")
@click.argument("reason")
@click.argument("fields", nargs=-1)
@_format_option
@click.pass_obj
def abuse_reports_new(
    client: HybridAnalysisClient, sha256: str, reason: str, fields: tuple[str, ...], fmt: str
) -> None:
    _emit(client.abuse_reports.new(sha256, reason, **_parse_fields(fields)), fmt)


@abuse_reports.command("feed")
@_format_option
@click.pass_obj
def abuse_reports_feed(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.abuse_reports.feed(), fmt)


# --- quick-scan -----------------------------------------------------------
@cli.group("quick-scan")
def quick_scan() -> None:
    """Quick-scan endpoints."""


@quick_scan.command("state")
@_format_analysis_option
@click.pass_obj
def quick_scan_state(client: HybridAnalysisClient, fmt: str) -> None:
    _emit(client.quick_scan.state(), fmt)


@quick_scan.command("file")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
@click.option("--scan-type", required=True)
@click.argument("fields", nargs=-1)
@_format_analysis_option
@click.pass_obj
def quick_scan_file(
    client: HybridAnalysisClient,
    file_path: str,
    scan_type: str,
    fields: tuple[str, ...],
    fmt: str,
) -> None:
    _emit(
        client.quick_scan.file(file_path, scan_type=scan_type, **_parse_fields(fields)),
        fmt,
        source=file_path,
    )


@quick_scan.command("url")
@click.argument("url")
@click.option("--scan-type", required=True)
@click.argument("fields", nargs=-1)
@_format_analysis_option
@click.pass_obj
def quick_scan_url(
    client: HybridAnalysisClient, url: str, scan_type: str, fields: tuple[str, ...], fmt: str
) -> None:
    _emit(
        client.quick_scan.url(url, scan_type=scan_type, **_parse_fields(fields)),
        fmt,
        source=url,
    )


@quick_scan.command("get")
@click.argument("scan_id")
@_format_analysis_option
@click.pass_obj
def quick_scan_get(client: HybridAnalysisClient, scan_id: str, fmt: str) -> None:
    _emit(client.quick_scan.get(scan_id), fmt, source=scan_id)


@quick_scan.command("convert-to-full")
@click.argument("scan_id")
@click.argument("fields", nargs=-1)
@_format_analysis_option
@click.pass_obj
def quick_scan_convert(
    client: HybridAnalysisClient, scan_id: str, fields: tuple[str, ...], fmt: str
) -> None:
    _emit(client.quick_scan.convert_to_full(scan_id, **_parse_fields(fields)), fmt, source=scan_id)


# --- submit ---------------------------------------------------------------
@cli.group()
def submit() -> None:
    """Sandbox submission endpoints."""


@submit.command("file")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("fields", nargs=-1)
@_format_option
@click.pass_obj
def submit_file(
    client: HybridAnalysisClient, file_path: str, fields: tuple[str, ...], fmt: str
) -> None:
    _emit(client.submit.file(file_path, **_parse_fields(fields)), fmt)


@submit.command("url")
@click.argument("url")
@click.argument("fields", nargs=-1)
@_format_option
@click.pass_obj
def submit_url(client: HybridAnalysisClient, url: str, fields: tuple[str, ...], fmt: str) -> None:
    _emit(client.submit.url(url, **_parse_fields(fields)), fmt)


@submit.command("hash-for-url")
@click.argument("url")
@click.argument("fields", nargs=-1)
@_format_option
@click.pass_obj
def submit_hash_for_url(
    client: HybridAnalysisClient, url: str, fields: tuple[str, ...], fmt: str
) -> None:
    _emit(client.submit.hash_for_url(url, **_parse_fields(fields)), fmt)


@submit.command("dropped-file")
@click.argument("report_id")
@click.argument("file_hash")
@click.argument("fields", nargs=-1)
@_format_option
@click.pass_obj
def submit_dropped_file(
    client: HybridAnalysisClient,
    report_id: str,
    file_hash: str,
    fields: tuple[str, ...],
    fmt: str,
) -> None:
    _emit(client.submit.dropped_file(report_id, file_hash, **_parse_fields(fields)), fmt)


# --- report ---------------------------------------------------------------
@cli.group()
def report() -> None:
    """Sandbox report endpoints."""


@report.command("state")
@click.argument("report_id")
@_format_analysis_option
@click.pass_obj
def report_state(client: HybridAnalysisClient, report_id: str, fmt: str) -> None:
    _emit(client.report.state(report_id), fmt, source=report_id)


@report.command("summary")
@click.argument("report_id")
@_format_analysis_option
@click.pass_obj
def report_summary(client: HybridAnalysisClient, report_id: str, fmt: str) -> None:
    _emit(client.report.summary(report_id), fmt, source=report_id)


@report.command("json")
@click.argument("report_id")
@_format_analysis_option
@click.pass_obj
def report_json(client: HybridAnalysisClient, report_id: str, fmt: str) -> None:
    _emit(client.report.json_report(report_id), fmt, source=report_id)


@report.command("children")
@click.argument("report_id")
@_format_analysis_option
@click.pass_obj
def report_children(client: HybridAnalysisClient, report_id: str, fmt: str) -> None:
    _emit(client.report.children(report_id), fmt, source=report_id)


@report.command("screenshots")
@click.argument("report_id")
@_format_analysis_option
@click.pass_obj
def report_screenshots(client: HybridAnalysisClient, report_id: str, fmt: str) -> None:
    _emit(client.report.screenshots(report_id), fmt, source=report_id)


@report.command("memory-dumps-list")
@click.argument("report_id")
@_format_analysis_option
@click.pass_obj
def report_memory_dumps_list(client: HybridAnalysisClient, report_id: str, fmt: str) -> None:
    _emit(client.report.memory_dumps_list(report_id), fmt, source=report_id)


@report.command("memory-dump-extracted-strings")
@click.argument("report_id")
@click.argument("filename")
@_format_analysis_option
@click.pass_obj
def report_memory_dump_extracted_strings(
    client: HybridAnalysisClient, report_id: str, filename: str, fmt: str
) -> None:
    _emit(client.report.memory_dump_extracted_strings(report_id, filename), fmt, source=report_id)


@report.command("memory-strings")
@click.argument("report_id")
@click.pass_obj
def report_memory_strings(client: HybridAnalysisClient, report_id: str) -> None:
    _emit_text(client.report.memory_strings(report_id))


@report.command("memory-dump-hex-dump")
@click.argument("report_id")
@click.argument("filename")
@click.pass_obj
def report_memory_dump_hex_dump(
    client: HybridAnalysisClient, report_id: str, filename: str
) -> None:
    _emit_text(client.report.memory_dump_hex_dump(report_id, filename))


@report.command("sample")
@click.argument("report_id")
@_out_option
@click.pass_obj
def report_sample(client: HybridAnalysisClient, report_id: str, out: str | None) -> None:
    _emit_bytes(client.report.sample(report_id), out)


@report.command("pcap")
@click.argument("report_id")
@_out_option
@click.pass_obj
def report_pcap(client: HybridAnalysisClient, report_id: str, out: str | None) -> None:
    _emit_bytes(client.report.pcap(report_id), out)


@report.command("certificate")
@click.argument("report_id")
@_out_option
@click.pass_obj
def report_certificate(client: HybridAnalysisClient, report_id: str, out: str | None) -> None:
    _emit_bytes(client.report.certificate(report_id), out)


@report.command("dropped-file")
@click.argument("report_id")
@click.argument("file_hash")
@_out_option
@click.pass_obj
def report_dropped_file(
    client: HybridAnalysisClient, report_id: str, file_hash: str, out: str | None
) -> None:
    _emit_bytes(client.report.dropped_file(report_id, file_hash), out)


@report.command("dropped-file-raw")
@click.argument("report_id")
@click.argument("file_hash")
@_out_option
@click.pass_obj
def report_dropped_file_raw(
    client: HybridAnalysisClient, report_id: str, file_hash: str, out: str | None
) -> None:
    _emit_bytes(client.report.dropped_file_raw(report_id, file_hash), out)


@report.command("dropped-files")
@click.argument("report_id")
@_out_option
@click.pass_obj
def report_dropped_files(client: HybridAnalysisClient, report_id: str, out: str | None) -> None:
    _emit_bytes(client.report.dropped_files(report_id), out)


# --- file-collection ------------------------------------------------------
@cli.group("file-collection")
def file_collection() -> None:
    """File collection endpoints."""


@file_collection.command("create")
@click.argument("fields", nargs=-1)
@_format_option
@click.pass_obj
def file_collection_create(client: HybridAnalysisClient, fields: tuple[str, ...], fmt: str) -> None:
    _emit(client.file_collection.create(**_parse_fields(fields)), fmt)


@file_collection.command("search")
@click.argument("fields", nargs=-1)
@_format_option
@click.pass_obj
def file_collection_search(client: HybridAnalysisClient, fields: tuple[str, ...], fmt: str) -> None:
    _emit(client.file_collection.search(**_parse_fields(fields)), fmt)


@file_collection.command("get")
@click.argument("collection_id")
@_format_option
@click.pass_obj
def file_collection_get(client: HybridAnalysisClient, collection_id: str, fmt: str) -> None:
    _emit(client.file_collection.get(collection_id), fmt)


@file_collection.command("delete")
@click.argument("collection_id")
@_format_option
@click.pass_obj
def file_collection_delete(client: HybridAnalysisClient, collection_id: str, fmt: str) -> None:
    _emit(client.file_collection.delete(collection_id), fmt)


@file_collection.command("add-file")
@click.argument("collection_id")
@click.argument("file_path", type=click.Path(exists=True, dir_okay=False))
@click.argument("fields", nargs=-1)
@_format_option
@click.pass_obj
def file_collection_add_file(
    client: HybridAnalysisClient,
    collection_id: str,
    file_path: str,
    fields: tuple[str, ...],
    fmt: str,
) -> None:
    _emit(client.file_collection.add_file(collection_id, file_path, **_parse_fields(fields)), fmt)


@file_collection.command("remove-file")
@click.argument("collection_id")
@click.argument("file_hash")
@_format_option
@click.pass_obj
def file_collection_remove_file(
    client: HybridAnalysisClient, collection_id: str, file_hash: str, fmt: str
) -> None:
    _emit(client.file_collection.remove_file(collection_id, file_hash), fmt)


@file_collection.command("download")
@click.argument("collection_id")
@_out_option
@click.pass_obj
def file_collection_download(
    client: HybridAnalysisClient, collection_id: str, out: str | None
) -> None:
    _emit_bytes(client.file_collection.download(collection_id), out)


@file_collection.command("download-selected")
@click.argument("collection_id")
@click.argument("hashes", nargs=-1, required=True)
@_out_option
@click.pass_obj
def file_collection_download_selected(
    client: HybridAnalysisClient, collection_id: str, hashes: tuple[str, ...], out: str | None
) -> None:
    _emit_bytes(client.file_collection.download_selected(collection_id, list(hashes)), out)


def main() -> None:
    cli()
