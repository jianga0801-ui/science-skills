"""Release / repository sanity checks for the open-source Science Skills package.

Validates:
  - All bundled JSON files parse cleanly.
  - Every skill directory has a matching metadata.json and its declared
    scripts exist.
  - Each metadata.json's has_chinese_normalizer flag matches what's on disk.
  - Every network profile listed in the manifest is present.
  - Every adapter listed in the manifest is present.
  - Required top-level documentation files are present.

Exits non-zero if any check fails. Does not perform network I/O.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from typing import Any


REQUIRED_DOCS = (
    "README.md",
    "README.zh-CN.md",
    "NOTICE",
    "LICENSE",
    "CHANGELOG.md",
    "docs/install-guide.md",
    "docs/troubleshooting.md",
    "docs/editions-comparison.md",
    "docs/inventory/data-source-license-matrix.md",
    "docs/inventory/network-risk-matrix.md",
    "docs/inventory/skills-inventory.md",
)
REQUIRED_SKILL_METADATA_FIELDS = (
    "schema_version",
    "package_id",
    "skill.directory",
    "skill.name",
    "skill.description",
    "skill.path",
    "implementation.scripts",
    "implementation.has_chinese_normalizer",
    "network.requires_network",
    "compliance.upstream.name",
    "compliance.upstream.repository",
    "compliance.upstream.license",
)


def _rel(path: pathlib.Path, root: pathlib.Path) -> str:
  return path.relative_to(root).as_posix()


def _get_nested(data: dict[str, Any], dotted: str) -> Any:
  value: Any = data
  for part in dotted.split("."):
    if not isinstance(value, dict) or part not in value:
      raise KeyError(dotted)
    value = value[part]
  return value


def _load_json(path: pathlib.Path) -> Any:
  return json.loads(path.read_text(encoding="utf-8"))


def _has_normalizer_script(skill_dir: pathlib.Path) -> bool:
  return any((skill_dir / "scripts").glob("*query_normalizer.py"))


def _add_failure(report: dict[str, Any], check: str, message: str) -> None:
  report["failures"].append({"check": check, "message": message})


def _add_check(report: dict[str, Any], check: str, status: str) -> None:
  report["checks"].append({"check": check, "status": status})


def _json_paths(root: pathlib.Path) -> list[pathlib.Path]:
  paths: list[pathlib.Path] = []
  for pattern in (
      "plugin.json",
      "installed_version.json",
      "metadata.json",
      "config/**/*.json",
      "skills/**/metadata.json",
      "adapters/**/adapter.json",
  ):
    paths.extend(root.glob(pattern))
  return sorted(set(paths))


def _skill_dirs(root: pathlib.Path) -> list[pathlib.Path]:
  return sorted(path.parent for path in (root / "skills").glob("*/SKILL.md"))


def _check_json_parse(root: pathlib.Path, report: dict[str, Any]) -> None:
  for path in _json_paths(root):
    try:
      _load_json(path)
    except json.JSONDecodeError as exc:
      _add_failure(report, "json_parse", f"{_rel(path, root)} is invalid JSON: {exc}")
  _add_check(report, "json_parse", "checked")


def _check_skill_metadata(root: pathlib.Path, report: dict[str, Any]) -> None:
  skill_dirs = _skill_dirs(root)
  for skill_dir in skill_dirs:
    metadata_path = skill_dir / "metadata.json"
    if not metadata_path.is_file():
      _add_failure(report, "skill_metadata", f"{_rel(skill_dir, root)} missing metadata.json")
      continue
    data = _load_json(metadata_path)
    for field in REQUIRED_SKILL_METADATA_FIELDS:
      try:
        _get_nested(data, field)
      except KeyError:
        _add_failure(
            report,
            "skill_metadata",
            f"{_rel(metadata_path, root)} missing required field {field}",
        )

    rel_skill_dir = _rel(skill_dir, root)
    if data.get("skill", {}).get("directory") != skill_dir.name:
      _add_failure(
          report,
          "skill_metadata",
          f"{_rel(metadata_path, root)} skill.directory does not match",
      )
    if data.get("skill", {}).get("path") != rel_skill_dir:
      _add_failure(
          report,
          "skill_metadata",
          f"{_rel(metadata_path, root)} skill.path must equal {rel_skill_dir}",
      )
    scripts = data.get("implementation", {}).get("scripts", [])
    for script in scripts:
      if not (root / script).exists():
        _add_failure(
            report,
            "skill_metadata",
            f"{_rel(metadata_path, root)} references missing script {script}",
        )
    flag = data.get("implementation", {}).get("has_chinese_normalizer")
    actual = _has_normalizer_script(skill_dir)
    if flag != actual:
      _add_failure(
          report,
          "skill_metadata",
          f"{_rel(metadata_path, root)} has_chinese_normalizer={flag} but actual={actual}",
      )
  _add_check(report, "skill_metadata", "checked")


def _check_manifest(root: pathlib.Path, report: dict[str, Any]) -> None:
  manifest_path = root / "config" / "package_manifest.json"
  if not manifest_path.is_file():
    _add_failure(report, "manifest", "config/package_manifest.json is missing")
    return
  manifest = _load_json(manifest_path)

  available_skills = {p.name for p in _skill_dirs(root)}
  profile_dir = root / "config" / "network_profiles"
  available_profiles = {
      p.stem
      for p in profile_dir.glob("*.json")
      if not p.stem.endswith(".overlay")
  }
  available_adapters = {
      p.parent.name for p in (root / "adapters").glob("*/adapter.json")
  }

  for edition_name, edition in manifest.get("editions", {}).items():
    skills = set(edition.get("included_skills", []))
    unknown = skills - available_skills
    if unknown and skills != {"all"}:
      _add_failure(
          report,
          "manifest",
          f"edition {edition_name} references unknown skills {sorted(unknown)}",
      )
    profiles = set(edition.get("network_profiles", []))
    if not profiles.issubset(available_profiles):
      _add_failure(
          report,
          "manifest",
          f"edition {edition_name} references unknown profiles "
          f"{sorted(profiles - available_profiles)}",
      )
    adapters = set(edition.get("adapters", []))
    if not adapters.issubset(available_adapters):
      _add_failure(
          report,
          "manifest",
          f"edition {edition_name} references unknown adapters "
          f"{sorted(adapters - available_adapters)}",
      )
  _add_check(report, "manifest", "checked")


def _check_docs(root: pathlib.Path, report: dict[str, Any]) -> None:
  for rel_path in REQUIRED_DOCS:
    if not (root / rel_path).is_file():
      _add_failure(report, "required_docs", f"{rel_path} is missing")
  _add_check(report, "required_docs", "checked")


def run_checks(repo_root: pathlib.Path | str | None = None) -> dict[str, Any]:
  root = pathlib.Path(repo_root or pathlib.Path.cwd()).resolve()
  report: dict[str, Any] = {"status": "ok", "checks": [], "failures": []}
  _check_json_parse(root, report)
  _check_skill_metadata(root, report)
  _check_manifest(root, report)
  _check_docs(root, report)
  if report["failures"]:
    report["status"] = "fail"
  return report


def main(argv: list[str] | None = None) -> int:
  parser = argparse.ArgumentParser(description="Run repository sanity checks.")
  parser.add_argument(
      "--root-dir",
      type=pathlib.Path,
      default=pathlib.Path.cwd(),
      help="Repository root to check.",
  )
  args = parser.parse_args(argv)
  report = run_checks(args.root_dir)
  print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
  return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
  raise SystemExit(main())
