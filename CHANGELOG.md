# Changelog

All notable changes to this open-source Free edition of Science Skills are
documented here. This changelog covers the open-source release line only;
the commercial Pro / Enterprise editions track their own versions.

## 0.1.0 - 2026-05-28

Initial open-source release. Derived from the internal Science Skills
commercial codebase; all customer-specific identifiers and commercial-only
material have been removed.

### Included

- Skills: `pubmed_database`, `pdb_database`, `science_skills_common`.
- Chinese query normalizers for PubMed and PDB.
- Network profiles: `default` (official sources first) and `china`
  (China-optimized for selected downloads, e.g. PDB mmCIF via PDBJ).
- Agent adapter declarations for Codex, Claude Code, and Cursor.
- Tools: `science_doctor.py` (local diagnostic), `release_check.py`
  (repository sanity check).
- Documentation: bilingual README, install guide, troubleshooting guide,
  editions comparison, data-source license matrix, network-risk matrix,
  skills inventory.

### Licensing

- Apache License 2.0 for this distribution.
- Upstream attribution preserved for the
  [google-deepmind/science-skills](https://github.com/google-deepmind/science-skills)
  project (Apache-2.0 code components, CC-BY-4.0 prompt/text components).
  See `NOTICE`.

### Not included (commercial editions only)

- Pro / Enterprise skills (UniProt, AlphaFold, ChEMBL, PubChem, OpenAlex,
  EuropePMC, ClinVar, dbSNP, Ensembl, ClinicalTrials, etc.).
- The `enterprise` network profile.
- Dify / LangGraph adapters.
- Customer package IDs and embedded license tokens.
