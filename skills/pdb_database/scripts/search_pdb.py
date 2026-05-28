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

"""Searches PDB using the RCSB Search API v2.

This script allows executing structured queries against the PDB Search API
with tunable pagination, return types, and sorting.
"""

# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "science-skills-common",
# ]
# [tool.uv.sources]
# science-skills-common = { path = "../../science_skills_common" }
# ///

import argparse
import json
import sys
import urllib.parse

try:
  from science_skills.science_skills_common import http_client
except ModuleNotFoundError:
  import pathlib
  _path = str(pathlib.Path(__file__).resolve().parents[3])
  sys.path.insert(0, _path)
  try:
    from skills.science_skills_common import http_client
  finally:
    if sys.path and sys.path[0] == _path:
      sys.path.pop(0)

try:
  import pdb_query_normalizer
except ModuleNotFoundError:
  import pathlib
  _path = str(pathlib.Path(__file__).resolve().parent)
  sys.path.insert(0, _path)
  try:
    import pdb_query_normalizer
  finally:
    if sys.path and sys.path[0] == _path:
      sys.path.pop(0)

try:
  from science_skills.science_skills_common import errors as _skill_errors
except ModuleNotFoundError:
  import pathlib
  _path = str(pathlib.Path(__file__).resolve().parents[3])
  sys.path.insert(0, _path)
  try:
    from skills.science_skills_common import errors as _skill_errors
  finally:
    if sys.path and sys.path[0] == _path:
      sys.path.pop(0)

NetworkError = _skill_errors.NetworkError
DataSourceError = _skill_errors.DataSourceError
QueryError = _skill_errors.QueryError
SkillError = _skill_errors.SkillError
skill_error_to_dict = _skill_errors.skill_error_to_dict

CLIENT = http_client.HttpClient("https://search.rcsb.org", qps=2.0)


def normalize_pdb_query(query: str) -> dict[str, str | bool | list[str]]:
  """Preview Chinese-to-English PDB query normalization without network I/O."""
  normalized = pdb_query_normalizer.normalize_pdb_query(query)
  return {
      "original_query": normalized.original,
      "normalized_query": normalized.query,
      "language": normalized.language,
      "changed": normalized.changed,
      "applied_rules": list(normalized.applied_rules),
  }


def search_pdb(args: argparse.Namespace):
  """Executes a search against the PDB Search API.

  Args:
    args: parsed command line arguments containing the query and options.
  """
  normalized = pdb_query_normalizer.normalize_pdb_query(args.query)
  query_str = normalized.query
  try:
    parsed_query = json.loads(query_str)
  except json.JSONDecodeError as e:
    raise QueryError(
        f"Error parsing --query as JSON: {e}",
        source="pdb",
    ) from e

  if isinstance(parsed_query, dict) and "query" in parsed_query:
    # Payload already contains "query" key, it's a full request payload
    payload = parsed_query
  else:
    # Only "query" block provided
    payload = {"query": parsed_query}

  if args.return_type is not None:
    payload["return_type"] = args.return_type

  request_options = payload.get("request_options", {})

  if args.count_only:
    # Count-only mode: request 0 rows, just get total_count from response
    request_options["paginate"] = {"start": 0, "rows": 0}
    # Remove return_all_hits if present, since we don't want all results
    request_options.pop("return_all_hits", None)
  elif args.page_start is not None or args.rows is not None:
    # Remove return_all_hits so CLI pagination flags are not silently ignored.
    request_options.pop("return_all_hits", None)
    paginate = request_options.get("paginate", {})
    if args.page_start is not None:
      paginate["start"] = args.page_start
    if args.rows is not None:
      paginate["rows"] = args.rows
    request_options["paginate"] = paginate
  else:
    # Default behavior: return all hits if no pagination is specified
    request_options["return_all_hits"] = True

  if args.sort_by is not None:
    sort_item = {"sort_by": args.sort_by}
    if args.sort_direction is not None:
      sort_item["direction"] = args.sort_direction
    request_options["sort"] = [sort_item]

  if request_options:
    payload["request_options"] = request_options

  json_payload = json.dumps(payload, separators=(",", ":"))
  encoded_query = urllib.parse.quote(json_payload)
  url = f"https://search.rcsb.org/rcsbsearch/v2/query?json={encoded_query}"

  print(f"Querying PDB Search API from {url}...", file=sys.stderr)

  content = CLIENT.fetch_bytes(url)
  if args.count_only:
    # Parse the response to extract just the total count
    response_data = json.loads(content.decode("utf-8"))
    total_count = response_data.get("total_count", 0)
    count_result = {"total_count": total_count}
    print(f"Total count: {total_count}", file=sys.stderr)
    with open(args.output, "w") as f:
      json.dump(count_result, f, indent=2)
  else:
    with open(args.output, "w") as f:
      f.write(content.decode("utf-8"))


def parse_args() -> argparse.Namespace:
  """Parse command line arguments."""
  parser = argparse.ArgumentParser(
      description="Search PDB using the RCSB Search API v2"
  )
  parser.add_argument(
      "--query",
      type=str,
      required=True,
      help="JSON string of the query object or full request payload",
  )
  parser.add_argument(
      "--return_type",
      type=str,
      choices=[
          "entry",
          "assembly",
          "polymer_entity",
          "non_polymer_entity",
          "polymer_instance",
          "mol_definition",
      ],
      help=(
          "Type of returned object."
          "entry = [PDB ID]"
          "assembly = [PDB ID]-[ASSEMBLY ID]"
          "polymer_entity = [PDB ID]-[ENTITY ID]"
          "non_polymer_entity = [PDB ID]-[ENTITY ID]"
          "polymer_instance = [PDB ID].[LABEL ASYM ID]"
          "mol_definition = [CHEMICAL COMP ID] or [BIRD ID]"
      ),
  )
  parser.add_argument(
      "--sort_by",
      type=str,
      help=(
          "Attribute to sort by (commonly score or "
          "rcsb_accession_info.initial_release_date)"
      ),
  )
  parser.add_argument(
      "--sort_direction",
      type=str,
      choices=["asc", "desc"],
      help="Sort direction (used with --sort_by)",
  )
  parser.add_argument(
      "--page_start",
      type=int,
      help="Start index for pagination",
  )
  parser.add_argument(
      "--rows",
      type=int,
      help="Number of rows to return",
  )
  parser.add_argument(
      "--count-only",
      action="store_true",
      help=(
          "Return only the total count of matching entries, not the full"
          " result list. Useful when you need to know how many results match"
          " without downloading them all."
      ),
  )
  parser.add_argument(
      "--output",
      type=str,
      help="File to write the output to",
  )
  parser.add_argument(
      "--normalize",
      action="store_true",
      help="Preview Chinese-to-English PDB query normalization",
  )

  parsed_args = parser.parse_args()
  if not parsed_args.normalize:
    if not parsed_args.return_type:
      parser.error("the following arguments are required: --return_type")
    if not parsed_args.output:
      parser.error("the following arguments are required: --output")
  return parsed_args


if __name__ == "__main__":
  try:
    main_args = parse_args()
    if main_args.normalize:
      preview = normalize_pdb_query(main_args.query)
      print(json.dumps(preview, indent=2))
    else:
      search_pdb(main_args)
  except SkillError as e:
    print(json.dumps(skill_error_to_dict(e), ensure_ascii=False), file=sys.stderr)
    sys.exit(1)
