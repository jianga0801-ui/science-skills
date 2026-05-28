# Security Policy

## Supported versions

This open-source Free edition is on the 0.x release line. Only the latest
0.x release receives security fixes.

| Version | Supported |
|---------|-----------|
| 0.1.x   | ✅        |
| < 0.1   | ❌        |

## Reporting a vulnerability

**Please do not open a public GitHub issue for security reports.**

Instead, use one of these channels:

1. GitHub's private vulnerability reporting (preferred): open the
   "Security" tab on the repository and click "Report a vulnerability".
2. Open a private GitHub Discussion (Q&A category) titled
   "Security report — please contact me" with your contact preference;
   the maintainer will reply privately.

When reporting, please include:

- A description of the issue.
- Steps to reproduce, or a proof-of-concept.
- The version (or commit hash) you tested against.
- Any known mitigation or workaround.

You can expect:

- Acknowledgement within 7 days.
- A target fix or remediation plan within 30 days for confirmed issues.
- Public credit in the changelog (unless you ask to remain anonymous).

## Out of scope

- Vulnerabilities in upstream third-party scientific databases
  (NCBI / PubMed, RCSB PDB, etc.) — report directly to the operators.
- Vulnerabilities in the commercial Pro / Enterprise editions are
  handled outside this repository; contact the commercial channel
  documented in `docs/editions-comparison.md`.
- Issues that require physical access to the user's machine without any
  remote vector.
