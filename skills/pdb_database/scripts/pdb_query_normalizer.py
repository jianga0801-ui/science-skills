"""Rule-based Chinese-to-PDB query normalization.

Translates common Chinese biological terms, organism names, and experimental
methods into standard PDB names, and supports recursive JSON-walking for structured
PDB queries or wrapping free-text into full_text PDB query JSONs.
"""

from __future__ import annotations

import dataclasses
import json
import re
from typing import Any

__all__ = ["NormalizedPDBQuery", "contains_chinese", "normalize_pdb_query"]

_CJK_RE = re.compile(r"[\u4e00-\u9fff]")


@dataclasses.dataclass(frozen=True)
class NormalizedPDBQuery:
  original: str
  query: str
  language: str
  changed: bool
  applied_rules: tuple[str, ...] = ()


# Standard organism names in PDB
_ORGANISM_RULES: tuple[tuple[str, str, str], ...] = (
    ("秀丽隐杆线虫", "Caenorhabditis elegans", "organism_celegans"),
    ("新型冠状病毒", "Severe acute respiratory syndrome coronavirus 2", "organism_sars_cov_2"),
    ("新冠病毒", "Severe acute respiratory syndrome coronavirus 2", "organism_sars_cov_2"),
    ("大肠杆菌", "Escherichia coli", "organism_ecoli"),
    ("酿酒酵母", "Saccharomyces cerevisiae", "organism_yeast"),
    ("黑腹果蝇", "Drosophila melanogaster", "organism_drosophila"),
    ("拟南芥", "Arabidopsis thaliana", "organism_arabidopsis"),
    ("小白鼠", "Mus musculus", "organism_mouse"),
    ("小老鼠", "Mus musculus", "organism_mouse"),
    ("大白鼠", "Rattus norvegicus", "organism_rat"),
    ("大老鼠", "Rattus norvegicus", "organism_rat"),
    ("人类", "Homo sapiens", "organism_human"),
    ("斑马鱼", "Danio rerio", "organism_zebrafish"),
    ("果蝇", "Drosophila melanogaster", "organism_drosophila"),
    ("酵母", "Saccharomyces cerevisiae", "organism_yeast"),
    ("小鼠", "Mus musculus", "organism_mouse"),
    ("大鼠", "Rattus norvegicus", "organism_rat"),
    ("线虫", "Caenorhabditis elegans", "organism_celegans"),
    ("新冠", "Severe acute respiratory syndrome coronavirus 2", "organism_sars_cov_2"),
    ("人", "Homo sapiens", "organism_human"),
)

# Common proteins, assemblies, methods
_BIOLOGICAL_RULES: tuple[tuple[str, str, str], ...] = (
    ("晶体衍射", "X-RAY DIFFRACTION", "method_xray"),
    ("X射线衍射", "X-RAY DIFFRACTION", "method_xray"),
    ("核磁共振", "NMR", "method_nmr"),
    ("冷冻电镜", "ELECTRON MICROSCOPY", "method_em"),
    ("刺突蛋白", "spike protein", "protein_spike"),
    ("主蛋白酶", "main protease", "protein_mpro"),
    ("免疫球蛋白", "immunoglobulin", "protein_immunoglobulin"),
    ("绿色荧光蛋白", "gfp", "protein_gfp"),
    ("血红蛋白", "hemoglobin", "protein_hemoglobin"),
    ("胶原蛋白", "collagen", "protein_collagen"),
    ("胰岛素", "insulin", "protein_insulin"),
    ("干扰素", "interferon", "protein_interferon"),
    ("激酶", "kinase", "protein_kinase"),
    ("受体", "receptor", "protein_receptor"),
    ("配体", "ligand", "protein_ligand"),
    ("抗体", "immunoglobulin", "protein_immunoglobulin"),
    ("复合物", "complex", "protein_complex"),
)

_REVIEWED_RULES: tuple[tuple[str, str, str], ...] = ()

_ALL_RULES: tuple[tuple[str, str, str], ...] = tuple(
    sorted(
        _ORGANISM_RULES + _BIOLOGICAL_RULES,
        key=lambda x: len(x[0]),
        reverse=True,
    )
)

_STOP_PHRASES = (
    "查一下",
    "查询",
    "关于",
    "相关",
    "蛋白",
    "基因",
    "序列",
    "文献",
    "一下",
    "的",
    "三维结构",
    "晶体结构",
)

_KEYWORD_FALLBACKS: tuple[tuple[str, str], ...] = (
    ("结构", "structure"),
    ("突变", "mutation"),
    ("变异", "mutation"),
    ("相互作用", "interaction"),
    ("互作", "interaction"),
    ("分辨率", "resolution"),
)


def contains_chinese(text: str) -> bool:
  return bool(_CJK_RE.search(text))


def _translate_text(text: str) -> str:
  """Translates a CJK-containing string using rules and preserves English words."""
  original = text.strip()
  parts: list[str] = []
  matched_phrases: list[str] = []
  matched_char_spans: list[tuple[int, int]] = []

  for phrase, expression, _ in _ALL_RULES:
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
      # Boundary protection for "人"
      if phrase == "人":
        if o_start > 0:
          prev_char = original[o_start - 1]
          if _CJK_RE.match(prev_char) and prev_char not in ("和", "与", "或", "及"):
            char_covered = False
            for m_start, m_end in matched_char_spans:
              if m_start <= (o_start - 1) < m_end:
                char_covered = True
                break
            if not char_covered:
              continue
        if o_end < len(original):
          next_char = original[o_end]
          if _CJK_RE.match(next_char) and next_char not in ("和", "与", "或", "及", "的"):
            char_covered = False
            for m_start, m_end in matched_char_spans:
              if m_start <= o_end < m_end:
                char_covered = True
                break
            if not char_covered:
              continue

      contained = False
      for m_start, m_end in matched_char_spans:
        if m_start <= o_start and o_end <= m_end:
          contained = True
          break
      if not contained:
        non_contained.append((o_start, o_end))

    if non_contained and expression not in parts:
      parts.append(expression)
      matched_phrases.append(phrase)
      matched_char_spans.extend(non_contained)

  # Check fallbacks
  fallback_terms = _fallback_keywords(original, matched_phrases)
  for term in fallback_terms:
    if term not in parts:
      parts.append(term)

  # Extract non-Chinese word tokens
  for match in re.finditer(r"[a-zA-Z0-9_\-\*\:]+", original):
    t_start, t_end = match.span()
    overlaps = False
    for m_start, m_end in matched_char_spans:
      if not (t_end <= m_start or t_start >= m_end):
        overlaps = True
        break
    if not overlaps:
      token = match.group(0)
      if token.upper() not in ("AND", "OR", "NOT") and token not in parts:
        parts.append(token)

  if not parts:
    parts.append("protein")

  return " ".join(parts)


def _fallback_keywords(text: str, matched_spans: list[str]) -> list[str]:
  remaining = text
  for phrase in matched_spans + list(_STOP_PHRASES):
    remaining = remaining.replace(phrase, " ")

  terms: list[str] = []
  for phrase, english in _KEYWORD_FALLBACKS:
    if phrase in remaining and english not in terms:
      terms.append(english)
  return terms


def _normalize_json_node(node: Any) -> Any:
  """Recursively walks a JSON query tree and translates Chinese value leaves."""
  if isinstance(node, dict):
    new_dict = {}
    for k, v in node.items():
      if k == "value" and isinstance(v, str) and contains_chinese(v):
        new_dict[k] = _translate_text(v)
      else:
        new_dict[k] = _normalize_json_node(v)
    return new_dict
  elif isinstance(node, list):
    return [_normalize_json_node(item) for item in node]
  return node


def normalize_pdb_query(query: str) -> NormalizedPDBQuery:
  """Normalize Chinese PDB query (structured JSON or free-text) into English.

  English queries are returned unchanged. Chinese queries are parsed as JSON
  and recursively normalized, or wrapped as a full_text PDB query JSON.
  """
  original = query.strip()
  if "\\u" in original:
    try:
      original = original.encode("utf-8").decode("unicode_escape")
    except ValueError:
      pass

  if not contains_chinese(original):
    return NormalizedPDBQuery(
        original=original,
        query=original,
        language="en",
        changed=False,
    )

  try:
    # Try parsing as structured PDB JSON query first
    parsed = json.loads(original)
    normalized_obj = _normalize_json_node(parsed)
    normalized_str = json.dumps(normalized_obj, separators=(",", ":"))
    return NormalizedPDBQuery(
        original=original,
        query=normalized_str,
        language="zh",
        changed=True,
        applied_rules=("structured_json_translation",),
    )
  except json.JSONDecodeError:
    # Treat as free-text query and wrap in PDB full_text query schema
    translated_text = _translate_text(original)
    full_text_query = {
        "type": "terminal",
        "service": "full_text",
        "parameters": {"value": translated_text},
    }
    normalized_str = json.dumps(full_text_query, separators=(",", ":"))
    return NormalizedPDBQuery(
        original=original,
        query=normalized_str,
        language="zh",
        changed=True,
        applied_rules=("free_text_wrapping",),
    )
