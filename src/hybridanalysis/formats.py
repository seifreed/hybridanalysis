"""Output formatters: JSON, TOON, and SARIF 2.1.0.

These pure functions turn a Hybrid Analysis response (an arbitrary ``dict``/list)
into a string in the requested format, and are reused by the CLI.
"""

from __future__ import annotations

import json
from typing import Any

_SARIF_SCHEMA = "https://json.schemastore.org/sarif-2.1.0.json"
_VERDICT_LEVEL = {"malicious": "error", "suspicious": "warning"}
_THREAT_LEVEL = {2: "error", 1: "warning", 0: "note"}


def to_json(data: Any) -> str:
    """Serialize a response as indented JSON."""
    return json.dumps(data, indent=2)


def to_toon(data: Any) -> str:
    """Serialize a response as TOON (token-efficient JSON alternative).

    TOON support lives in the optional ``toon`` extra: ``pip install
    'hybridanalysis[toon]'``. Without it this raises ``ModuleNotFoundError``.
    """
    from toon_format import encode

    return encode(data)


def _records(data: Any) -> list[dict[str, Any]]:
    """Yield the analysis records inside a response (dict, list, or ``{result: [...]}``)."""
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        result = data.get("result")
        if isinstance(result, list):
            return [item for item in result if isinstance(item, dict)]
        return [data]
    return []


def _result(rule_id: str, message: str, level: str, source: str | None) -> dict[str, Any]:
    entry: dict[str, Any] = {"ruleId": rule_id, "level": level, "message": {"text": message}}
    if source:
        entry["locations"] = [{"physicalLocation": {"artifactLocation": {"uri": source}}}]
    return entry


def _record_results(
    record: dict[str, Any], source: str | None, rules: dict[str, dict[str, str]]
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    location = source or record.get("sha256") or record.get("submit_name")
    verdict = record.get("verdict")
    if verdict is not None:
        rules.setdefault("verdict", {"id": "verdict", "name": "verdict"})
        level = _VERDICT_LEVEL.get(str(verdict).lower(), "note")
        results.append(_result("verdict", f"Verdict: {verdict}", level, location))
    signatures = record.get("signatures")
    if isinstance(signatures, list):
        for sig in signatures:
            if not isinstance(sig, dict):
                continue
            name = str(sig.get("name") or "signature")
            rule_id = str(sig.get("category") or name)
            rules.setdefault(rule_id, {"id": rule_id, "name": rule_id})
            threat_level = sig.get("threat_level")
            level = (
                _THREAT_LEVEL.get(threat_level, "note") if isinstance(threat_level, int) else "note"
            )
            results.append(_result(rule_id, str(sig.get("description") or name), level, location))
    return results


def to_sarif(data: Any, *, source: str | None = None) -> str:
    """Map a Hybrid Analysis analysis response to a SARIF 2.1.0 document.

    ``verdict`` becomes a summary result and each entry in ``signatures`` becomes a
    result, with SARIF levels derived from the verdict / threat level. A response
    with no findings yields a valid SARIF document with an empty ``results`` list.
    """
    rules: dict[str, dict[str, str]] = {}
    results: list[dict[str, Any]] = []
    for record in _records(data):
        results.extend(_record_results(record, source, rules))
    document = {
        "version": "2.1.0",
        "$schema": _SARIF_SCHEMA,
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "hybridanalysis",
                        "informationUri": "https://hybrid-analysis.com",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
            }
        ],
    }
    return json.dumps(document, indent=2)
