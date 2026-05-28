"""Local diagnostics for Science Skills.

The doctor reports environment and network readiness without reading or
printing secrets. Output is JSON by default so agents can parse it reliably.
"""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import site
import subprocess
import sys
import tempfile
import http.client
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

try:
  from science_skills.science_skills_common import http_client
except ModuleNotFoundError:
  sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
  from skills.science_skills_common import http_client


def _find_installed_uv() -> str | None:
  """Dynamically locate the uv executable on Windows and Unix platforms.

  Bypasses active process PATH cache delays by checking site.getuserbase() and
  sys.executable directories.
  """
  # 1. Check system path via shutil.which
  uv_path = shutil.which("uv")
  if uv_path:
    return uv_path

  # 2. Check site user base directories
  user_base = site.getuserbase()
  if user_base:
    user_bin = pathlib.Path(user_base) / ("Scripts" if os.name == "nt" else "bin")
    for path in (user_bin / "uv", user_bin / "uv.exe"):
      if path.exists():
        return str(path.resolve())

  # 3. Check sys.executable directory and Scripts folder
  exe_dir = pathlib.Path(sys.executable).parent
  scripts_dir = exe_dir / ("Scripts" if os.name == "nt" else "bin")
  for path in (exe_dir / "uv", exe_dir / "uv.exe", scripts_dir / "uv.exe", scripts_dir / "uv"):
    if path.exists():
      return str(path.resolve())

  return None


Probe = Callable[[str, float], None]

PUBMED_HEALTH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi?db=pubmed"
)
PDBJ_MIRROR_HEALTH_URL = (
    "https://data.pdbj.org/pub/pdb/data/structures/divided/mmCIF/cb/"
    "1cbs.cif.gz"
)
DOCTOR_USER_AGENT = "science-skills-doctor/0.1"


def _ok(**extra: Any) -> dict[str, Any]:
  return {"status": "ok", **extra}


def _warn(hint: str, **extra: Any) -> dict[str, Any]:
  return {"status": "warn", "hint": hint, **extra}


def _fail(hint: str, **extra: Any) -> dict[str, Any]:
  return {"status": "fail", "hint": hint, **extra}


def _skip(hint: str, **extra: Any) -> dict[str, Any]:
  return {"status": "skip", "hint": hint, **extra}


def _probe_url(url: str, timeout: float) -> None:
  request = urllib.request.Request(
      url, headers={"User-Agent": DOCTOR_USER_AGENT}, method="HEAD"
  )
  try:
    with urllib.request.urlopen(request, timeout=timeout):
      return
  except (urllib.error.HTTPError, http.client.RemoteDisconnected) as exc:
    if isinstance(exc, urllib.error.HTTPError) and exc.code not in (405, 501):
      raise
    get_request = urllib.request.Request(
        url,
        headers={"Range": "bytes=0-0", "User-Agent": DOCTOR_USER_AGENT},
        method="GET",
    )
    with urllib.request.urlopen(get_request, timeout=timeout):
      return


def _check_profile() -> dict[str, Any]:
  try:
    profile = http_client.load_network_profile()
  except http_client.NetworkProfileError as exc:
    return _fail(str(exc), env="SCIENCE_NETWORK_PROFILE")

  sources = sorted(profile.get("sources", {}).keys())
  return _ok(profile=profile.get("profile"), sources=sources)


def _check_temp_lock() -> dict[str, Any]:
  try:
    path = pathlib.Path(tempfile.gettempdir()) / "science-skills-doctor.lock"
    with path.open("a+", encoding="utf-8") as f:
      f.write("")
  except OSError as exc:
    return _fail(f"临时目录或锁文件不可写: {exc}")
  return _ok(temp_dir=tempfile.gettempdir())


def _check_env_file(root_dir: pathlib.Path) -> dict[str, Any]:
  env_path = root_dir / ".env"
  if env_path.exists():
    return _warn(".env 存在；诊断工具不会读取或打印其中的密钥。", present=True)
  return _ok(present=False)


def _check_proxy() -> dict[str, Any]:
  for env_name in ("SCIENCE_PROXY", "HTTP_PROXY", "HTTPS_PROXY"):
    if os.environ.get(env_name):
      return _ok(configured=True, env=env_name)
  return _ok(
      configured=False,
      env="SCIENCE_PROXY",
      hint="未检测到代理；默认 china profile 已启用，代理仅作为高级排障选项。",
  )


def _check_license(root_dir: pathlib.Path) -> dict[str, Any]:
  manifest_path = root_dir / "config" / "package_manifest.json"
  if not manifest_path.exists():
    return _warn(
        "未找到产品分包 manifest，无法确认本地授权状态。",
        manifest="config/package_manifest.json",
    )

  try:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
  except (OSError, json.JSONDecodeError) as exc:
    return _fail(
        f"产品分包 manifest 无法读取或不是合法 JSON: {exc}",
        manifest="config/package_manifest.json",
    )

  current_edition = manifest.get("current_edition")
  editions = manifest.get("editions", {})
  edition_manifest = editions.get(current_edition)
  customer_package_id = manifest.get("customer_package_id")
  license_status = manifest.get("license_status", "unknown")

  if not current_edition or not isinstance(edition_manifest, dict):
    return _fail(
        "产品分包 manifest 缺少有效的 current_edition。",
        manifest="config/package_manifest.json",
    )

  if current_edition != "free" and not customer_package_id:
    return _fail(
        "当前商业版本缺少客户专属包编号。",
        edition=current_edition,
        manifest="config/package_manifest.json",
    )

  return _ok(
      edition=current_edition,
      package_id=edition_manifest.get("package_id"),
      customer_package_id=customer_package_id,
      license_status=license_status,
      manifest="config/package_manifest.json",
      adapters=edition_manifest.get("adapters", []),
  )


def _check_remote(name: str, url: str, timeout: float, probe: Probe) -> dict[str, Any]:
  try:
    probe(url, timeout)
  except Exception as exc:
    return _fail(
        f"{name} 访问失败，可能是网络、代理或远端服务限制。请检查网络 profile "
        f"；如已有代理，可配置 SCIENCE_PROXY、HTTPS_PROXY 或 HTTP_PROXY 后重试。"
        f"错误类型: {type(exc).__name__}",
        url=url,
    )
  return _ok(url=url)


def run_checks(
    *,
    root_dir: pathlib.Path | str | None = None,
    network: bool = True,
    timeout: float = 10.0,
    probe: Probe = _probe_url,
    auto_heal: bool = False,
    auto_confirm: bool = False,
) -> dict[str, Any]:
  """Run local and optional network diagnostics.

  Args:
    root_dir: Repository root used only to check whether `.env` exists.
    network: Whether to run remote HTTP probes.
    timeout: Per-probe timeout in seconds.
    probe: Injectable network probe for tests.

  Returns:
    A JSON-serializable report. Secrets and proxy values are never included.
  """
  root = pathlib.Path(root_dir) if root_dir is not None else pathlib.Path.cwd()

  # Load the profile to get PyPI configuration
  try:
    profile = http_client.load_network_profile()
  except Exception:
    profile = {}
  pypi_config = profile.get("pypi")

  uv_path = _find_installed_uv()
  auto_installed = False
  if not uv_path:
    if not auto_heal:
      # Without auto-heal, just warn and suggest installation.
      uv_status = _warn("未检测到 uv，请运行 pip install uv 进行安装。")
    else:
      pip_cmd = [sys.executable, "-m", "pip", "install", "uv"]
      index_url = None
      if pypi_config:
        index_url = pypi_config.get("index_url")
        if index_url:
          pip_cmd.extend(["-i", index_url])
          print(f"[自愈提示] 检测到本地未安装 uv，正在通过 {index_url} 为您自动安装 uv...", file=sys.stderr)
        else:
          print("[自愈提示] 检测到本地未安装 uv，正在为您自动安装 uv...", file=sys.stderr)
      else:
        print("[自愈提示] 检测到本地未安装 uv，正在为您自动安装 uv...", file=sys.stderr)
  
      try:
        subprocess.run(
            pip_cmd,
            check=True,
            capture_output=True,
        )
        uv_path = _find_installed_uv()
        if uv_path:
          auto_installed = True
      except Exception as exc:
        warn_msg = f"[自愈警告] 自动安装 uv 失败: {exc}。"
        if index_url:
          warn_msg += f"您可稍后尝试手动执行: pip install uv -i {index_url}"
        else:
          warn_msg += "您可稍后尝试手动执行: pip install uv"
        print(warn_msg, file=sys.stderr)
      
      uv_status = _ok(path=uv_path, auto_installed=auto_installed) if uv_path else _warn("自动安装 uv 失败。请稍后尝试手动执行 pip install uv")
  else:
    uv_status = _ok(path=uv_path, auto_installed=False)

  if uv_path and pypi_config and auto_heal:
    # 自动注入项目级 uv.toml，让默认安装源适配国内网络。
    uv_toml_path = root / "uv.toml"
    if not uv_toml_path.exists():
      try:
        index_url = pypi_config.get("index_url")
        extra_index_urls = pypi_config.get("extra_index_urls", [])
        toml_lines = []
        if index_url:
          toml_lines.append("[[index]]")
          toml_lines.append(f'url = "{index_url}"')
        for extra in extra_index_urls:
          toml_lines.append("[[index]]")
          toml_lines.append(f'url = "{extra}"')

        if toml_lines:
          if auto_confirm:
            uv_toml_path.write_text(
                "\n".join(toml_lines) + "\n", encoding="utf-8"
            )
          elif not sys.stdin.isatty():
            print(
                "[自愈提示] stdin 非交互模式，跳过写入 uv.toml。"
                "请在交互终端中运行 --auto-heal 以自动写入。",
                file=sys.stderr,
            )
          else:
            confirm = input(
                f"[自愈提示] 将写入 {uv_toml_path}（国内 PyPI 源配置）。确认？[y/N] "
            )
            if confirm.strip().lower() in ("y", "yes"):
              uv_toml_path.write_text(
                  "\n".join(toml_lines) + "\n", encoding="utf-8"
              )
            else:
              print("[自愈提示] 已跳过写入 uv.toml。", file=sys.stderr)
      except OSError as exc:
        print(f"[自愈警告] 自动写入项目级 uv.toml 失败: {exc}", file=sys.stderr)

  checks: dict[str, dict[str, Any]] = {
      "python": _ok(
          version=".".join(str(part) for part in sys.version_info[:3]),
          executable=sys.executable,
      ),
      "uv": uv_status,
      "network_profile": _check_profile(),
      "license": _check_license(root),
      "temp_lock": _check_temp_lock(),
      "env_file": _check_env_file(root),
      "proxy": _check_proxy(),
  }

  if network:
    def _probe_pubmed():
      return _check_remote("PubMed 官方 API", PUBMED_HEALTH_URL, timeout, probe)

    def _probe_pdbj():
      return _check_remote("PDBJ 下载镜像", PDBJ_MIRROR_HEALTH_URL, timeout, probe)

    with ThreadPoolExecutor(max_workers=2) as executor:
      pubmed_future = executor.submit(_probe_pubmed)
      pdbj_future = executor.submit(_probe_pdbj)
      checks["pubmed_api"] = pubmed_future.result()
      checks["pdb_download_mirror"] = pdbj_future.result()
  else:
    checks["pubmed_api"] = _skip("已使用 --no-network，未访问 PubMed。")
    checks["pdb_download_mirror"] = _skip("已使用 --no-network，未访问 PDBJ。")

  status = "ok"
  if any(check["status"] == "fail" for check in checks.values()):
    status = "fail"
  elif any(check["status"] == "warn" for check in checks.values()):
    status = "warn"

  return {"status": status, "checks": checks}


def main(argv: list[str] | None = None) -> int:
  if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

  parser = argparse.ArgumentParser(description="Science Skills diagnostics")
  parser.add_argument(
      "--no-network",
      action="store_true",
      help="只运行本地检查，不访问外部数据库或镜像。",
  )
  parser.add_argument(
      "--timeout",
      type=float,
      default=10.0,
      help="网络探测超时时间，单位秒。",
  )
  parser.add_argument(
      "--root-dir",
      type=pathlib.Path,
      default=pathlib.Path.cwd(),
      help="用于检查 .env 是否存在的项目目录；不会读取 .env 内容。",
  )
  parser.add_argument(
      "--auto-heal", "--fix",
      action="store_true",
      help="允许诊断脚本自动执行修复操作（如安装缺失的依赖）。",
  )
  parser.add_argument(
      "-y", "--yes",
      action="store_true",
      help="跳过交互确认，自动执行所有修复操作（需配合 --auto-heal 使用）。",
  )
  args = parser.parse_args(argv)

  if args.yes and not args.auto_heal:
    print(
        "[提示] --yes/-y 需配合 --auto-heal 使用，否则无实际效果。",
        file=sys.stderr,
    )

  report = run_checks(
      root_dir=args.root_dir,
      network=not args.no_network,
      timeout=args.timeout,
      auto_heal=args.auto_heal,
      auto_confirm=args.yes,
  )
  print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
  return 1 if report["status"] == "fail" else 0


if __name__ == "__main__":
  raise SystemExit(main())
