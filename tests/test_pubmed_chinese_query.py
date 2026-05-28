import datetime
import importlib.util
import pathlib
import sys
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[1]
PUBMED_SCRIPTS = ROOT / "skills" / "pubmed_database" / "scripts"


def _load_script_module(module_name: str):
  path = PUBMED_SCRIPTS / f"{module_name}.py"
  spec = importlib.util.spec_from_file_location(module_name, path)
  module = importlib.util.module_from_spec(spec)
  sys.modules[module_name] = module
  spec.loader.exec_module(module)
  return module


class PubMedChineseQueryTest(unittest.TestCase):
  def setUp(self):
    self._original_modules = dict(sys.modules)

  def tearDown(self):
    # Restore sys.modules to prevent pollution across test methods
    for key in list(sys.modules.keys()):
      if key not in self._original_modules:
        del sys.modules[key]
      else:
        sys.modules[key] = self._original_modules[key]

  def test_normalizes_chinese_review_query_to_english_pubmed_query(self):
    normalizer = _load_script_module("pubmed_query_normalizer")

    result = normalizer.normalize_pubmed_query(
        "查一下肺癌靶向治疗最近五年的综述",
        today=datetime.date(2026, 5, 25),
    )

    self.assertTrue(result.changed)
    self.assertEqual(result.language, "zh")
    self.assertNotRegex(result.query, r"[\u4e00-\u9fff]")
    self.assertIn('"Lung Neoplasms"[MeSH Terms]', result.query)
    self.assertIn('"Molecular Targeted Therapy"[MeSH Terms]', result.query)
    self.assertIn('"review"[Publication Type]', result.query)
    self.assertIn('"2021/05/25"[Date - Publication]', result.query)
    self.assertIn('"2026/05/25"[Date - Publication]', result.query)

  def test_relative_year_filter_handles_leap_day(self):
    normalizer = _load_script_module("pubmed_query_normalizer")

    result = normalizer.normalize_pubmed_query(
        "肺癌 最近一年",
        today=datetime.date(2024, 2, 29),
    )

    self.assertIn('"2023/02/28"[Date - Publication]', result.query)
    self.assertIn('"2024/02/29"[Date - Publication]', result.query)

  def test_english_query_is_left_unchanged(self):
    normalizer = _load_script_module("pubmed_query_normalizer")

    result = normalizer.normalize_pubmed_query("BRCA1 breast cancer")

    self.assertFalse(result.changed)
    self.assertEqual(result.query, "BRCA1 breast cancer")

  def test_unknown_chinese_query_returns_keyword_fallback_without_chinese(self):
    normalizer = _load_script_module("pubmed_query_normalizer")

    result = normalizer.normalize_pubmed_query("查一下新的治疗方向")

    self.assertTrue(result.changed)
    self.assertNotRegex(result.query, r"[\u4e00-\u9fff]")
    self.assertIn("new", result.query)
    self.assertIn("therapy", result.query)

  def test_search_pubmed_uses_normalized_query_before_api_call(self):
    pubmed_api = _load_script_module("pubmed_api")
    captured = {}

    def fake_get(url, params=None, **kwargs):
      captured["term"] = params["term"]
      return {"esearchresult": {"idlist": ["123"]}}

    with mock.patch.object(pubmed_api, "_get", fake_get):
      result = pubmed_api.search_pubmed("肺癌 靶向治疗", max_results=1)

    self.assertEqual(result, ["123"])
    self.assertNotRegex(captured["term"], r"[\u4e00-\u9fff]")
    self.assertIn('"Lung Neoplasms"[MeSH Terms]', captured["term"])

  def test_pubmed_api_exposes_normalization_preview(self):
    pubmed_api = _load_script_module("pubmed_api")

    result = pubmed_api.normalize_pubmed_query("肺癌 靶向治疗")

    self.assertEqual(result["language"], "zh")
    self.assertTrue(result["changed"])
    self.assertIn("normalized_query", result)
    self.assertNotRegex(result["normalized_query"], r"[\u4e00-\u9fff]")

  def test_overlapping_term_rules_does_not_produce_redundant_and(self):
    normalizer = _load_script_module("pubmed_query_normalizer")
    result = normalizer.normalize_pubmed_query("非小细胞肺癌")
    self.assertTrue(result.changed)
    self.assertIn("Carcinoma, Non-Small-Cell Lung", result.query)
    self.assertNotIn("Lung Neoplasms", result.query)

  def test_overlapping_publication_type_rules_does_not_produce_redundant_pub_types(self):
    normalizer = _load_script_module("pubmed_query_normalizer")
    result = normalizer.normalize_pubmed_query("系统综述")
    self.assertTrue(result.changed)
    self.assertIn('"systematic review"[Publication Type]', result.query)
    self.assertNotIn('"review"[Publication Type]', result.query)

  def test_mixed_chinese_english_query_preserves_english_tokens(self):
    normalizer = _load_script_module("pubmed_query_normalizer")
    result = normalizer.normalize_pubmed_query("肺癌 BRCA1 treatment")
    self.assertTrue(result.changed)
    self.assertIn('"Lung Neoplasms"[MeSH Terms]', result.query)
    self.assertIn("BRCA1", result.query)
    self.assertIn("treatment", result.query)

  def test_mixed_query_with_overlapping_english_word_extracted_from_rule_phrase(self):
    normalizer = _load_script_module("pubmed_query_normalizer")
    result = normalizer.normalize_pubmed_query("meta分析 BRCA1")
    self.assertTrue(result.changed)
    self.assertIn('"meta-analysis"[Publication Type]', result.query)
    self.assertIn("BRCA1", result.query)
    # "meta" is a substring of "meta分析", which is matched, so it should NOT be extracted as a separate English token.
    # We verify this by asserting "meta" is not in the parts as a plain word token (it only appears inside the publication type expression).
    self.assertNotIn(" AND meta AND ", f" {result.query} ")

  def test_empty_or_whitespace_input_handling(self):
    normalizer = _load_script_module("pubmed_query_normalizer")
    result_empty = normalizer.normalize_pubmed_query("")
    self.assertFalse(result_empty.changed)
    self.assertEqual(result_empty.query, "")

    result_whitespace = normalizer.normalize_pubmed_query("   ")
    self.assertFalse(result_whitespace.changed)
    self.assertEqual(result_whitespace.query, "")

  def test_keyword_fallback_with_term_rule(self):
    normalizer = _load_script_module("pubmed_query_normalizer")
    result = normalizer.normalize_pubmed_query("肺癌最新的治疗方向")
    self.assertTrue(result.changed)
    self.assertIn('"Lung Neoplasms"[MeSH Terms]', result.query)
    self.assertIn("latest[Title/Abstract]", result.query)
    self.assertIn("therapy[Title/Abstract]", result.query)
    self.assertIn("direction[Title/Abstract]", result.query)


if __name__ == "__main__":
  unittest.main()


