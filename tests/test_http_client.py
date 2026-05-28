# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for HttpClient core functionality, fallback, and redaction."""

from __future__ import annotations

import io
import unittest
from unittest import mock

from skills.science_skills_common import http_client
from skills.science_skills_common.http_client import (
    HttpClient,
    HttpError,
    redact_url,
    _redact_proxy_url,
    fetch_batch,
)


class HttpClientTest(unittest.TestCase):

  def test_redact_url(self):
    self.assertIsNone(redact_url(None))
    self.assertEqual(redact_url("https://example.com/api"), "https://example.com/api")
    self.assertEqual(
        redact_url("https://example.com/api?api_key=secret123&q=test"),
        "https://example.com/api?api_key=REDACTED&q=test",
    )
    self.assertEqual(
        redact_url("https://example.com/api?api-key=secret123&q=test"),
        "https://example.com/api?api-key=REDACTED&q=test",
    )
    self.assertEqual(
        redact_url("https://example.com/api?apiKey=secret123&q=test"),
        "https://example.com/api?apiKey=REDACTED&q=test",
    )

  def test_redact_proxy_url(self):
    self.assertEqual(
        _redact_proxy_url("http://user:pass@127.0.0.1:8080"),
        "http://127.0.0.1:8080",
    )
    self.assertEqual(
        _redact_proxy_url("http://127.0.0.1:8080"),
        "http://127.0.0.1:8080",
    )
    self.assertEqual(
        _redact_proxy_url("invalid-url"),
        "invalid-url",
    )

  @mock.patch("urllib.request.OpenerDirector.open")
  def test_fetch_with_fallback_chains_errors(self, mock_open):
    # Mock urllib to raise HTTP Error using a generator function to ensure
    # each raised HTTPError has its own unclosed BytesIO instance.
    import urllib.error
    def side_effect(*args, **kwargs):
      raise urllib.error.HTTPError(
          "http://error.com", 500, "Internal Server Error", {}, io.BytesIO(b"")
      )
    mock_open.side_effect = side_effect

    client = HttpClient("https://base.org", 5.0)
    with self.assertRaises(HttpError) as ctx:
      client.fetch_with_fallback(
          "https://base.org/primary",
          alternatives=["https://base.org/alt1", "https://base.org/alt2"],
      )

    exc = ctx.exception
    self.assertEqual(exc.status_code, 500)
    # Check that __cause__ chains the first failure (primary URL)
    self.assertIsNotNone(exc.__cause__)
    self.assertEqual(exc.__cause__.url, "https://base.org/primary")

    # Check that __notes__ contains information about prior failures (Python 3.11+)
    if hasattr(exc, "add_note"):
      self.assertTrue(any("Prior failure [1/3]" in note for note in exc.__notes__))
      self.assertTrue(any("Prior failure [2/3]" in note for note in exc.__notes__))

  @mock.patch("skills.science_skills_common.http_client.HttpClient.fetch")
  def test_fetch_batch_preserves_order_and_handles_failures(self, mock_fetch):
    def side_effect(url, **kwargs):
      if "fail" in url:
        raise HttpError("Failed to fetch", status_code=404, url=url)
      return http_client.HttpResponse(
          status_code=200,
          headers={},
          data=b"Success",
          url=url,
      )

    mock_fetch.side_effect = side_effect

    client = HttpClient("https://base.org", 5.0)
    urls = [
        "https://base.org/ok1",
        "https://base.org/fail",
        "https://base.org/ok2",
    ]
    results = fetch_batch(client, urls)

    self.assertEqual(len(results), 3)
    self.assertEqual(results[0].data, b"Success")
    self.assertIsInstance(results[1], HttpError)
    self.assertEqual(results[1].status_code, 404)
    self.assertEqual(results[2].data, b"Success")


if __name__ == "__main__":
  unittest.main()
