# Contributing to Science Skills

Thanks for your interest in contributing. This document covers the
day-to-day workflow for the open-source Free edition.

**Language**: English (this page) | [简体中文请见底部](#中文简版)

---

## Ground rules

- Be respectful. See `CODE_OF_CONDUCT.md`.
- This project is licensed under Apache-2.0. By contributing, you agree
  that your contributions are licensed under the same terms (Apache-2.0
  inbound = outbound).
- Upstream attribution (Google DeepMind science-skills) must be preserved.
  Do not remove `NOTICE` or upstream license headers in derived files.
- Security issues: do not open a public issue. See `SECURITY.md`.

## What this repo accepts

- Bug fixes in the Free-edition skills (`pubmed_database`, `pdb_database`,
  `science_skills_common`) and tools (`science_doctor.py`,
  `release_check.py`).
- Documentation improvements (English and Chinese), including the bilingual
  README and `docs/`.
- New tests covering existing code paths.
- Improvements to the `default` / `china` network profiles.

## What this repo does **not** accept

- New skills for domains covered by the commercial Pro / Enterprise
  editions (UniProt, AlphaFold, ChEMBL, PubChem, OpenAlex, EuropePMC,
  ClinVar, dbSNP, Ensembl, ClinicalTrials). Adding these would dilute
  the edition boundary. Open a Discussion if you'd like to discuss.
- Changes to the `enterprise` profile (not present in this repo).
- Dify / LangGraph adapter wiring (commercial Enterprise scope).
- Features that bypass third-party database rate limits or licensing.

## Development setup

```powershell
# Clone
git clone https://github.com/<your-username>/science-skills.git
cd science-skills

# Optional: create a virtualenv
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate    # macOS / Linux

# Run the local diagnostic
python tools/science_doctor.py --no-network

# Run the repository sanity check
python tools/release_check.py

# Run tests
python -m pytest tests/
```

## Pull request checklist

1. The PR description states the problem, the fix, and any user-visible
   change.
2. `python tools/release_check.py` returns status `ok`.
3. `python -m pytest tests/` is green.
4. New code follows the surrounding style (2-space indent in Python here).
5. If user-visible behavior changes, both `README.md` and `README.zh-CN.md`
   are updated together — they must stay in sync.
6. If you touched a skill, its `metadata.json` still reflects reality
   (script list, `has_chinese_normalizer`, network sources).
7. No customer package IDs, email addresses, proxy URLs, or API keys
   in any committed file.

## Bilingual documentation

`README.md` (English) and `README.zh-CN.md` (Chinese) must stay
synchronized. A PR that updates one is expected to update the other in
the same commit. The `docs/editions-comparison.md` follows the same rule.

If you only speak one of the two languages, that's fine — submit your
side and explicitly say so in the PR. A maintainer or another contributor
will produce the translation before merge.

---

## 中文简版

欢迎贡献。本节提炼上文要点。

- 本项目采用 Apache-2.0 许可证。提交即表示同意以同样许可证授权。
- 必须保留对上游 `google-deepmind/science-skills` 的署名（`NOTICE`、
  代码许可证头），不可删除。
- 安全问题请按 `SECURITY.md` 私下报告，不要在公开 Issue 中披露。

接受：
- 免费版技能（PubMed、PDB、common）与工具的 Bug 修复；
- 双语文档改进；
- 新增覆盖现有代码的测试；
- `default` / `china` profile 的改进。

不接受：
- 商业版（Pro / 企业版）才包含的技能（UniProt、AlphaFold 等）；
- `enterprise` profile 改动；
- Dify / LangGraph 适配；
- 任何绕过第三方数据库速率限制或授权条款的功能。

PR 自检清单见英文版"Pull request checklist"。中英文 README 必须同步更新。
