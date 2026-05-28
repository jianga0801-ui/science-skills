# Science Skills（开源免费版）

> 面向科研数据库工作流的开源 Agent 技能包，内置国内网络感知、中文查询归一化与本地诊断工具。

**语言**：[English](README.md) | 简体中文（本页）

[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-green.svg)](CHANGELOG.md)
[![Editions](https://img.shields.io/badge/版本-免费%20%7C%20Pro%20%7C%20企业-orange.svg)](docs/editions-comparison.md)

Science Skills 是一个开源的 Agent "技能"集合，让 AI 编程或科研助手（Claude Code、Codex、Cursor 等）能够以**更可靠、对中国大陆网络更友好**的方式去查询主流科研数据库 —— 本免费版覆盖 PubMed 与 RCSB PDB。

它**不**替代上游数据库本身。它提供的是本地的 Agent 指令、脚本、网络 profile、诊断工具与元数据，让 Agent 在调用这些数据库时更安全、更一致，并保留正确的署名信息。

本免费版（Free）是该项目的开源基线。商业 **Pro** 版与 **Enterprise**（企业）版在此之上扩展了更多数据库、更多 profile 与配套支持 —— 详见 [docs/editions-comparison.md](docs/editions-comparison.md)。

---

## 目录

1. [免费版包含哪些内容](#免费版包含哪些内容)
2. [安装](#安装)
3. [快速开始](#快速开始)
4. [网络 Profile](#网络-profile)
5. [可选代理](#可选代理)
6. [Science Doctor 本地体检](#science-doctor-本地体检)
7. [版本对比：免费 / Pro / 企业](#版本对比免费--pro--企业)
8. [Agent 兼容性](#agent-兼容性)
9. [第三方数据库使用条款](#第三方数据库使用条款)
10. [上游署名](#上游署名)
11. [参与贡献](#参与贡献)
12. [许可证](#许可证)
13. [免责声明](#免责声明)

---

## 免费版包含哪些内容

| 组件 | 具体内容 |
|---|---|
| 技能（Skills） | `pubmed_database`、`pdb_database`、`science_skills_common`（共享 HTTP 客户端） |
| 网络 Profile | `china`（**内置默认值**，国内优化镜像，覆盖选定下载场景）、`default`（官方源优先，需手动切换） |
| 适配器（Adapters） | Codex、Claude Code、Cursor |
| 工具 | `science_doctor.py`（本地体检）、`release_check.py`（仓库自检） |
| 中文查询归一化 | PubMed、PDB |

免费版定位轻量。商业 Pro 版在此基础上增加 UniProt、AlphaFold、ChEMBL、PubChem、OpenAlex / EuropePMC、ClinVar、dbSNP、Ensembl、ClinicalTrials 等技能 —— 详见 [editions-comparison.md](docs/editions-comparison.md)。

---

## 安装

1. 将本目录复制到您的 Agent 技能 / 插件位置：
   - **Claude Code（CLI 插件）**：放到 `~/.claude/plugins/`（Windows：`%USERPROFILE%\.claude\plugins\`）。
   - **Codex / Cursor**：参照各自客户端文档中本地技能的路径。
2. 重启 AI 终端，使其加载新技能。

完成。默认网络 profile 为 `china`，中国大陆用户无需额外配置即可获得合理默认值。

如果运行有异常，先跑本地体检：

```powershell
python tools/science_doctor.py
```

可根据本地 Python 安装情况使用 `python`、`py` 或 `python3`。主要支持 Windows PowerShell，同时兼容 macOS / Linux / Git Bash。

完整安装步骤参见 [docs/install-guide.md](docs/install-guide.md)。

---

## 快速开始

预览中文问题如何转成 PubMed 查询（不发起任何网络请求）：

```powershell
python skills/pubmed_database/scripts/pubmed_api.py normalize --query "<您的中文生物医学问题>"
```

预览 PDB 结构检索：

```powershell
python skills/pdb_database/scripts/pdb_query_normalizer.py --query "<您的中文结构生物学问题>"
```

工作流调用第三方数据库时，请在下游笔记和报告中**保留原始标识符**（PMID、DOI、PDB ID 等）—— 这是上游引用和署名的基础。

---

## 网络 Profile

Science Skills 把 API 访问和文件下载镜像分开管理。Profile 决定使用哪些镜像、哪种客户端行为。

| Profile | 作用 |
|---|---|
| `china`（**内置默认值**） | 国内优化：API 查询仍走官方源，选定的大文件下载（如 PDB 坐标）走 PDBJ 等镜像；代理可见性诊断更严格。中国大陆用户开箱即用，无需任何配置。 |
| `default` | 官方源优先，适合海外或畅通网络环境。需手动设置 `SCIENCE_NETWORK_PROFILE=default` 启用。 |

如需覆盖，设置环境变量。PowerShell：

```powershell
$env:SCIENCE_NETWORK_PROFILE = "default"
```

macOS / Linux / Git Bash：

```bash
export SCIENCE_NETWORK_PROFILE="default"
```

第三个 profile `enterprise`（私有镜像、内网终点）仅在商业企业版中提供。

---

## 可选代理

代理配置是**可选的**。HTTP 客户端依次检查 `SCIENCE_PROXY`、`HTTPS_PROXY`、`HTTP_PROXY`。

PowerShell：

```powershell
$env:SCIENCE_PROXY = "http://127.0.0.1:7890"
```

macOS / Linux / Git Bash：

```bash
export SCIENCE_PROXY="http://127.0.0.1:7890"
```

请勿在聊天、文档或日志中粘贴含凭证的私有代理。Science Doctor 只报告"是否配置"，绝不打印代理值。

---

## Science Doctor 本地体检

本地诊断工具，输出 Python / `uv` 版本、当前网络 profile、技能包状态、`.env` 存在性、代理配置状态、临时锁文件可写性，以及（可选）PubMed / PDB 连通性探测。

仅本地：

```powershell
python tools/science_doctor.py --no-network
```

含网络探测：

```powershell
python tools/science_doctor.py
```

该工具**不读取 `.env` 内容**、**不打印任何密钥或代理值**。

---

## 版本对比：免费 / Pro / 企业

| 维度 | **免费版**（开源，本仓库） | **Pro 版**（商业） | **企业版**（商业） |
|---|---|---|---|
| 许可证 | Apache-2.0 | 商业 EULA | 商业合同 |
| 适用对象 | 学生、个人科研者、试用评估 | 独立科研人员、课题组、小型实验室 | 高校、企业研发部门、研究机构 |
| 技能覆盖 | PubMed、PDB + 公共组件 | + UniProt、AlphaFold、ChEMBL、PubChem、OpenAlex、EuropePMC、ClinVar、dbSNP、Ensembl、ClinicalTrials | Pro 全部技能 + 最广商业技能集 |
| 中文查询归一化 | PubMed、PDB | 商业技能全覆盖 | 同 Pro + 自定义术语映射 |
| 网络 Profile | `default`、`china` | `default`、`china` | `default`、`china`、`enterprise`（私有镜像 / 内网终点） |
| Agent 适配器 | Codex / Claude Code / Cursor | Codex / Claude Code / Cursor | + Dify / LangGraph |
| Science Doctor | ✅ | ✅ | ✅（含企业扩展） |
| 技术支持 | 社区尽力（Issues / Discussions） | 邮件，约 72 小时响应 | 专属通道，约 24 小时响应 |
| 更新服务 | 开源版本发布节奏 | 自购买起 12 个月内更新 | 合同期内持续更新 |
| 客户专属包编号 | 无 | 每份授权唯一 | 每机构唯一，可管理子账号 |

完整中英文对比与商业咨询入口：[docs/editions-comparison.md](docs/editions-comparison.md)。

---

## Agent 兼容性

免费版包含以下适配器：

- **Codex** —— 见 `adapters/codex/`
- **Claude Code** —— 见 `adapters/claude-code/`
- **Cursor** —— 见 `adapters/cursor/`

每个适配器目录提供对应 Agent 的清单文件。技能本体是 Agent 无关的 Markdown + Python。

---

## 第三方数据库使用条款

Science Skills 仅提供自动化工具，**不拥有**任何第三方数据库的内容版权。您在使用本工具访问任何数据库时，需自行遵守该数据库的使用条款、速率限制、账号政策、引用要求与商业使用限制。

要点速查：

| 数据源 | 匿名速率限制 | 备注 |
|---|---|---|
| NCBI / PubMed | 3 req/s | 配置 `NCBI_API_KEY` 可提升到 10 req/s；同一 Key 最多 3 个并发连接。 |
| RCSB PDB | 无法律限制（CC0） | 出版物中按社区惯例引用 PDB ID。 |

完整矩阵：[docs/inventory/data-source-license-matrix.md](docs/inventory/data-source-license-matrix.md)。

**严禁**使用本工具绕过任何第三方速率限制或授权条款。

---

## 上游署名

本项目派生自 [google-deepmind/science-skills](https://github.com/google-deepmind/science-skills)。

- 派生自上游的**代码**部分受 [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0) 约束。
- 派生自上游的**提示文本**部分受 [CC-BY-4.0](https://creativecommons.org/licenses/by/4.0/) 约束。

完整署名声明与修改记录见 `NOTICE`。

**本项目不是 Google 的官方产品。** Google LLC 不对本项目的质量、功能或下游使用承担任何责任。

---

## 参与贡献

欢迎提交 Issue 和 Pull Request。开发流程、代码风格与评审要求见 [CONTRIBUTING.md](CONTRIBUTING.md)。安全问题报告见 [SECURITY.md](SECURITY.md)。

如果本项目对您有帮助，欢迎 Star 让更多人看到。

---

## 许可证

[Apache License 2.0](LICENSE)。Copyright 2026 Jinxiao Wang。

Apache-2.0 仅适用于本开源免费版。Pro 与企业版基于商业 EULA 单独授权，并通过本仓库**外**的渠道分发。

---

## 免责声明

Science Skills 按"现状（AS IS）"提供，不附带任何形式的明示或暗示保证。作者不对因使用本软件而产生的任何直接或间接损害承担责任，包括但不限于科研数据丢失、第三方数据库账号暂停或业务中断。您自行承担使用本软件的全部风险。
