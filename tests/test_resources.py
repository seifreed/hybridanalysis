"""Tests for every resource method, routed through the real local server."""

from __future__ import annotations

from pathlib import Path

from hybridanalysis.client import HybridAnalysisClient
from hybridanalysis.resources.base import BaseResource

from .api_server import LocalAPIServer


def _last_path(server: LocalAPIServer) -> str:
    return server.requests[-1].path


def test_seg_encodes_structural_characters() -> None:
    # Path separators / query / fragment must be encoded so an id cannot change
    # which endpoint is called; ':' stays for the 'sha256:environmentId' format.
    assert BaseResource._seg("a/b") == "a%2Fb"
    assert BaseResource._seg("x?y#z") == "x%3Fy%23z"
    assert BaseResource._seg("../key/current") == "..%2Fkey%2Fcurrent"
    assert BaseResource._seg("sha256hash:160") == "sha256hash:160"
    assert BaseResource._seg("ca1191ef") == "ca1191ef"


def test_system_endpoints(client: HybridAnalysisClient, server: LocalAPIServer) -> None:
    assert client.system.version()["path"] == "/system/version"
    assert client.system.environments()["path"] == "/system/environments"
    assert client.system.action_scripts()["path"] == "/system/action-scripts"
    assert client.system.stats()["path"] == "/system/stats"
    assert client.system.configuration()["path"] == "/system/configuration"
    assert client.system.queue_size()["path"] == "/system/queue-size"
    assert client.system.total_submissions()["path"] == "/system/total-submissions"


def test_key_endpoints(client: HybridAnalysisClient) -> None:
    assert client.key.current()["path"] == "/key/current"
    assert client.key.submission_quota()["path"] == "/key/submission-quota"


def test_feed_endpoints(client: HybridAnalysisClient) -> None:
    assert client.feed.detonation()["path"] == "/feed/detonation"
    assert client.feed.quick_scan()["path"] == "/feed/quick-scan"


def test_overview_endpoints(client: HybridAnalysisClient) -> None:
    assert client.overview.get("abc")["path"] == "/overview/abc"
    assert client.overview.summary("abc")["path"] == "/overview/abc/summary"
    assert client.overview.refresh("abc")["path"] == "/overview/abc/refresh"
    assert client.overview.sample("abc") == b"BINARY-DATA"


ALL_SEARCH_TERMS = {
    "domain": "evil.example",
    "host": "8.8.8.8",
    "url": "login",
    "port": "443",
    "filename": "invoice.exe",
    "filetype": "peexe",
    "filetype_desc": "PE32 executable",
    "verdict": "5",
    "av_detect": "50-70",
    "vx_family": "nemucod",
    "tag": "ransomware",
    "country": "DEU",
    "env_id": "160",
    "imp_hash": "f34d5f2d4577ed6d9ceec516c1f5a744",
    "ssdeep": "3:aaa:baa",
    "authentihash": "a" * 64,
    "similar_to": "abc",
    "context": "abc",
    "uses_tactic": "TA0002",
    "uses_technique": "T1055",
    "date_from": "2024-01-01 00:00",
    "date_to": "2024-12-31 23:59",
}


def test_search_endpoints(client: HybridAnalysisClient) -> None:
    result = client.search.hash("deadbeef")
    assert result["path"] == "/search/hash"
    assert result["query"] == {"hash": ["deadbeef"]}
    terms = client.search.terms(filetype="peexe", verdict="5")
    assert terms["form"] == {"filetype": ["peexe"], "verdict": ["5"]}


def test_search_terms_sends_all_documented_fields(
    client: HybridAnalysisClient, server: LocalAPIServer
) -> None:
    client.search.terms(**ALL_SEARCH_TERMS)
    request = server.requests[-1]
    assert request.method == "POST"
    assert request.path == "/search/terms"
    for field, value in ALL_SEARCH_TERMS.items():
        assert request.form[field] == [value]


def test_abuse_reports_endpoints(client: HybridAnalysisClient) -> None:
    created = client.abuse_reports.new("abc", "mistake")
    assert created["path"] == "/abuse-reports/new"
    assert created["form"] == {"reason": ["mistake"], "sha256": ["abc"]}
    assert client.abuse_reports.feed()["path"] == "/abuse-reports/feed"


def test_quick_scan_endpoints(
    client: HybridAnalysisClient, server: LocalAPIServer, tmp_path: Path
) -> None:
    assert client.quick_scan.state()["path"] == "/quick-scan/state"

    sample = tmp_path / "sample.bin"
    sample.write_bytes(b"MZ...")
    client.quick_scan.file(sample, scan_type="all")
    assert _last_path(server) == "/quick-scan/file"
    assert b"scan_type" in server.requests[-1].body
    assert b"sample.bin" in server.requests[-1].body

    url_result = client.quick_scan.url("http://x.test", scan_type="all")
    assert url_result["form"] == {"url": ["http://x.test"], "scan_type": ["all"]}
    assert client.quick_scan.get("id1")["path"] == "/quick-scan/id1"
    converted = client.quick_scan.convert_to_full("id1", environment_id="100")
    assert converted["path"] == "/quick-scan/id1/convert-to-full"
    assert converted["form"] == {"environment_id": ["100"]}


def test_submit_endpoints(
    client: HybridAnalysisClient, server: LocalAPIServer, tmp_path: Path
) -> None:
    sample = tmp_path / "malware.exe"
    sample.write_bytes(b"payload")
    client.submit.file(sample, environment_id="120")
    assert _last_path(server) == "/submit/file"
    assert b"environment_id" in server.requests[-1].body

    assert client.submit.url("http://x.test", environment_id="120")["path"] == "/submit/url"
    assert client.submit.hash_for_url("http://x.test")["path"] == "/submit/hash-for-url"

    dropped = client.submit.dropped_file("job1", "abc123")
    assert dropped["path"] == "/submit/dropped-file"
    assert dropped["form"] == {"id": ["job1"], "file_hash": ["abc123"]}


def test_report_json_endpoints(client: HybridAnalysisClient) -> None:
    rid = "job1"
    assert client.report.state(rid)["path"] == f"/report/{rid}/state"
    assert client.report.summary(rid)["path"] == f"/report/{rid}/summary"
    assert client.report.json_report(rid)["path"] == f"/report/{rid}/report/json"
    assert client.report.children(rid)["path"] == f"/report/{rid}/children"
    assert client.report.screenshots(rid)["path"] == f"/report/{rid}/screenshots"
    assert client.report.memory_dumps_list(rid)["path"] == f"/report/{rid}/memory-dumps-list"
    extracted = client.report.memory_dump_extracted_strings(rid, "mem.dmp")
    assert extracted["path"] == f"/report/{rid}/memory-dump/extracted-strings"
    assert extracted["query"] == {"filename": ["mem.dmp"]}


def test_report_text_endpoints(client: HybridAnalysisClient) -> None:
    rid = "job1"
    assert "memory-strings" in client.report.memory_strings(rid)
    assert "hex-dump" in client.report.memory_dump_hex_dump(rid, "mem.dmp")


def test_report_binary_endpoints(client: HybridAnalysisClient) -> None:
    rid = "job1"
    assert client.report.sample(rid) == b"BINARY-DATA"
    assert client.report.pcap(rid) == b"BINARY-DATA"
    assert client.report.certificate(rid) == b"BINARY-DATA"
    assert client.report.dropped_file(rid, "h1") == b"BINARY-DATA"
    assert client.report.dropped_file_raw(rid, "h1") == b"BINARY-DATA"
    assert client.report.dropped_files(rid) == b"BINARY-DATA"


def test_file_collection_endpoints(
    client: HybridAnalysisClient, server: LocalAPIServer, tmp_path: Path
) -> None:
    created = client.file_collection.create(collection_name="mycol")
    assert created["path"] == "/file-collection/create"
    assert created["form"] == {"collection_name": ["mycol"]}
    assert client.file_collection.search(tag="ransomware")["path"] == "/file-collection/search"
    assert client.file_collection.get("c1")["path"] == "/file-collection/c1"

    assert client.file_collection.delete("c1") is None
    assert server.requests[-1].method == "DELETE"
    assert server.requests[-1].path == "/file-collection/c1"

    upload = tmp_path / "add.bin"
    upload.write_bytes(b"content")
    added = client.file_collection.add_file("c1", upload)
    assert added["path"] == "/file-collection/c1/files/add"
    assert b"add.bin" in server.requests[-1].body

    client.file_collection.remove_file("c1", "h1")
    assert _last_path(server) == "/file-collection/c1/files/h1"
    assert server.requests[-1].method == "DELETE"

    assert client.file_collection.download("c1") == b"BINARY-DATA"
    assert client.file_collection.download_selected("c1", ["h1", "h2"]) == b"BINARY-DATA"
    assert server.requests[-1].form["hashes[]"] == ["h1", "h2"]


def test_from_env_builds_client(server: LocalAPIServer) -> None:
    from .api_server import VALID_KEY

    env = {"HYBRIDANALYSIS": VALID_KEY, "HYBRIDANALYSIS_URL": server.base_url}
    with HybridAnalysisClient.from_env(env=env) as instance:
        assert instance.system.version()["path"] == "/system/version"
