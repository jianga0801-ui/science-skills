import importlib.util
import json
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
PDB_SCRIPTS = ROOT / "skills" / "pdb_database" / "scripts"


def _load_script_module(module_name: str):
  path = PDB_SCRIPTS / f"{module_name}.py"
  spec = importlib.util.spec_from_file_location(module_name, path)
  module = importlib.util.module_from_spec(spec)
  sys.modules[module_name] = module
  spec.loader.exec_module(module)
  return module


class PDBChineseQueryTest(unittest.TestCase):

  def setUp(self):
    self._original_modules = dict(sys.modules)

  def tearDown(self):
    # Restore sys.modules to prevent pollution across test methods
    for key in list(sys.modules.keys()):
      if key not in self._original_modules:
        del sys.modules[key]
      else:
        sys.modules[key] = self._original_modules[key]

  def test_free_text_wrapped_as_full_text_json(self):
    normalizer = _load_script_module("pdb_query_normalizer")
    result = normalizer.normalize_pdb_query("人类 胰岛素")
    self.assertTrue(result.changed)
    self.assertEqual(result.language, "zh")
    
    parsed = json.loads(result.query)
    self.assertEqual(parsed["type"], "terminal")
    self.assertEqual(parsed["service"], "full_text")
    self.assertIn("Homo sapiens", parsed["parameters"]["value"])
    self.assertIn("insulin", parsed["parameters"]["value"])

  def test_recursive_json_value_translation(self):
    normalizer = _load_script_module("pdb_query_normalizer")
    structured_query = {
        "type": "group",
        "logical_operator": "and",
        "nodes": [
            {
                "type": "terminal",
                "service": "text",
                "parameters": {"attribute": "rcsb_entity_source_organism.scientific_name", "value": "人类"}
            },
            {
                "type": "terminal",
                "service": "text",
                "parameters": {"attribute": "struct.title", "value": "胰岛素冷冻电镜结构"}
            }
        ]
    }
    query_str = json.dumps(structured_query)
    result = normalizer.normalize_pdb_query(query_str)
    self.assertTrue(result.changed)
    
    parsed = json.loads(result.query)
    self.assertEqual(parsed["nodes"][0]["parameters"]["value"], "Homo sapiens")
    self.assertIn("insulin", parsed["nodes"][1]["parameters"]["value"])
    self.assertIn("ELECTRON MICROSCOPY", parsed["nodes"][1]["parameters"]["value"])

  def test_single_character_human_boundary_protection(self):
    normalizer = _load_script_module("pdb_query_normalizer")
    
    # Standalone "人"
    res1 = normalizer.normalize_pdb_query("人 insulin")
    parsed1 = json.loads(res1.query)
    self.assertIn("Homo sapiens", parsed1["parameters"]["value"])
    
    # Conjunction "大鼠和人"
    res2 = normalizer.normalize_pdb_query("大鼠和人")
    parsed2 = json.loads(res2.query)
    self.assertIn("Rattus norvegicus", parsed2["parameters"]["value"])
    self.assertIn("Homo sapiens", parsed2["parameters"]["value"])

    # False positive "人工" -> should not translate "人" to "Homo sapiens"
    res3 = normalizer.normalize_pdb_query("人工蛋白")
    parsed3 = json.loads(res3.query)
    self.assertNotIn("Homo sapiens", parsed3["parameters"]["value"])

  def test_search_pdb_uses_normalized_query(self):
    search_pdb = _load_script_module("search_pdb")
    captured_urls = []

    def fake_fetch_bytes(url, *args, **kwargs):
      captured_urls.append(url)
      return b'{"total_count": 0}'

    with mock.patch.object(search_pdb.CLIENT, "fetch_bytes", fake_fetch_bytes):
      # Construct fake args
      args = mock.MagicMock()
      args.query = "人类 胰岛素"
      args.return_type = "entry"
      args.count_only = True
      args.output = "fake_output.json"
      args.page_start = None
      args.rows = None
      args.sort_by = None
      args.normalize = False
      
      with mock.patch("builtins.open", mock.mock_open()):
        search_pdb.search_pdb(args)

    self.assertTrue(len(captured_urls) > 0)
    import urllib.parse
    decoded_url = urllib.parse.unquote(captured_urls[0])
    self.assertIn("Homo sapiens", decoded_url)
    self.assertIn("insulin", decoded_url)


  def test_empty_or_whitespace_input(self):
    normalizer = _load_script_module("pdb_query_normalizer")
    res1 = normalizer.normalize_pdb_query("")
    self.assertFalse(res1.changed)
    self.assertEqual(res1.query, "")

    res2 = normalizer.normalize_pdb_query("   ")
    self.assertFalse(res2.changed)
    self.assertEqual(res2.query, "")


if __name__ == "__main__":
  unittest.main()
