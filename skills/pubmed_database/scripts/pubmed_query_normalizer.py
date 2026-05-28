# Copyright 2026 Jinxiao Wang
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

"""Rule-based Chinese-to-PubMed query normalization.

This module is intentionally conservative: it covers common Chinese biomedical
phrases and query intents, and falls back to broad English keywords instead of
passing Chinese text directly to PubMed.
"""

from __future__ import annotations

import dataclasses
import datetime
import re

__all__ = ["NormalizedPubMedQuery", "contains_chinese", "normalize_pubmed_query"]


_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


@dataclasses.dataclass(frozen=True)
class NormalizedPubMedQuery:
  original: str
  query: str
  language: str
  changed: bool
  applied_rules: tuple[str, ...] = ()


_TERM_RULES: tuple[tuple[str, str, str], ...] = (
    (
        "非小细胞肺癌",
        '("Carcinoma, Non-Small-Cell Lung"[MeSH Terms] OR '
        '"non-small cell lung cancer"[Title/Abstract] OR NSCLC[Title/Abstract])',
        "non_small_cell_lung_cancer",
    ),
    (
        "肺癌",
        '("Lung Neoplasms"[MeSH Terms] OR "lung cancer"[Title/Abstract] OR '
        '"lung neoplasms"[Title/Abstract])',
        "lung_cancer",
    ),
    (
        "靶向治疗",
        '("Molecular Targeted Therapy"[MeSH Terms] OR '
        '"targeted therapy"[Title/Abstract] OR "targeted therapies"[Title/Abstract])',
        "targeted_therapy",
    ),
    (
        "阿尔茨海默",
        '("Alzheimer Disease"[MeSH Terms] OR "Alzheimer disease"[Title/Abstract])',
        "alzheimer_disease",
    ),
    (
        "乳腺癌",
        '("Breast Neoplasms"[MeSH Terms] OR "breast cancer"[Title/Abstract])',
        "breast_cancer",
    ),
    (
        "糖尿病",
        '("Diabetes Mellitus"[MeSH Terms] OR diabetes[Title/Abstract])',
        "diabetes_mellitus",
    ),
    (
        "免疫治疗",
        '("Immunotherapy"[MeSH Terms] OR immunotherapy[Title/Abstract])',
        "immunotherapy",
    ),
)
_TERM_RULES = tuple(sorted(_TERM_RULES, key=lambda x: len(x[0]), reverse=True))

_PUBLICATION_TYPE_RULES: tuple[tuple[str, str, str], ...] = (
    ("系统综述", '"systematic review"[Publication Type]', "systematic_review"),
    ("meta分析", '"meta-analysis"[Publication Type]', "meta_analysis"),
    ("荟萃分析", '"meta-analysis"[Publication Type]', "meta_analysis"),
    ("临床试验", '"clinical trial"[Publication Type]', "clinical_trial"),
    ("综述", '"review"[Publication Type]', "review"),
)
_PUBLICATION_TYPE_RULES = tuple(sorted(_PUBLICATION_TYPE_RULES, key=lambda x: len(x[0]), reverse=True))

_KEYWORD_FALLBACKS: tuple[tuple[str, str], ...] = (
    ("新", "new"),
    ("最新", "latest"),
    ("治疗", "therapy"),
    ("方向", "direction"),
    ("机制", "mechanism"),
    ("诊断", "diagnosis"),
    ("预后", "prognosis"),
    ("风险", "risk"),
    ("基因", "gene"),
    ("蛋白", "protein"),
)

_STOP_PHRASES = (
    "查一下",
    "查询",
    "查",
    "关于",
    "相关",
    "文献",
    "研究",
    "一下",
    "的",
)

_CHINESE_DIGITS = {
    "一": 1,
    "二": 2,
    "两": 2,
    "三": 3,
    "四": 4,
    "五": 5,
    "六": 6,
    "七": 7,
    "八": 8,
    "九": 9,
    "十": 10,
    "二十": 20,
    "三十": 30,
    "四十": 40,
    "五十": 50,
}


def contains_chinese(text: str) -> bool:
  return bool(_CJK_RE.search(text))


def normalize_pubmed_query(
    query: str,
    *,
    today: datetime.date | None = None,
) -> NormalizedPubMedQuery:
  """Normalize Chinese user input into an English PubMed query.

  English queries are returned unchanged. Chinese queries are converted to
  conservative PubMed syntax using known MeSH terms, publication type filters,
  date ranges, and broad English fallback keywords.
  """
  original = query.strip()
  if not contains_chinese(original):
    return NormalizedPubMedQuery(
        original=original,
        query=original,
        language="en",
        changed=False,
    )

  parts: list[str] = []
  applied: list[str] = []
  matched_phrases: list[str] = []
  matched_char_spans: list[tuple[int, int]] = []

  for phrase, expression, rule_name in _TERM_RULES:
    occurrences = []
    start = 0
    while True:
      idx = original.find(phrase, start)
      if idx == -1:
        break
      occurrences.append((idx, idx + len(phrase)))
      start = idx + 1

    if not occurrences:
      continue

    non_contained = []
    for o_start, o_end in occurrences:
      contained = False
      for m_start, m_end in matched_char_spans:
        if m_start <= o_start and o_end <= m_end:
          contained = True
          break
      if not contained:
        non_contained.append((o_start, o_end))

    if non_contained:
      parts.append(expression)
      applied.append(rule_name)
      matched_phrases.append(phrase)
      matched_char_spans.extend(non_contained)

  for phrase, expression, rule_name in _PUBLICATION_TYPE_RULES:
    phrase_lower = phrase.lower()
    original_lower = original.lower()
    occurrences = []
    start = 0
    while True:
      idx = original_lower.find(phrase_lower, start)
      if idx == -1:
        break
      occurrences.append((idx, idx + len(phrase)))
      start = idx + 1

    if not occurrences:
      continue

    non_contained = []
    for o_start, o_end in occurrences:
      contained = False
      for m_start, m_end in matched_char_spans:
        if m_start <= o_start and o_end <= m_end:
          contained = True
          break
      if not contained:
        non_contained.append((o_start, o_end))

    if non_contained and expression not in parts:
      parts.append(expression)
      applied.append(rule_name)
      matched_phrases.append(phrase)
      matched_char_spans.extend(non_contained)

  if date_filter := _relative_year_filter(original, today=today):
    parts.append(date_filter)
    applied.append("relative_years")

  fallback_terms = _fallback_keywords(original, matched_phrases)
  if fallback_terms:
    parts.append(
        "("
        + " AND ".join(f"{term}[Title/Abstract]" for term in fallback_terms)
        + ")"
    )
    applied.append("keyword_fallback")

  # Extract non-Chinese word tokens and preserve them if they don't overlap with matched rules
  for match in re.finditer(r"[a-zA-Z0-9_\-\*]+", original):
    t_start, t_end = match.span()
    overlaps = False
    for m_start, m_end in matched_char_spans:
      if not (t_end <= m_start or t_start >= m_end):
        overlaps = True
        break
    if not overlaps:
      token = match.group(0)
      parts.append(token)

  if not parts:
    parts.append('"biomedical research"[Title/Abstract]')
    applied.append("generic_biomedical_fallback")

  return NormalizedPubMedQuery(
      original=original,
      query=" AND ".join(parts),
      language="zh",
      changed=True,
      applied_rules=tuple(applied),
  )



def _relative_year_filter(
    text: str,
    *,
    today: datetime.date | None,
) -> str:
  match = re.search(r"最近([一二两三四五六七八九十\d]+)年", text)
  if not match:
    return ""
  years = _parse_chinese_or_ascii_int(match.group(1))
  if years <= 0:
    return ""
  end = today or datetime.date.today()
  start = _subtract_years_safe(end, years)
  return (
      f'"{start:%Y/%m/%d}"[Date - Publication] : '
      f'"{end:%Y/%m/%d}"[Date - Publication]'
  )


def _subtract_years_safe(date_value: datetime.date, years: int) -> datetime.date:
  """Subtract calendar years, mapping leap day to Feb 28 when needed."""
  try:
    return date_value.replace(year=date_value.year - years)
  except ValueError:
    if date_value.month == 2 and date_value.day == 29:
      return date_value.replace(year=date_value.year - years, day=28)
    raise


def _parse_chinese_or_ascii_int(value: str) -> int:
  if value.isdigit():
    return int(value)
  if value == "十":
    return 10
  if value.startswith("十"):
    return 10 + _CHINESE_DIGITS.get(value[1:], 0)
  if value.endswith("十"):
    return _CHINESE_DIGITS.get(value[:-1], 0) * 10
  if "十" in value:
    left, right = value.split("十", 1)
    return _CHINESE_DIGITS.get(left, 1) * 10 + _CHINESE_DIGITS.get(right, 0)
  return _CHINESE_DIGITS.get(value, 0)


def _fallback_keywords(text: str, matched_spans: list[str]) -> list[str]:
  remaining = text
  for phrase in matched_spans + list(_STOP_PHRASES):
    remaining = remaining.replace(phrase, " ")

  terms: list[str] = []
  for phrase, english in _KEYWORD_FALLBACKS:
    if phrase in remaining and english not in terms:
      terms.append(english)
  return terms
