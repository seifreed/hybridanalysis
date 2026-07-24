"""Tests for the JSON/TOON/SARIF output formatters."""

from __future__ import annotations

import json

from toon_format import decode

from hybridanalysis.formats import to_json, to_sarif, to_toon

_REPORT = {
    "sha256": "abc123",
    "verdict": "malicious",
    "signatures": [
        {
            "name": "Drops files",
            "category": "Anti-Detection",
            "threat_level": 2,
            "description": "Drops executable files",
        },
        {"name": "Reads config", "threat_level": 1},
        {"name": "Benign", "threat_level": 0},
        "not-a-dict",
    ],
}


def test_to_json_round_trips() -> None:
    assert json.loads(to_json({"a": 1, "b": [1, 2]})) == {"a": 1, "b": [1, 2]}


def test_to_toon_is_lossless() -> None:
    data = {"name": "x", "rows": [{"a": 1, "b": 2}, {"a": 3, "b": 4}]}
    assert decode(to_toon(data)) == data


def test_to_sarif_maps_verdict_and_signatures() -> None:
    doc = json.loads(to_sarif(_REPORT))
    assert doc["version"] == "2.1.0"
    run = doc["runs"][0]
    assert run["tool"]["driver"]["name"] == "hybridanalysis"
    results = run["results"]
    levels = [r["level"] for r in results]
    assert "error" in levels  # verdict=malicious and threat_level=2
    assert "warning" in levels  # threat_level=1
    assert "note" in levels  # threat_level=0
    # source falls back to the record's sha256 as the artifact location
    assert results[0]["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "abc123"
    rule_ids = {rule["id"] for rule in run["tool"]["driver"]["rules"]}
    assert "verdict" in rule_ids
    assert "Anti-Detection" in rule_ids


def test_to_sarif_explicit_source_overrides() -> None:
    doc = json.loads(to_sarif({"verdict": "suspicious"}, source="rules/x"))
    result = doc["runs"][0]["results"][0]
    assert result["level"] == "warning"
    assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "rules/x"


def test_to_sarif_from_result_list() -> None:
    doc = json.loads(to_sarif({"count": 1, "result": [{"verdict": "no verdict"}]}))
    assert doc["runs"][0]["results"][0]["level"] == "note"


def test_to_sarif_from_top_level_list() -> None:
    doc = json.loads(to_sarif([{"verdict": "malicious"}, "skip-me"]))
    assert doc["runs"][0]["results"][0]["level"] == "error"


def test_to_sarif_empty_findings_is_valid() -> None:
    doc = json.loads(to_sarif({"api": "2.37.0"}))
    assert doc["version"] == "2.1.0"
    assert doc["runs"][0]["results"] == []


def test_to_sarif_ignores_non_record_input() -> None:
    doc = json.loads(to_sarif("just a string"))
    assert doc["runs"][0]["results"] == []
