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

"""Standard error types for Science Skills.

All skill scripts should raise SkillError subclasses instead of calling sys.exit().
CLI entry points catch SkillError and convert to JSON output with exit code 1.
Agent callers catch SkillError directly for programmatic error handling.
"""

from __future__ import annotations


class SkillError(Exception):
  """Base class for skill execution errors.

  Attributes:
      message: Human-readable error message (Chinese preferred for user-facing)
      code: Machine-readable error code for programmatic handling
      source: Data source or skill name that generated the error
      retryable: Whether the operation can be retried
      retry_after: Seconds to wait before retry (for RateLimitError)
  """
  retryable: bool = False
  retry_after: float | None = None

  def __init__(
      self,
      message: str,
      *,
      code: str = "SKILL_ERROR",
      source: str = "",
  ) -> None:
    self.message = message
    self.code = code
    self.source = source
    super().__init__(message)


class NetworkError(SkillError):
  """Network request failed (timeout, connection refused, DNS failure, etc.)."""
  retryable = True

  def __init__(
      self,
      message: str,
      *,
      status_code: int | None = None,
      source: str = "",
  ) -> None:
    super().__init__(message, code="NETWORK_ERROR", source=source)
    self.status_code = status_code


class QueryError(SkillError):
  """User input or query parameter error.

  Not retryable - user must fix the input.
  """

  def __init__(self, message: str, *, source: str = "") -> None:
    super().__init__(message, code="QUERY_ERROR", source=source)


class RateLimitError(SkillError):
  """Rate limit exceeded.

  Retryable after waiting retry_after seconds.
  """
  retryable = True

  def __init__(
      self,
      message: str,
      *,
      retry_after: float | None = None,
      source: str = "",
  ) -> None:
    super().__init__(message, code="RATE_LIMIT", source=source)
    self.retry_after = retry_after


class DataSourceError(SkillError):
  """Data source returned an error (malformed response, server error, etc.).

  Not retryable with same query - may need to try alternative source.
  """

  def __init__(self, message: str, *, source: str = "") -> None:
    super().__init__(message, code="DATA_SOURCE_ERROR", source=source)


def skill_error_to_dict(exc: SkillError) -> dict[str, str | bool | float | None]:
  """Convert a SkillError to an Agent-parseable dict.

  Example output:
      {
          "status": "error",
          "error_code": "NETWORK_ERROR",
          "message": "PubMed 查询超时",
          "source": "pubmed",
          "retryable": true,
          "retry_after": null,
      }
  """
  return {
      "status": "error",
      "error_code": exc.code,
      "message": exc.message,
      "source": exc.source,
      "retryable": exc.retryable,
      "retry_after": exc.retry_after,
  }
