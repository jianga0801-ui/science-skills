import importlib
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock
import threading
import time


class FileLockTest(unittest.TestCase):
  def setUp(self):
    self._env = mock.patch.dict(os.environ, {}, clear=True)
    self._env.start()

  def tearDown(self):
    self._env.stop()

  def _load_http_client(self):
    module_name = "skills.science_skills_common.http_client"
    if module_name in sys.modules:
      return importlib.reload(sys.modules[module_name])
    return importlib.import_module(module_name)

  def test_lock_empty_file(self):
    http_client = self._load_http_client()
    tmp = tempfile.NamedTemporaryFile(mode="a+", delete=False)
    try:
      with http_client._exclusive_file_lock(tmp):
        tmp.write("test content\n")
        tmp.flush()
        tmp.seek(0)
        self.assertEqual(tmp.read(), "test content\n")
    finally:
      tmp.close()
      try:
        os.unlink(tmp.name)
      except OSError:
        pass

  def test_lock_file_with_content(self):
    http_client = self._load_http_client()
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".lock"
    ) as tmp:
      tmp.write("initial content\n")
      tmp.flush()
      file_path = tmp.name

    try:
      with open(file_path, "r+") as f:
        with http_client._exclusive_file_lock(f):
          f.seek(0)
          content = f.read()
          self.assertEqual(content, "initial content\n")
          f.seek(0)
          f.truncate()
          f.write("new content\n")
          f.flush()
      with open(file_path, "r") as f:
        self.assertEqual(f.read(), "new content\n")
    finally:
      try:
        os.unlink(file_path)
      except OSError:
        pass

  def test_lock_two_files_independent(self):
    http_client = self._load_http_client()
    with tempfile.TemporaryDirectory() as tmpdir:
      p1 = pathlib.Path(tmpdir) / "f1.lock"
      p2 = pathlib.Path(tmpdir) / "f2.lock"
      with open(p1, "w+") as f1, open(p2, "w+") as f2:
        with http_client._exclusive_file_lock(f1):
          with http_client._exclusive_file_lock(f2):
            f1.write("file one\n")
            f2.write("file two\n")
            f1.flush()
            f2.flush()
        f1.seek(0)
        f2.seek(0)
        self.assertEqual(f1.read(), "file one\n")
        self.assertEqual(f2.read(), "file two\n")

  def test_rate_limiter_lock_file_creatable(self):
    http_client = self._load_http_client()
    limiter = http_client._RateLimiter("test-host.example.com", qps=10)
    limiter.wait()
    lock_path = pathlib.Path(limiter._lock_file)
    self.assertTrue(lock_path.exists())
    try:
      lock_path.unlink()
    except OSError:
      pass


  def test_lock_contention_between_threads(self):
    """Thread B must wait for Thread A's lock to release."""
    http_client = self._load_http_client()
    with tempfile.TemporaryDirectory() as tmpdir:
      lock_path = pathlib.Path(tmpdir) / "shared.lock"
      results = []
      barrier = threading.Barrier(2, timeout=10)

      def thread_a():
        with open(lock_path, "a+") as f:
          with http_client._exclusive_file_lock(f):
            results.append("A_acquired")
            barrier.wait()  # signal B that A has the lock
            f.seek(0)
            f.truncate()
            f.write("A_data\n")
            f.flush()
            time.sleep(0.2)  # ensure B has time to attempt lock
          results.append("A_released")

      def thread_b():
        barrier.wait()  # wait for A to acquire
        # brief sleep to ensure A is inside the lock
        time.sleep(0.05)
        with open(lock_path, "a+") as f:
          # B should block here until A releases
          with http_client._exclusive_file_lock(f):
            results.append("B_acquired")
            f.seek(0)
            data = f.read()
            results.append("B_read:" + data.strip())
          results.append("B_released")

      t_a = threading.Thread(target=thread_a)
      t_b = threading.Thread(target=thread_b)
      t_a.start()
      t_b.start()
      t_a.join(timeout=10)
      t_b.join(timeout=10)

      self.assertFalse(t_a.is_alive(), "Thread A timed out")
      self.assertFalse(t_b.is_alive(), "Thread B timed out")

      # Verify ordering: B must not acquire until after A releases
      self.assertEqual(results[0], "A_acquired")
      a_release_idx = results.index("A_released")
      b_acquire_idx = results.index("B_acquired")
      self.assertLess(a_release_idx, b_acquire_idx,
                      "B acquired lock before A released")
      # B should have read A's data
      self.assertEqual(results[results.index("B_read:A_data")], "B_read:A_data")


if __name__ == "__main__":
  unittest.main()
