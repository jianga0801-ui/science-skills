import json
import http.client
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


class ScienceDoctorTest(unittest.TestCase):
  def test_script_path_execution_outputs_json_without_pythonpath(self):
    repo_root = pathlib.Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env.pop("SCIENCE_NETWORK_PROFILE", None)
    env.pop("SCIENCE_NETWORK_PROFILE_DIR", None)

    result = subprocess.run(
        [sys.executable, "tools/science_doctor.py", "--no-network"],
        cwd=repo_root,
        env=env,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    self.assertTrue(
        result.stdout.strip(),
        f"science_doctor produced no stdout; returncode={result.returncode}; "
        f"stderr={result.stderr!r}",
    )
    report = json.loads(result.stdout)
    self.assertIn(report["status"], {"ok", "warn"})
    self.assertEqual(report["checks"]["pubmed_api"]["status"], "skip")

  def test_local_checks_do_not_expose_env_file_or_proxy_secret(self):
    from tools import science_doctor

    with tempfile.TemporaryDirectory() as temp_dir:
      root_dir = pathlib.Path(temp_dir)
      (root_dir / ".env").write_text(
          "SCIENCE_PROXY=http://private-proxy.example:7890\n"
          "LOCAL_CREDENTIAL=SENSITIVE_MARKER\n",
          encoding="utf-8",
      )

      with mock.patch.dict(
          os.environ,
          {"SCIENCE_PROXY": "http://127.0.0.1:7890"},
          clear=True,
      ):
        report = science_doctor.run_checks(root_dir=root_dir, network=False)

    rendered = json.dumps(report, ensure_ascii=False)
    self.assertNotIn("SENSITIVE_MARKER", rendered)
    self.assertNotIn("private-proxy", rendered)
    self.assertNotIn("127.0.0.1", rendered)
    self.assertEqual(report["checks"]["env_file"]["status"], "warn")
    self.assertTrue(report["checks"]["proxy"]["configured"])
    self.assertEqual(report["checks"]["proxy"]["env"], "SCIENCE_PROXY")

  def test_no_proxy_is_ok_for_builtin_china_profile(self):
    from tools import science_doctor

    with mock.patch.dict(os.environ, {}, clear=True):
      report = science_doctor.run_checks(network=False)

    self.assertEqual(report["checks"]["proxy"]["status"], "ok")
    self.assertFalse(report["checks"]["proxy"]["configured"])

  def test_system_proxy_is_detected_without_exposing_secret(self):
    from tools import science_doctor

    with mock.patch.dict(
        os.environ,
        {"HTTP_PROXY": "http://private-proxy.example:7890"},
        clear=True,
    ):
      report = science_doctor.run_checks(network=False)

    rendered = json.dumps(report, ensure_ascii=False)
    self.assertNotIn("private-proxy", rendered)
    self.assertEqual(report["checks"]["proxy"]["status"], "ok")
    self.assertTrue(report["checks"]["proxy"]["configured"])
    self.assertEqual(report["checks"]["proxy"]["env"], "HTTP_PROXY")

  def test_network_probe_failure_returns_chinese_hint(self):
    from tools import science_doctor

    def failing_probe(url, timeout):
      raise OSError("timed out")

    report = science_doctor.run_checks(network=True, probe=failing_probe)

    self.assertEqual(report["checks"]["pubmed_api"]["status"], "fail")
    self.assertIn("网络", report["checks"]["pubmed_api"]["hint"])

  def test_no_network_mode_skips_remote_checks(self):
    from tools import science_doctor

    report = science_doctor.run_checks(network=False)

    self.assertEqual(report["checks"]["pubmed_api"]["status"], "skip")
    self.assertEqual(report["checks"]["pdb_download_mirror"]["status"], "skip")

  def test_probe_url_falls_back_to_get_when_head_disconnects(self):
    from tools import science_doctor

    class Response:
      def __enter__(self):
        return self

      def __exit__(self, exc_type, exc, traceback):
        return False

    calls = []

    def fake_urlopen(request, timeout):
      calls.append(request)
      if len(calls) == 1:
        raise http.client.RemoteDisconnected("remote closed")
      return Response()

    with mock.patch.object(science_doctor.urllib.request, "urlopen", fake_urlopen):
      science_doctor._probe_url("https://example.test/file.gz", timeout=1)

    self.assertEqual([request.get_method() for request in calls], ["HEAD", "GET"])
    self.assertEqual(calls[1].headers["Range"], "bytes=0-0")
    self.assertEqual(calls[0].headers["User-agent"], "science-skills-doctor/0.1")
    self.assertEqual(calls[1].headers["User-agent"], "science-skills-doctor/0.1")


if __name__ == "__main__":
  unittest.main()
