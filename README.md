# Science Skills

> Open-source agent skills for scientific database workflows, with China-network awareness, Chinese query normalization helpers, and local diagnostics.

**Language**: English (this page) | [简体中文](README.zh-CN.md)

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](CHANGELOG.md)
[![Editions](https://img.shields.io/badge/editions-Free%20%7C%20Pro%20%7C%20Enterprise-orange.svg)](docs/editions-comparison.md)

Science Skills is an open-source bundle of agent "skills" that an AI coding or research agent (Claude Code, Codex, Cursor, etc.) can load to query major scientific databases — PubMed and RCSB PDB in this Free edition — in a more reliable, China-network-friendly way.

It does **not** replace the upstream databases. It provides local agent instructions, scripts, network profiles, diagnostics, and metadata so the agent makes safer, more consistent, attribution-preserving calls.

This Free edition is the open-source baseline. Commercial **Pro** and **Enterprise** editions extend it with more domains, more profiles, and dedicated support — see [docs/editions-comparison.md](docs/editions-comparison.md).

---

## Table of Contents

1. [What's in the Free edition](#whats-in-the-free-edition)
2. [Installation](#installation)
3. [Quick start](#quick-start)
4. [Network profiles](#network-profiles)
5. [Optional proxy](#optional-proxy)
6. [Science Doctor](#science-doctor)
7. [Editions: Free vs Pro vs Enterprise](#editions-free-vs-pro-vs-enterprise)
8. [Agent compatibility](#agent-compatibility)
9. [Database terms of use](#database-terms-of-use)
10. [Attribution](#attribution)
11. [Contributing](#contributing)
12. [License](#license)
13. [Disclaimer](#disclaimer)

---

## What's in the Free edition

| Component | Items |
|---|---|
| Skills | `pubmed_database`, `pdb_database`, `science_skills_common` (shared HTTP client) |
| Network profiles | `china` (**built-in default**, China-optimized mirrors for selected downloads), `base` (official sources only; opt-in via env var) |
| Adapters | Codex, Claude Code, Cursor |
| Tools | `science_doctor.py` (local diagnostic), `release_check.py` (repo sanity check) |
| Chinese query normalizers | PubMed, PDB |

The Free edition is intentionally compact. The commercial Pro edition adds UniProt, AlphaFold, ChEMBL, PubChem, OpenAlex / EuropePMC, ClinVar, dbSNP, Ensembl, ClinicalTrials, etc. See [editions-comparison.md](docs/editions-comparison.md).

---

## Installation

1. Copy this directory into your AI agent's skills / plugin location:
   - **Claude Code (CLI plugin)**: place under your `~/.claude/plugins/` (or equivalent on Windows: `%USERPROFILE%\.claude\plugins\`).
   - **Codex / Cursor**: see your client's documentation for the local skills path.
2. Restart your AI terminal so it picks up the new skills.

That's it. The default network profile is `china`, so users on the Chinese mainland get sensible defaults without further configuration.

If anything looks off, run the local diagnostic:

```powershell
python tools/science_doctor.py
```

Use `python`, `py`, or `python3` per your local Python install. Windows PowerShell is the primary supported shell; macOS / Linux / Git Bash are also supported.

For step-by-step setup, see [docs/install-guide.md](docs/install-guide.md).

---

## Quick start

Preview how a Chinese question becomes a PubMed query — without sending any network request:

```powershell
python skills/pubmed_database/scripts/pubmed_api.py normalize --query "<your Chinese biomedical question>"
```

Preview a PDB structure lookup:

```powershell
python skills/pdb_database/scripts/pdb_query_normalizer.py --query "<your Chinese structural-biology question>"
```

When a workflow calls a third-party database, keep returned identifiers (PMID, DOI, PDB ID, etc.) intact in downstream notes — they are how upstream citations and attribution are preserved.

---

## Network profiles

Science Skills separates API access from file-download mirrors. Profiles select which mirrors and which client behavior to use.

| Profile | What it does |
|---|---|
| `china` (**built-in default**) | China-optimized: official sources for API queries, configured mirrors for selected large downloads (e.g. PDB coordinate files via PDBJ). Also tightens proxy diagnostics. Users on the Chinese mainland don't need to configure anything. |
| `base` | Official sources only — no mirror overrides. Suitable for global environments. Opt in by setting `SCIENCE_NETWORK_PROFILE=base`. |

To override, set an environment variable. PowerShell:

```powershell
$env:SCIENCE_NETWORK_PROFILE = "base"
```

macOS / Linux / Git Bash:

```bash
export SCIENCE_NETWORK_PROFILE="base"
```

A third profile, `enterprise` (private mirrors, internal endpoints), exists only in the commercial Enterprise edition.

---

## Optional proxy

Proxy configuration is optional. The shared HTTP client looks at `SCIENCE_PROXY` first, then `HTTPS_PROXY`, then `HTTP_PROXY`.

PowerShell:

```powershell
$env:SCIENCE_PROXY = "http://127.0.0.1:7890"
```

macOS / Linux / Git Bash:

```bash
export SCIENCE_PROXY="http://127.0.0.1:7890"
```

Do not paste private proxy credentials into chats, documents, or logs. Science Doctor only reports whether a proxy variable is set — it never prints the value.

---

## Science Doctor

A local diagnostic that reports Python / `uv` versions, the active network profile, package status, presence of `.env`, proxy configuration status, temp-lock-file accessibility, and (optionally) PubMed / PDB connectivity probes.

Local only:

```powershell
python tools/science_doctor.py --no-network
```

Full diagnostic with network probes:

```powershell
python tools/science_doctor.py
```

It does not read the contents of `.env` and does not print secrets.

---

## Editions: Free vs Pro vs Enterprise

| Dimension | **Free** (open source, this repo) | **Pro** (commercial) | **Enterprise** (commercial) |
|---|---|---|---|
| License | Apache-2.0 | Commercial EULA | Commercial contract |
| Audience | Students, individual researchers, evaluation | Independent researchers, small labs | Universities, R&D departments, institutions |
| Skills coverage | PubMed, PDB + shared common | + UniProt, AlphaFold, ChEMBL, PubChem, OpenAlex, EuropePMC, ClinVar, dbSNP, Ensembl, ClinicalTrials | All Pro skills + the broadest commercial set |
| Chinese query normalizers | PubMed, PDB | Full coverage across commercial skills | Same as Pro + custom term mappings |
| Network profiles | `china` (default), `base` | `china` (default), `base` | `china` (default), `base`, `enterprise` (private mirrors / internal endpoints) |
| Agent adapters | Codex, Claude Code, Cursor | Codex, Claude Code, Cursor | + Dify, LangGraph |
| Science Doctor | Yes | Yes | Yes (with enterprise extensions) |
| Support | Community best-effort (issues / discussions) | Email, ~72 h response | Dedicated channel, ~24 h response |
| Updates | Open-source releases | 12 months of updates per purchase | Continuous within contract |
| Customer package ID | None | Per-licensee | Per-institution, with sub-account management |

Full bilingual comparison: [docs/editions-comparison.md](docs/editions-comparison.md).

To inquire about Pro or Enterprise, see the *Commercial editions* section in [editions-comparison.md](docs/editions-comparison.md).

---

## Agent compatibility

The Free edition includes adapter declarations for:

- **Codex** — see `adapters/codex/`
- **Claude Code** — see `adapters/claude-code/`
- **Cursor** — see `adapters/cursor/`

Each adapter directory contains the agent-specific manifest. The skills themselves are agent-neutral Markdown + Python.

---

## Database terms of use

Science Skills is an automation aid; it does not own or sublicense any third-party database content. You are responsible for following each data source's terms, rate limits, account policies, citation requirements, and commercial-use restrictions.

Highlights:

| Source | Anonymous rate limit | Notes |
|---|---|---|
| NCBI / PubMed | 3 req/s | Use `NCBI_API_KEY` for 10 req/s; max 3 concurrent connections per key. |
| RCSB PDB | No legal limit (CC0) | Cite PDB IDs in publications per community norms. |

Full per-source matrix: [docs/inventory/data-source-license-matrix.md](docs/inventory/data-source-license-matrix.md).

Do **not** use this package to bypass third-party rate limits or licensing terms.

---

## Attribution

This project is derived from [google-deepmind/science-skills](https://github.com/google-deepmind/science-skills).

- **Code** components derived from the upstream project are governed by the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0).
- **Prompt / instruction text** components derived from the upstream project are governed by [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/).

See `NOTICE` for the complete attribution statement and the list of modifications relative to the upstream project.

**This is not an official Google product.** Google LLC is not responsible for this distribution, its quality, its support, or its downstream use.

---

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) for the development workflow, code style, and review expectations. Security reports: see [SECURITY.md](SECURITY.md).

If you find this project useful, a GitHub star helps others discover it.

---

## License

[Apache License 2.0](LICENSE). Copyright 2026 Jinxiao Wang.

The Apache-2.0 license applies to this open-source Free edition. The Pro and Enterprise editions are separately licensed under a commercial EULA and are distributed outside this repository.

---

## Disclaimer

Science Skills is provided "AS IS", without warranty of any kind. The authors are not responsible for any direct or indirect damages arising from the use of this software, including but not limited to loss of research data, third-party database account suspension, or business interruption. You assume all risks associated with use.
