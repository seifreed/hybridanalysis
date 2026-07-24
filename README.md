<p align="center">
  <img src="https://img.shields.io/badge/hybridanalysis-Falcon%20Sandbox%20API%20v2-blue?style=for-the-badge" alt="hybridanalysis">
</p>

<h1 align="center">hybridanalysis</h1>

<p align="center">
  <strong>Python library and CLI for the Hybrid Analysis (Falcon Sandbox) API v2</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.14%2B-blue?style=flat-square&logo=python&logoColor=white" alt="Python Versions">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
  <img src="https://img.shields.io/badge/coverage-100%25-brightgreen?style=flat-square" alt="Coverage">
  <img src="https://img.shields.io/badge/typed-mypy%20strict-blue?style=flat-square" alt="Typed">
  <img src="https://img.shields.io/badge/async-httpx-purple?style=flat-square" alt="Async">
</p>

<p align="center">
  <a href="https://github.com/seifreed/hybridanalysis/stargazers"><img src="https://img.shields.io/github/stars/seifreed/hybridanalysis?style=flat-square" alt="GitHub Stars"></a>
  <a href="https://github.com/seifreed/hybridanalysis/issues"><img src="https://img.shields.io/github/issues/seifreed/hybridanalysis?style=flat-square" alt="GitHub Issues"></a>
  <a href="https://buymeacoffee.com/seifreed"><img src="https://img.shields.io/badge/Buy%20Me%20a%20Coffee-support-yellow?style=flat-square&logo=buy-me-a-coffee&logoColor=white" alt="Buy Me a Coffee"></a>
</p>

---

## Overview

**hybridanalysis** is a Python toolkit to submit samples to and query the
[Hybrid Analysis](https://hybrid-analysis.com) (Falcon Sandbox) service through its
[API v2](https://hybrid-analysis.com/docs/api/v2). It ships both a **synchronous** and
an **asynchronous** client with identical surfaces, a full-featured **CLI**, and a typed
exception hierarchy — covering every current (non-deprecated) endpoint across all ten
API tags.

### Key Features

| Feature | Description |
|---------|-------------|
| **Full API coverage** | Every current v2 endpoint across `feed`, `key`, `overview`, `quick-scan`, `submit`, `report`, `search`, `file-collection`, `abuse-reports`, `system` |
| **Sync + Async** | `HybridAnalysisClient` (httpx) and `AsyncHybridAnalysisClient` (httpx async) with the same methods |
| **CLI + Library** | Use as the `hybridanalysis` command-line tool or as a Python package |
| **Rich search** | Query by domain, host/IP, URL, malware family, tag, MITRE ATT&CK technique, hash-similarity and more |
| **File submission** | Full sandbox and quick-scan multipart uploads |
| **Multiple output formats** | JSON, token-efficient TOON, and SARIF 2.1.0 for analysis results (`--format`) |
| **Flexible config** | Environment variables or a local TOML file |

### Supported Surface

```text
Clients      HybridAnalysisClient (sync), AsyncHybridAnalysisClient (async)
Tags         feed · key · overview · quick-scan · submit · report
             search · file-collection · abuse-reports · system
Downloads    sample, pcap, certificate, dropped files, memory strings (bytes/text)
Config       HYBRIDANALYSIS env var · ~/.config/hybridanalysis/config.toml
Errors       AuthenticationError · NotFoundError · RateLimitError · APIError
             NetworkError · ConfigError (all subclass HybridAnalysisError)
```

---

## Installation

### From PyPI

```bash
pip install hybridanalysis            # core
pip install 'hybridanalysis[toon]'    # + TOON output (`--format toon`)
```

### From Source

```bash
git clone https://github.com/seifreed/hybridanalysis.git
cd hybridanalysis
python3.14 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt  # runtime + dev tooling; use `pip install -e .` for runtime only
```

> Requires **Python 3.14+**. Runtime dependencies are `httpx` and `click`; `--format toon` needs the optional `toon` extra (`toon-format`).

---

## Configuration

The API key is resolved from, in order:

1. The `HYBRIDANALYSIS` environment variable.
2. A local TOML file — `./.hybridanalysis.toml` or `~/.config/hybridanalysis/config.toml`:

   ```toml
   [hybridanalysis]
   api_key = "your-api-key"
   # base_url   = "https://hybrid-analysis.com/api/v2"  # optional
   # user_agent = "Falcon Sandbox"                      # optional
   # timeout    = 60                                    # optional, seconds
   ```

Every field also has an environment variable that takes precedence over the file:
`HYBRIDANALYSIS_URL`, `HYBRIDANALYSIS_USER_AGENT`, and `HYBRIDANALYSIS_TIMEOUT`.

---

## Quick Start

```bash
export HYBRIDANALYSIS="your-api-key"

# System / key info
hybridanalysis system version
hybridanalysis key current

# Submit a sample and poll its report
hybridanalysis submit file sample.exe environment_id=160
hybridanalysis report summary <job-id>
```

---

## Usage

### Command Line Interface

```bash
# Look up a hash (any format -> SHA256) and its reports
hybridanalysis search hash <md5|sha1|sha256>

# Search by behaviour / infrastructure
hybridanalysis search terms host=8.8.8.8
hybridanalysis search terms vx_family=nemucod verdict=5
hybridanalysis search terms uses_technique=T1055

# Submit for analysis
hybridanalysis submit file sample.exe environment_id=160
hybridanalysis quick-scan file sample.exe --scan-type all

# Download binary artifacts (to a file, or stdout when --out is omitted)
hybridanalysis report pcap <job-id> --out capture.pcap
hybridanalysis overview sample <sha256> --out sample.gz
```

`--api-key`, `--base-url`, and `--config` override the resolved configuration.
`python -m hybridanalysis` works as an alternative to the `hybridanalysis` command.

### Output Formats

Every JSON-returning command accepts `-f` / `--format`:

```bash
hybridanalysis overview get <sha256> --format toon    # token-efficient JSON
hybridanalysis report summary <job-id> --format sarif # SARIF 2.1.0 findings
```

| Format | Available on | Description |
|--------|--------------|-------------|
| `json` | all commands (default) | Indented JSON. |
| `toon` | all commands | [TOON](https://github.com/toon-format/toon) — a compact, lossless JSON encoding that uses fewer tokens. Needs the `toon` extra: `pip install 'hybridanalysis[toon]'`. |
| `sarif` | analysis commands (`feed`, `overview`, `search`, `quick-scan`, `report`) | SARIF 2.1.0: the `verdict` and each `signatures[]` entry become results, with levels derived from the verdict / threat level. The artifact location is taken from the command's SHA256 / report-id argument. |

### Command Groups

| Command | Description |
|---------|-------------|
| `hybridanalysis system` | Instance version, environments, action scripts, stats, config, queue |
| `hybridanalysis key` | API key info and submission quota |
| `hybridanalysis feed` | Recent detonation and quick-scan feeds |
| `hybridanalysis overview` | Aggregated report for a SHA256 (+ sample download) |
| `hybridanalysis search` | Hash lookup and multi-field term search |
| `hybridanalysis quick-scan` | Quick scans of files/URLs and result retrieval |
| `hybridanalysis submit` | Sandbox submission of files, URLs and dropped files |
| `hybridanalysis report` | Report state/summary and artifact downloads |
| `hybridanalysis file-collection` | Create, search, and manage file collections |
| `hybridanalysis abuse-reports` | Request report deletion; removed-hash feed |

---

## Python Library

### Synchronous

```python
from hybridanalysis import HybridAnalysisClient

with HybridAnalysisClient.from_env() as client:
    print(client.system.version())

    # Submit a file and poll its report
    submitted = client.submit.file("sample.exe", environment_id="160")
    job_id = submitted["job_id"]
    print(client.report.state(job_id))
    print(client.report.summary(job_id))

    # Download binary artifacts (returned as bytes)
    pcap = client.report.pcap(job_id)

    # Search (verdict is numeric 1-5, 5 = malicious)
    client.search.terms(filetype="peexe", verdict="5")
```

### Asynchronous

```python
import asyncio
from hybridanalysis import AsyncHybridAnalysisClient

async def main():
    async with AsyncHybridAnalysisClient.from_env() as client:
        print(await client.system.version())
        results = await asyncio.gather(*(client.overview.get(h) for h in hashes))

asyncio.run(main())
```

Errors raise subclasses of `HybridAnalysisError`: `AuthenticationError`,
`NotFoundError`, `RateLimitError`, `APIError`, `NetworkError`, and `ConfigError`.

---

## Requirements

- Python 3.14+
- See [pyproject.toml](pyproject.toml) for dependencies and extras

---

## Support the Project

If this project is useful in your workflows, you can support development:

<a href="https://buymeacoffee.com/seifreed" target="_blank">
  <img src="https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png" alt="Buy Me A Coffee" height="50">
</a>

---

## License

This project is licensed under the MIT license. See [LICENSE](LICENSE).

**Attribution**
- Author: **Marc Rivero López** | [@seifreed](https://github.com/seifreed)
- Repository: [github.com/seifreed/hybridanalysis](https://github.com/seifreed/hybridanalysis)

---

<p align="center">
  <sub>Built for practical malware analysis and security automation</sub>
</p>
