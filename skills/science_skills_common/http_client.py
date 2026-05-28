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

"""Unified HTTP client with rate limiting, retries, and backoff.

Provides `HttpClient` — a single entry-point that combines:

* **Per-API rate limiting** via `_RateLimiter` (cross-process file-lock).
* **Automatic retries** on transient errors (HTTP 429, 5xx).
* **Exponential backoff** with optional *jitter*.
* **Retry-After header** support (server-directed backoff).
* **X-Throttling-Control** proactive backpressure (PubChem / NCBI).
* **Configurable timeouts** per request.

Transport is `urllib.request` (stdlib) — no third-party dependencies.

Typical usage:

```
import http_client

# Scoped to a specific base URL
api_client = http_client.HttpClient(
  "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/",
  qps=3
)

# Simple GET with relative path (returns parsed JSON).
data = api_client.fetch_json("esummary.fcgi?db=pubmed&id=123456")

# POST with a JSON body.
data = api_client.fetch_json(
  "esearch.fcgi",
  method="POST",
  json_body={"db": "pubmed", "term": "cancer"},
)

# Raw bytes (e.g. file / PDF download).
pdf = api_client.fetch_bytes(
  "efetch.fcgi?db=pubmed&id=123456&rettype=abstract",
  timeout=60
)
```
"""

from __future__ import annotations

import contextlib
import datetime
import email.utils
import gzip
import http.client
import importlib.resources
import json
import logging
import os
import pathlib
import random
import re
import tempfile
import time
from typing import Any, Iterator
import urllib.error
import urllib.parse
import urllib.request

try:
  import fcntl
except ImportError:
  fcntl = None

try:
  import msvcrt
except ImportError:
  msvcrt = None

__all__ = [
    "HttpClient",
    "HttpError",
    "HttpResponse",
    "NetworkProfileError",
    "apply_mirror",
    "clear_network_profile_cache",
    "get_api_url",
    "load_network_profile",
    "redact_sensitive_text",
    "redact_url",
    "DEFAULT_BACKOFF_BASE_SECS",
    "DEFAULT_BACKOFF_MAX_SECS",
    "DEFAULT_JITTER_SECS",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_TIMEOUT_SECS",
    "RETRYABLE_STATUS_CODES",
]

RETRYABLE_STATUS_CODES: frozenset[int] = frozenset({429, 500, 502, 503, 504})
DEFAULT_TIMEOUT_SECS: float = 60.0
DEFAULT_MAX_RETRIES: int = 7
DEFAULT_BACKOFF_BASE_SECS: float = 3.0
DEFAULT_BACKOFF_MAX_SECS: float = 180.0
DEFAULT_JITTER_SECS: float = 0.5
FAST_FAIL_MAX_RETRIES: int = 1
FAST_FAIL_TIMEOUT_SECS: float = 10.0
FAST_FAIL_BACKOFF_MAX_SECS: float = 5.0
_DEFAULT_USER_AGENT: str = "science-skills/0.1.0"
DEFAULT_CHARSET: str = "utf-8"
PROJECT_NAME: str = "science-skills"
SKILL_REFERER_TEMPLATE: str = (
    "https://github.com/google-deepmind/science-skills/tree/main/{skill}"
)
DEFAULT_NETWORK_PROFILE = "china"
NETWORK_PROFILE_ENV = "SCIENCE_NETWORK_PROFILE"
NETWORK_PROFILE_DIR_ENV = "SCIENCE_NETWORK_PROFILE_DIR"
DEFAULT_NETWORK_PROFILE_DIR = (
    pathlib.Path(__file__).resolve().parents[2] / "config" / "network_profiles"
)
_NETWORK_PROFILE_CACHE: dict[tuple[str, str], dict[str, Any]] = {}
_LOCK_FALLBACK_WARNING_EMITTED = False

def clear_network_profile_cache() -> None:
  """Clear the cached network profiles and force re-read on next access."""
  _NETWORK_PROFILE_CACHE.clear()
SENSITIVE_QUERY_PARAMS = frozenset({
    "access_token",
    "api-key",
    "api_key",
    "apikey",
    "client_secret",
    "key",
    "password",
    "secret",
    "token",
})

# Regex for parsing X-Throttling-Control status entries.
# Matches e.g. "Request Count status: Red (82%)".
_THROTTLE_STATUS_RE = re.compile(
    r"(\w[\w ]*?) status:\s*(Green|Yellow|Red|Black)\s*\((\d+)%\)"
)

# Backpressure delays (seconds) keyed by throttle colour.
_THROTTLE_BACKPRESSURE: dict[str, float] = {
    "Green": 0.0,
    "Yellow": 1.0,
    "Red": 5.0,
    "Black": 30.0,
}

class NetworkProfileError(Exception):
  """Raised when a configured network profile cannot be loaded."""


def load_network_profile(profile_name: str | None = None) -> dict[str, Any]:
  """Load the configured network profile JSON.

  Defaults to package data bundled with `science-skills-common`. Agents can
  select another profile with `SCIENCE_NETWORK_PROFILE` or point to a custom
  directory with `SCIENCE_NETWORK_PROFILE_DIR`.
  """
  name = profile_name or os.environ.get(
      NETWORK_PROFILE_ENV, DEFAULT_NETWORK_PROFILE
  )
  profile_dir_override = os.environ.get(NETWORK_PROFILE_DIR_ENV)
  profile_dir = (
      pathlib.Path(profile_dir_override)
      if profile_dir_override
      else DEFAULT_NETWORK_PROFILE_DIR
  )
  cache_key = (name, str(profile_dir.resolve()))
  if cache_key in _NETWORK_PROFILE_CACHE:
    return _NETWORK_PROFILE_CACHE[cache_key]

  if NETWORK_PROFILE_DIR_ENV in os.environ:
    profile = _load_network_profile_file(profile_dir / f"{name}.json", name)
    _NETWORK_PROFILE_CACHE[cache_key] = profile
    return profile

  try:
    profile_text = (
        importlib.resources.files(__package__)
        .joinpath("network_profiles", f"{name}.json")
        .read_text(encoding="utf-8")
    )
    profile = json.loads(profile_text)
  except (FileNotFoundError, ModuleNotFoundError) as exc:
    profile = _load_network_profile_file(
        DEFAULT_NETWORK_PROFILE_DIR / f"{name}.json", name
    )
  except json.JSONDecodeError as exc:
    raise NetworkProfileError(
        f"网络 profile '{name}' 不是有效 JSON: package resource: {exc}"
    ) from exc

  if not isinstance(profile, dict):
    raise NetworkProfileError(
        f"网络 profile '{name}' 格式错误: 顶层必须是 JSON object。"
    )
  _NETWORK_PROFILE_CACHE[cache_key] = profile
  return profile


def _load_network_profile_file(
    profile_path: pathlib.Path, name: str
) -> dict[str, Any]:
  """Load a profile from an explicit filesystem path."""
  try:
    with profile_path.open("r", encoding="utf-8") as f:
      profile = json.load(f)
  except FileNotFoundError as exc:
    raise NetworkProfileError(
        f"网络 profile '{name}' 不存在: {profile_path}。请检查 "
        f"{NETWORK_PROFILE_ENV} 或 {NETWORK_PROFILE_DIR_ENV}。"
    ) from exc
  except json.JSONDecodeError as exc:
    raise NetworkProfileError(
        f"网络 profile '{name}' 不是有效 JSON: {profile_path}: {exc}"
    ) from exc

  if not isinstance(profile, dict):
    raise NetworkProfileError(
        f"网络 profile '{name}' 格式错误: 顶层必须是 JSON object。"
    )
  return profile


def get_api_url(source_key: str, fallback: str) -> str:
  """Return the official API URL for *source_key* from the active network profile.

  Falls back to *fallback* if the profile or source entry is missing.
  """
  try:
    profile = load_network_profile()
    url = profile.get("sources", {}).get(source_key, {}).get("official_api")
    if url:
      return url
  except NetworkProfileError:
    pass
  except Exception as exc:
    logging.warning(
        "get_api_url(%r): unexpected error reading profile, using fallback: %s",
        source_key,
        exc,
    )
  return fallback


def _format_mirror_url(
    mirror_prefix: str, source_suffix: str, transformer: str | None
) -> str:
  """Format a mirror URL for source-specific download layouts."""
  if transformer == "pdbj_divided_structure":
    return _format_pdbj_divided_structure_url(mirror_prefix, source_suffix)
  return urllib.parse.urljoin(mirror_prefix, source_suffix)


def _format_pdbj_divided_structure_url(
    mirror_prefix: str, source_suffix: str
) -> str:
  """Map RCSB PDB/mmCIF download filenames to PDBJ divided archive paths."""
  filename = pathlib.PurePosixPath(source_suffix).name.lower()
  compressed = filename.endswith(".gz")
  if compressed:
    filename = filename[:-3]

  match = re.fullmatch(r"(?:pdb_0+)?([0-9a-z]{4})\.(cif|pdb)", filename)
  if not match:
    original_url = urllib.parse.urljoin(mirror_prefix, source_suffix)
    logging.info(
        "PDBJ mirror does not support %s; passing through to official source",
        original_url,
    )
    return original_url

  pdb_id, file_format = match.groups()
  shard = pdb_id[1:3]
  suffix = ".gz" if compressed else ""
  if file_format == "cif":
    path = f"mmCIF/{shard}/{pdb_id}.cif{suffix}"
  else:
    path = f"pdb/{shard}/pdb{pdb_id}.ent{suffix}"
  return urllib.parse.urljoin(mirror_prefix, path)


def apply_mirror(url: str) -> str:
  """Apply profile-configured download mirrors without changing API URLs."""
  profile = load_network_profile()
  for source in profile.get("sources", {}).values():
    for mirror in source.get("mirrors", []):
      source_prefix = mirror.get("source_prefix")
      mirror_prefix = mirror.get("mirror_prefix")
      if not source_prefix or not mirror_prefix:
        continue
      if url.startswith(source_prefix):
        source_suffix = url[len(source_prefix) :]
        return _format_mirror_url(
            mirror_prefix, source_suffix, mirror.get("transformer")
        )
  return url


@contextlib.contextmanager
def _exclusive_file_lock(f) -> Iterator[None]:
  """Cross-platform advisory lock for the rate limiter state file."""
  if fcntl is not None:
    fcntl.flock(f, fcntl.LOCK_EX)
    try:
      yield
    finally:
      fcntl.flock(f, fcntl.LOCK_UN)
  elif msvcrt is not None:
    # Ensure file has content before locking -- avoids race where an
    # empty file could be modified by another process between the
    # write and the lock acquisition.
    f.seek(0, os.SEEK_END)
    if f.tell() == 0:
      f.write("\n")
      f.flush()
    # Lock a 1024-byte range (not 1 byte) so concurrent processes
    # cannot truncate or re-write the file while we hold the lock.
    lock_len = 1024
    f.seek(0)
    deadline = time.monotonic() + 5.0  # 5-second ceiling
    while True:
      try:
        msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, lock_len)
        break  # lock acquired
      except OSError:
        if time.monotonic() >= deadline:
          # Give up and proceed without lock -- better than hanging
          # forever.  The rate limiter degrades gracefully.
          break
        time.sleep(0.01)
    try:
      yield
    finally:
      f.seek(0)
      try:
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, lock_len)
      except OSError:
        pass  # best-effort unlock
  else:
    global _LOCK_FALLBACK_WARNING_EMITTED
    if not _LOCK_FALLBACK_WARNING_EMITTED:
      logging.warning(
          "science-skills rate limiter is running without cross-process "
          "locking; API rate limits may be less reliable in this Python build."
      )
      _LOCK_FALLBACK_WARNING_EMITTED = True
    yield


class _RateLimiter:
  """Enforces a minimum interval between requests.

  Uses a shared lock file in the platform temp directory so multiple processes
  respect the same rate limit.

  Example:
        limiter = _RateLimiter('ncbi.nlm.nih.gov', qps=10)
  """

  def __init__(self, hostname: str, qps: float):
    """Initialize rate limiter.

    Args:
      hostname: Hostname of the API.
      qps: Maximum queries per second.
    """
    self._min_interval = 1.0 / qps
    safe_hostname = re.sub(r"[^A-Za-z0-9_.-]", "_", hostname)
    self._lock_file = os.path.join(
        tempfile.gettempdir(), f"{PROJECT_NAME}-{safe_hostname}.lock"
    )

  def wait(self, min_sleep: float = 0.0):
    """Block until the next request is allowed.

    Args:
      min_sleep: Additional minimum sleep in seconds.  The actual delay is
        `max(rate_limit_gap, min_sleep)`, which lets callers fold retry back-off
        into the same call.
    """
    with open(self._lock_file, "a+") as f:
      with _exclusive_file_lock(f):
        f.seek(0)
        content = f.read().strip()
        last_ts = float(content) if content else 0.0
        now = time.monotonic()
        gap = self._min_interval - (now - last_ts)
        delay = max(gap, min_sleep)
        if delay > 0:
          time.sleep(delay)
        f.seek(0)
        f.truncate()
        f.write(str(time.monotonic()))
        f.flush()


def _maybe_decompress(
    response: http.client.HTTPResponse,
) -> http.client.HTTPResponse | gzip.GzipFile:
  """Wrap the response in a gzip decompressor if Content-Encoding says so.

  Args:
    response: The response to wrap. Must support .read() and .headers.

  Returns:
    A `GzipFile` wrapper if the response is gzip-encoded, otherwise the
    original response unchanged.
  """
  encoding = response.headers.get("Content-Encoding", "").lower()
  if encoding in ("gzip", "x-gzip"):
    return gzip.GzipFile(fileobj=response)
  return response


def redact_url(url: str | None) -> str | None:
  """Return *url* with sensitive query parameter values redacted."""
  if url is None:
    return None
  try:
    parsed = urllib.parse.urlsplit(url)
  except ValueError:
    return url
  if not parsed.query:
    return url

  query = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
  redacted_query = [
      (
          key,
          "REDACTED" if key.lower() in SENSITIVE_QUERY_PARAMS else value,
      )
      for key, value in query
  ]
  return urllib.parse.urlunsplit(
      parsed._replace(query=urllib.parse.urlencode(redacted_query))
  )


def redact_sensitive_text(text: str | None) -> str | None:
  """Redact sensitive query parameter values in arbitrary text."""
  if text is None:
    return None

  param_names = "|".join(re.escape(name) for name in sorted(SENSITIVE_QUERY_PARAMS))

  def replace(match: re.Match[str]) -> str:
    return f"{match.group(1)}=REDACTED"

  return re.sub(
      rf"(?i)([?&;]?(?:{param_names}))=([^&\s\"'<>]+)",
      replace,
      text,
  )


class HttpError(Exception):
  """Raised when an HTTP request fails with a non-retryable or exhausted error.

  Attributes:
    status_code: HTTP status code (`None` for network-level failures).
    body: Raw error response body bytes, if available.
    url: The URL that was requested.
  """

  MAX_BODY_SUMMARY_LEN = 500

  def __init__(
      self,
      message: str,
      *,
      status_code: int | None = None,
      body: bytes | None = None,
      url: str | None = None,
  ):
    message = redact_sensitive_text(message) or message
    # Append server body to message to help agent debug any errors.
    if summary := self._summarize_body(body):
      message = f"{message}\nServer body: {summary}"

    super().__init__(message)
    self.status_code = status_code
    self.body = body
    self.url = redact_url(url)

  def json(self) -> Any:
    """Attempt to parse the error body as JSON."""
    # Let the JSON decode fail with JSONDecodeError if the body is empty
    body = self.body or b""
    return json.loads(body.decode("utf-8"))

  @classmethod
  def _summarize_body(cls, body: bytes) -> str | None:
    """Return a short summary of the error body if available."""
    if not body:
      return None
    if body.startswith(b"\x1f\x8b"):  # Gzip encoding.
      try:
        body = gzip.decompress(body)
      except gzip.BadGzipFile:
        return None

    decoded = body.decode("utf-8", errors="replace").strip()
    decoded = redact_sensitive_text(decoded) or decoded
    if len(decoded) > cls.MAX_BODY_SUMMARY_LEN:
      return decoded[: cls.MAX_BODY_SUMMARY_LEN] + "..."
    return decoded


class HttpResponse:
  """Lightweight wrapper around an HTTP response.

  Attributes:
    data: Raw response body bytes (decompressed if the server sent
      `Content-Encoding: gzip`).
    status_code: HTTP status code.
    headers: Response headers as a dict.
    url: The final URL after any redirects.
    encoding: Character encoding parsed from the `Content-Type` header.  Falls
      back to `"utf-8"` when absent.
  """

  __slots__ = ("data", "status_code", "headers", "url", "encoding")

  def __init__(
      self,
      data: bytes,
      status_code: int,
      headers: dict[str, str],
      url: str,
      encoding: str | None = None,
  ):
    self.data = data
    self.status_code = status_code
    self.headers = headers
    self.url = url
    self.encoding = encoding or "utf-8"

  def json(self) -> Any:
    """Parse the response body as JSON."""
    return json.loads(self.data.decode(self.encoding))

  @property
  def text(self) -> str:
    """Decode the response body using the detected charset."""
    return self.data.decode(self.encoding)

  def __repr__(self) -> str:
    return (
        f"HttpResponse(status={self.status_code}, "
        f"url={self.url!r}, size={len(self.data)})"
    )


def _parse_retry_after(headers) -> float | None:
  """Extract `Retry-After` value from HTTP response headers.

  Handles both formats defined in RFC 7231 §7.1.3:

  * **delta-seconds** — `Retry-After: 120`
  * **HTTP-date** — `Retry-After: Mon, 31 Mar 2026 15:10:00 GMT`

  Args:
    headers: Response headers (dict-like or `http.client.HTTPMessage`).

  Returns:
    Delay in seconds, or `None` if the header is absent or not parseable.
  """
  value = headers.get("Retry-After")
  if value is None:
    return None

  try:
    return float(value)
  except ValueError:
    pass

  try:
    retry_dt = email.utils.parsedate_to_datetime(value)
    delta = (
        retry_dt - datetime.datetime.now(datetime.timezone.utc)
    ).total_seconds()
    return max(0.0, delta)
  except (TypeError, ValueError, OverflowError):
    logging.warning("Failed to parse Retry-After header value: %r", value)
    return None


def _parse_throttle_control(headers) -> float:
  """Parse `X-Throttling-Control` header for proactive backpressure.

  The header (used by PubChem / NCBI) reports real-time usage across three
  dimensions:

      X-Throttling-Control: Request Count status: Green (12%),
          Request Time status: Yellow (55%), Service status: Green (8%)

  Each dimension has a colour: Green (<50%), Yellow (50–75%), Red (>75%), Black
  (blocked).  We return the worst-case backpressure delay across all dimensions
  so the client can slow down **before** hitting a hard 429/503.

  Args:
    headers: Mapping of response headers.

  Returns:
    Recommended additional delay in seconds (0.0 if Green or header
    is absent).
  """
  value = headers.get("X-Throttling-Control")
  if not value:
    return 0.0

  max_delay = 0.0
  for match in _THROTTLE_STATUS_RE.finditer(value):
    colour = match.group(2)
    delay = _THROTTLE_BACKPRESSURE.get(colour, 0.0)
    if delay > max_delay:
      max_delay = delay
  return max_delay


class HttpClient:
  """Rate-limited HTTP client with automatic retries and backoff.

  Uses `urllib.request` as the transport layer. Handles gzip decompression,
  charset detection, and streaming iteration internally.

  Proxy configuration (``SCIENCE_PROXY``, ``HTTPS_PROXY``, ``HTTP_PROXY``)
  is read once on the first request and cached for the client's lifetime.
  Changing environment variables after the first request has no effect —
  create a new ``HttpClient`` instance instead.

  Example:

      chembl_api = HttpClient(
          "https://www.ebi.ac.uk/chembl/api/data/",
          qps=5,
          jitter=0.5,
      )
      data = chembl_api.fetch_json("molecule/CHEMBL25.json")
  """

  def __init__(
      self,
      base_url: str,
      qps: float,
      *,
      default_headers: dict[str, str] | None = None,
      max_retries: int | None = None,
      timeout: float | None = None,
      backoff_base: float = DEFAULT_BACKOFF_BASE_SECS,
      backoff_max: float | None = None,
      jitter: float = DEFAULT_JITTER_SECS,
      user_agent: str | None = None,
      retryable_status_codes: frozenset[int] = RETRYABLE_STATUS_CODES,
      referer_skill: str | None = None,
      fast_fail: bool = False,
  ):
    """Rate-limited HTTP client with automatic retries and backoff.

    Args:
      base_url: Base URL of the API (e.g. "https://eutils.ncbi.nlm.nih.gov/").
      qps: Maximum queries per second (steady-state).
      default_headers: Default HTTP headers to include in every request.
      max_retries: Maximum retry attempts for transient errors.  The total
        number of attempts is `max_retries + 1`.
      timeout: Default per-request timeout in seconds.
      backoff_base: Base delay (seconds) for exponential backoff.
      backoff_max: Cap on backoff delay (seconds).
      jitter: Maximum random jitter (seconds) added uniformly to each backoff
        delay.
      user_agent: Default `User-Agent` header value.  Falls back to the
        `SCIENCE_SKILLS_USER_AGENT` env var.
      retryable_status_codes: HTTP status codes that trigger a retry.
      referer_skill: Skill name to use to populate HTTP Referer header.
      fast_fail: When True, use aggressive retry/timeout settings
        (max_retries=1, timeout=10s, backoff_max=5s) for fast fallback
        to alternative endpoints.  Only applies when the caller does not
        explicitly set max_retries, timeout, or backoff_max.
    """
    self.base_url = base_url
    parsed = urllib.parse.urlparse(base_url)
    if not parsed.scheme or not parsed.netloc:
      raise ValueError(f"base_url must be an absolute URL: {base_url!r}")
    self.hostname = parsed.hostname
    fast = fast_fail
    self.max_retries = max_retries if max_retries is not None else (FAST_FAIL_MAX_RETRIES if fast else DEFAULT_MAX_RETRIES)
    self.timeout = timeout if timeout is not None else (FAST_FAIL_TIMEOUT_SECS if fast else DEFAULT_TIMEOUT_SECS)
    self.backoff_max = backoff_max if backoff_max is not None else (FAST_FAIL_BACKOFF_MAX_SECS if fast else DEFAULT_BACKOFF_MAX_SECS)
    self.backoff_base = backoff_base
    self.jitter = jitter
    self.user_agent = user_agent or os.environ.get(
        "SCIENCE_SKILLS_USER_AGENT", _DEFAULT_USER_AGENT
    )
    self.retryable_status_codes = retryable_status_codes
    self.default_headers = default_headers or {}
    self._limiter = _RateLimiter(self.hostname, qps=qps)
    self._next_min_sleep = 0.0
    self._referer_skill = referer_skill
    self._proxy_opener: urllib.request.OpenerDirector | None = None

  def wait(self, min_sleep: float = 0.0) -> None:
    """Wait for the rate limiter without making a request.

    Useful for non-`fetch` operations that still need to respect the
    cross-process rate limit — for example, polling loops or pre-streaming
    handshakes.

    Args:
      min_sleep: Minimum time to sleep in seconds before returning.
    """
    self._limiter.wait(min_sleep=min_sleep)

  def _compute_backoff(
      self, attempt: int, retry_after: float | None = None
  ) -> float:
    """Compute the delay before the next retry.

    Uses exponential backoff `base * 2^attempt` capped at `backoff_max`, with
    optional uniform jitter.  If the server provided a `Retry-After` value, the
    returned delay is at least that large.

    Args:
      attempt: Zero-based retry attempt number (0 = first *retry*).
      retry_after: Optional server `Retry-After` value in seconds.

    Returns:
      Delay in seconds.
    """
    delay = self.backoff_base * (2**attempt)
    if retry_after is not None:
      delay = max(delay, retry_after)
    delay = min(delay, self.backoff_max)
    if self.jitter > 0:
      delay += random.uniform(0, self.jitter)
    return delay

  def _resolve_url(self, url: str) -> str:
    """Resolve *url* against `base_url`."""
    if "://" not in url:
      resolved = urllib.parse.urljoin(self.base_url, url)
    else:
      if not url.startswith(self.base_url):
        raise ValueError(f"URL {url!r} does not match base_url {self.base_url!r}")
      resolved = url

    return apply_mirror(resolved)

  def _build_request(
      self,
      url: str,
      method: str,
      headers: dict[str, str] | None,
      data: bytes | None,
      json_body: Any | None,
  ) -> urllib.request.Request:
    """Build a `urllib.request.Request` from the given parameters."""
    merged_headers = {
        "User-Agent": self.user_agent,
        "Accept-Encoding": "gzip",
    }
    if self._referer_skill:
      merged_headers["Referer"] = SKILL_REFERER_TEMPLATE.format(
          skill=self._referer_skill
      )
    # Must be last: Give priority to user-provided headers.
    merged_headers.update(self.default_headers)
    if headers:
      merged_headers.update(headers)

    body: bytes | None = data
    if json_body is not None:
      body = json.dumps(json_body).encode("utf-8")
      merged_headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(
        url,
        data=body,
        headers=merged_headers,
        method=method,
    )
    return req

  def fetch(
      self,
      url: str,
      *,
      method: str = "GET",
      headers: dict[str, str] | None = None,
      data: bytes | None = None,
      json_body: Any | None = None,
      timeout: float | None = None,
      max_retries: int | None = None,
  ) -> HttpResponse:
    """Execute an HTTP request with rate limiting and retries.

    On each attempt the client:

    1. Waits for the rate limiter (cross-process file-lock).
    2. Sends the request via `urllib.request`.
    3. On success (2xx), returns an `HttpResponse`.
    4. On a retryable HTTP error (429, 5xx) or a network error, sleeps for an
       exponential backoff delay (with optional jitter and `Retry-After`
       support) before retrying.
    5. On a non-retryable HTTP error, raises `HttpError` immediately.

    Args:
      url: Request URL.
      method: HTTP method (`GET`, `POST`, etc.).
      headers: Extra HTTP headers (merged with the default User-Agent).
      data: Raw request body bytes (mutually exclusive with *json_body*).
      json_body: JSON-serializable request body.  Automatically sets
        `Content-Type: application/json`.
      timeout: Per-request timeout in seconds (overrides the client-level
        default).
      max_retries: Override for the maximum number of retry attempts.

    Returns:
      `HttpResponse` containing the response data.

    Raises:
      HttpError: On non-retryable HTTP errors or after exhausting all
          retry attempts.
      ValueError: If both *data* and *json_body* are provided.
    """
    with self._open_stream(
        url, method, headers, data, json_body, timeout, max_retries
    ) as resp:
      stream = _maybe_decompress(resp)
      body = stream.read()
      encoding = resp.headers.get_content_charset() or DEFAULT_CHARSET
      return HttpResponse(
          data=body,
          status_code=resp.status,
          headers=dict(resp.headers),
          url=resp.url,
          encoding=encoding,
      )

  def fetch_json(self, url: str, **kwargs) -> Any:
    """Fetch a URL and parse the response as JSON.

    Convenience wrapper around `fetch()` that adds an
    `Accept: application/json` header (if not already set) and returns the
    parsed JSON body.

    Args:
      url: URL to fetch.
      **kwargs: Keyword arguments to pass to `fetch()`.

    Returns:
      Parsed JSON (dict, list, str, etc.).

    Raises:
      HttpError: On HTTP or network errors.
      json.JSONDecodeError: If the response body is not valid JSON.
    """
    hdrs = kwargs.pop("headers", None) or {}
    hdrs.setdefault("Accept", "application/json")
    resp = self.fetch(url, headers=hdrs, **kwargs)
    return resp.json()

  def fetch_bytes(self, url: str, **kwargs) -> bytes:
    """Fetch a URL and return the raw response body.

    Convenience wrapper for binary downloads (PDFs, images, archives, etc.).

    Args:
      url: URL to fetch.
      **kwargs: Keyword arguments to pass to `fetch()`.

    Returns:
      Raw response bytes.

    Raises:
      HttpError: On HTTP or network errors.
    """
    return self.fetch(url, **kwargs).data

  def fetch_text(self, url: str, **kwargs) -> str:
    """Fetch a URL and return the response body as a decoded string.

    Convenience wrapper for text-based APIs (XML, TSV, plain text).

    Args:
      url: URL to fetch.
      **kwargs: Keyword arguments to pass to `fetch()`.

    Returns:
      Response body decoded using the charset from Content-Type.

    Raises:
      HttpError: On HTTP or network errors.
    """
    return self.fetch(url, **kwargs).text

  @contextlib.contextmanager
  def _open_stream(
      self,
      url: str,
      method: str,
      headers: dict[str, str] | None,
      data: bytes | None,
      json_body: Any | None,
      timeout: float | None,
      max_retries: int | None = None,
  ) -> Iterator[http.client.HTTPResponse]:
    """Open an HTTP response with rate limiting and retries (internal).

    Handles argument validation, rate limiting, request dispatch, and
    error checking.  Yields the raw `http.client.HTTPResponse` and
    guarantees `response.close()` on exit.

    The **connection phase** (before any data flows) is retried on
    transient errors (429, 5xx) with the same backoff logic as
    `fetch()`.  Once a 2xx response is yielded, no further retries
    are attempted — streaming data is not idempotently resumable.

    On **2xx responses** that include an `X-Throttling-Control`
    header, proactive backpressure is applied so the next request
    is delayed before hitting a hard limit.

    Args:
      url: Request URL.
      method: HTTP method.
      headers: Extra HTTP headers.
      data: Raw request body bytes.
      json_body: JSON-serializable request body.
      timeout: Per-request timeout override.
      max_retries: Override for maximum connection retry attempts.

    Yields:
      An open `http.client.HTTPResponse` ready for streaming reads.

    Raises:
      HttpError: On HTTP errors (non-2xx status) or network errors.
      ValueError: If both *data* and *json_body* are provided.
    """
    if data is not None and json_body is not None:
      raise ValueError("Cannot specify both 'data' and 'json_body'.")

    url = self._resolve_url(url)
    display_url = redact_url(url) or url

    effective_timeout = timeout if timeout is not None else self.timeout
    effective_retries = (
        max_retries if max_retries is not None else self.max_retries
    )

    last_exc: Exception | None = None
    next_min_sleep = 0.0
    for attempt in range(effective_retries + 1):
      current_min_sleep = max(next_min_sleep, self._next_min_sleep)
      self._limiter.wait(min_sleep=current_min_sleep)
      self._next_min_sleep = 0.0
      req = self._build_request(url, method, headers, data, json_body)

      try:
        if self._proxy_opener is None:
          proxy_url = (
              os.environ.get("SCIENCE_PROXY")
              or os.environ.get("HTTPS_PROXY")
              or os.environ.get("HTTP_PROXY")
          )
          if proxy_url:
            proxy_handler = urllib.request.ProxyHandler({'http': proxy_url, 'https': proxy_url})
            self._proxy_opener = urllib.request.build_opener(proxy_handler)
          else:
            self._proxy_opener = urllib.request.build_opener()
        response = self._proxy_opener.open(req, timeout=effective_timeout)
      except urllib.error.HTTPError as exc:
        status = exc.code
        error_body = exc.read()
        retry_after = _parse_retry_after(exc.headers)
        exc.close()

        if (
            status in self.retryable_status_codes
            and attempt < effective_retries
        ):
          next_min_sleep = self._compute_backoff(attempt, retry_after)
          logging.info(
              "HttpClient[%s]: HTTP %d from %s — retrying in ≥%.1fs"
              " (attempt %d/%d)",
              self.hostname,
              status,
              display_url,
              next_min_sleep,
              attempt + 1,
              effective_retries + 1,
          )
          last_exc = HttpError(
              f"HTTP Error {status} while fetching {display_url}",
              status_code=status,
              body=error_body,
              url=display_url,
          )
          continue

        hint = ""
        if status == 403:
          hint = (
              f" (Hint: this may be caused by the User-Agent"
              f" '{self.user_agent}'. Override it by setting the environment"
              f" variable SCIENCE_SKILLS_USER_AGENT, e.g.:"
              f' SCIENCE_SKILLS_USER_AGENT="<enter_your_custom_user_agent>"'
              f" python3 script.py ...)"
          )
        raise HttpError(
            f"HTTP Error {status} while fetching {display_url}{hint}",
            status_code=status,
            body=error_body,
            url=display_url,
        ) from exc
      except (urllib.error.URLError, OSError) as exc:
        if attempt < effective_retries:
          next_min_sleep = self._compute_backoff(attempt)
          logging.info(
              "HttpClient[%s]: Network error (%s) — retrying in ≥%.1fs"
              " (attempt %d/%d)",
              self.hostname,
              redact_sensitive_text(str(exc)),
              next_min_sleep,
              attempt + 1,
              effective_retries + 1,
          )
          last_exc = exc
          continue

        hint = "\n(Hint / 提示：连接数据库失败或拒绝连接。默认 china profile 已启用；如仍失败，可能是网络受限、代理不可用或远端服务限制。技术用户可配置 SCIENCE_PROXY、HTTPS_PROXY 或 HTTP_PROXY 后重试。)"
        raise HttpError(
            f"Network error fetching {display_url}: "
            f"{redact_sensitive_text(str(exc))}{hint}",
            url=display_url,
        ) from exc

      # 2xx success.
      throttle_delay = _parse_throttle_control(response.headers)
      if throttle_delay > 0:
        logging.info(
            "HttpClient[%s]: X-Throttling-Control backpressure %.1fs from %s",
            self.hostname,
            throttle_delay,
            display_url,
        )
        self._next_min_sleep = throttle_delay

      try:
        yield response
      finally:
        response.close()
      return

    # Should not be reachable.
    raise HttpError(
        f"Max retries ({effective_retries}) exceeded for {display_url}",
        url=display_url,
    ) from last_exc

  def stream_lines(
      self,
      url: str,
      *,
      method: str = "GET",
      headers: dict[str, str] | None = None,
      data: bytes | None = None,
      json_body: Any | None = None,
      timeout: float | None = None,
      max_retries: int | None = None,
  ) -> Iterator[str]:
    """Stream an HTTP response line-by-line without buffering.

    Useful for large result sets (e.g. UniProt `/stream` which can
    return up to 10M lines).  The response is streamed via
    `urllib.request` with automatic gzip decompression.

    Rate-limits before each attempt.  The **connection phase** is
    retried on transient errors (429, 5xx), but once data starts
    streaming, no further retries are attempted.

    Args:
      url: Request URL.
      method: HTTP method.
      headers: Extra HTTP headers.
      data: Raw request body bytes (mutually exclusive with *json_body*).
      json_body: JSON-serializable request body.
      timeout: Per-request timeout in seconds (overrides the client default).
        This is the timeout for the initial connection, not for reading
        individual lines.
      max_retries: Override for maximum connection retry attempts.

    Yields:
      Each non-empty line of the response body, decoded as text.

    Raises:
      HttpError: On HTTP errors (non-2xx status).
    """
    with self._open_stream(
        url, method, headers, data, json_body, timeout, max_retries
    ) as response:
      stream = _maybe_decompress(response)
      encoding = response.headers.get_content_charset() or DEFAULT_CHARSET
      for raw_line in stream:
        line = raw_line.decode(encoding).rstrip("\r\n")
        yield line

  def stream_bytes(
      self,
      url: str,
      *,
      method: str = "GET",
      headers: dict[str, str] | None = None,
      data: bytes | None = None,
      json_body: Any | None = None,
      timeout: float | None = None,
      chunk_size: int = 8192,
      max_retries: int | None = None,
  ) -> Iterator[bytes]:
    """Stream an HTTP response as raw byte chunks without buffering.

    Symmetric with `stream_lines` but for binary content (PDFs, archives,
    images, etc.).  Each iteration yields a chunk of up to *chunk_size* bytes.
    Chunks are **transfer-decoded**: if the server applied
    `Content-Encoding: gzip` in transit, the yielded bytes are the
    decompressed content.

    Rate-limits before each attempt.  The **connection phase** is retried on
    transient errors (429, 5xx), but once data starts streaming, no further
    retries are attempted.

    Example:

        with open("paper.pdf", "wb") as f:
            for chunk in client.stream_bytes(url):
                f.write(chunk)

    Args:
      url: Request URL.
      method: HTTP method.
      headers: Extra HTTP headers.
      data: Raw request body bytes (mutually exclusive with *json_body*).
      json_body: JSON-serializable request body.
      timeout: Per-request timeout in seconds (overrides the client default).
        This is the timeout for the initial connection, not for reading
        individual chunks.
      chunk_size: Maximum number of bytes per yielded chunk.
      max_retries: Override for maximum connection retry attempts.

    Yields:
      Non-empty `bytes` chunks of the response body.

    Raises:
      HttpError: On HTTP errors (non-2xx status).
    """
    with self._open_stream(
        url, method, headers, data, json_body, timeout, max_retries
    ) as response:
      stream = _maybe_decompress(response)
      while True:
        chunk = stream.read(chunk_size)
        if not chunk:
          break
        yield chunk

  def fetch_with_fallback(
      self,
      url: str,
      alternatives: list[str] | None = None,
      **kwargs,
  ) -> HttpResponse:
    """Try *url* first, then each URL in *alternatives* on failure.

    Uses fast-fail semantics (max_retries=1, timeout=10s) for the primary
    URL and each alternative so fallback happens quickly.  Only the last
    failure is raised if all URLs fail.

    Callers may override ``max_retries`` and ``timeout`` via *kwargs*;
    the fast-fail defaults only apply when the caller does not specify them.

    Args:
      url: Primary request URL.
      alternatives: List of fallback URLs to try on failure.
      **kwargs: Keyword arguments passed to ``fetch()``.

    Returns:
      ``HttpResponse`` from the first successful URL.

    Raises:
      HttpError: If all URLs fail.
    """
    kwargs.setdefault("max_retries", FAST_FAIL_MAX_RETRIES)
    kwargs.setdefault("timeout", FAST_FAIL_TIMEOUT_SECS)
    urls = [url] + (alternatives or [])
    last_exc: Exception | None = None
    for candidate in urls:
      try:
        return self.fetch(candidate, **kwargs)
      except HttpError as exc:
        last_exc = exc
        logging.info(
            "HttpClient[%s]: fallback candidate %s failed (%s), trying next",
            self.hostname,
            redact_url(candidate),
            redact_sensitive_text(str(exc)),
        )
    raise last_exc  # type: ignore[misc]


def fetch_batch(
    client: HttpClient,
    urls: list[str],
    *,
    max_workers: int = 4,
    **kwargs,
) -> list[HttpResponse | Exception]:
    """Fetch multiple URLs concurrently using a thread pool.

    Respects the client's rate limiter — each thread calls ``client.fetch()``
    which goes through the same ``_RateLimiter``.  Results are returned in
    the same order as *urls*; failures are returned as exceptions (not
    raised).

    Args:
      client: The ``HttpClient`` to use.
      urls: List of URLs to fetch.
      max_workers: Maximum number of concurrent threads.
      **kwargs: Keyword arguments passed to ``client.fetch()``.

    Returns:
      A list of ``HttpResponse`` or ``Exception`` objects, one per URL.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    results: list[HttpResponse | Exception] = [None] * len(urls)  # type: ignore[list-item]
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
      future_to_idx = {
          executor.submit(client.fetch, url, **kwargs): i
          for i, url in enumerate(urls)
      }
      for future in as_completed(future_to_idx):
        idx = future_to_idx[future]
        try:
          results[idx] = future.result()
        except Exception as exc:
          results[idx] = exc
    return results
