# Editions: Free / Pro / Enterprise — 版本对比

**Language**: English (below) | [跳转到中文版](#中文版)

---

## English

Science Skills is offered in three editions. The **Free** edition (this open-source repository) is the foundation. **Pro** and **Enterprise** are commercial editions distributed outside this repository.

### Side-by-side comparison

| Dimension | Free (open source) | Pro (commercial) | Enterprise (commercial) |
|---|---|---|---|
| **License** | Apache-2.0 | Commercial EULA | Commercial contract |
| **Target audience** | Students, individual researchers, evaluation | Independent researchers, small labs | Universities, R&D departments, large institutions |
| **Distribution** | This GitHub repository | Direct delivery after purchase | Direct delivery, per-institution contract |
| **Literature skills** | PubMed | PubMed + EuropePMC + OpenAlex | Same as Pro + private-corpus integration support |
| **Protein / structure skills** | PDB | PDB + UniProt + AlphaFold | Same as Pro + private-database integration support |
| **Chemistry skills** | — | PubChem + ChEMBL | Same as Pro + private compound library |
| **Variants / clinical skills** | — | ClinVar + dbSNP + Ensembl + ClinicalTrials | Same as Pro + private clinical-data integration support |
| **Chinese query normalization** | PubMed, PDB | Across all commercial skills | Same as Pro + custom term-mapping table |
| **Network profiles** | `china` (default), `default` | `china` (default), `default` | `china` (default), `default`, `enterprise` (private mirrors, internal endpoints) |
| **Proxy support** | Optional (`SCIENCE_PROXY`) | Optional (`SCIENCE_PROXY`) | Optional (`SCIENCE_PROXY`) |
| **Science Doctor (diagnostic)** | Standard | Standard | Standard + enterprise extensions |
| **Agent adapters** | Codex, Claude Code, Cursor | Codex, Claude Code, Cursor | + Dify, LangGraph (and custom platforms on request) |
| **Update policy** | Open-source releases | 12 months of updates per purchase | Continuous updates within contract |
| **Support** | Community best-effort (GitHub Issues / Discussions) — no SLA | Email, ~72 h response | Dedicated channel, ~24 h response, plus remote assistance |
| **Customer package ID** | None | Per-licensee, embedded in delivered package | Per-institution, with sub-account management |
| **Private deployment / mirrors** | Not included | Not included | Included |
| **Training / docs** | Online README + FAQ | Online docs + quickstart | Full training docs, troubleshooting handbook, admin guide |
| **Seats** | Individual (community) | Single user (per license) | Per contract |
| **Pricing model** | Free | One-time purchase | Annual contract |

### Upgrade paths

- **Free → Pro**: purchase a Pro license through the official channel. You will receive a customer package ID and an installable Pro package. Your existing Free configuration migrates over.
- **Pro → Enterprise**: contact the maintainer for an Enterprise quote and custom deployment plan. Enterprise requires an institutional contract.

### Commercial editions: how to inquire

The commercial Pro / Enterprise editions are not distributed through this GitHub repository. To inquire, please open a GitHub Discussion in this repo titled "Commercial inquiry — [Pro|Enterprise]" with your use case. The maintainer will follow up by email.

### What this open-source edition is **not**

To set expectations clearly:

- No SLA — community best-effort only.
- No customer package ID, no embedded license tokens, no online activation.
- No `enterprise` network profile, no Dify / LangGraph adapter.
- No commercial-bundle skills (UniProt, AlphaFold, ChEMBL, PubChem, etc.).
- Not redistributable as your own SaaS product without preserving Apache-2.0 obligations and upstream attribution.

The open-source Free edition is fully usable on its own for the PubMed + PDB workflows it covers. The commercial editions exist to serve users who need broader coverage, private deployment, or formal support.

---

## 中文版

Science Skills 提供三个版本。**免费版（Free）** 即本开源仓库，是产品基线。**Pro 版** 与 **企业版（Enterprise）** 是商业版本，**不**通过本仓库分发。

### 三版对比表

| 维度 | 免费版（开源） | Pro 版（商业） | 企业版（商业） |
|---|---|---|---|
| **许可证** | Apache-2.0 | 商业 EULA | 商业合同 |
| **适用对象** | 学生、个人科研者、试用评估 | 独立科研人员、课题组、小型实验室 | 高校、企业研发部门、大型机构 |
| **交付方式** | 本 GitHub 仓库 | 购买后直接交付 | 按机构合同直接交付 |
| **文献检索** | PubMed | PubMed + EuropePMC + OpenAlex | 同 Pro + 内部语料库集成支持 |
| **蛋白 / 结构** | PDB | PDB + UniProt + AlphaFold | 同 Pro + 私有数据库集成支持 |
| **化学信息学** | — | PubChem + ChEMBL | 同 Pro + 企业私有化合物库 |
| **变异 / 临床** | — | ClinVar + dbSNP + Ensembl + ClinicalTrials | 同 Pro + 私有临床数据集成支持 |
| **中文查询归一化** | PubMed、PDB | 商业技能全覆盖 | 同 Pro + 自定义术语映射表 |
| **网络 Profile** | `china`（默认）、`default` | `china`（默认）、`default` | `china`（默认）、`default`、`enterprise`（私有镜像 / 内网终点） |
| **代理支持** | 可选（`SCIENCE_PROXY`） | 可选 | 可选 |
| **Science Doctor 诊断** | 标准版 | 标准版 | 标准版 + 企业扩展 |
| **Agent 适配器** | Codex / Claude Code / Cursor | Codex / Claude Code / Cursor | + Dify / LangGraph（可按需扩展） |
| **更新策略** | 按开源版本发布节奏 | 自购买起 12 个月内功能更新与修复 | 合同期内持续更新与安全补丁 |
| **技术支持** | 社区尽力（GitHub Issues / Discussions），无 SLA | 邮件，约 72 小时响应 | 专属通道，约 24 小时响应，含远程协助 |
| **客户专属包编号** | 无 | 每份授权唯一编号，嵌入交付包 | 每机构唯一编号，可管理子账号 |
| **私有部署 / 镜像** | 不含 | 不含 | 包含 |
| **培训 / 文档** | 在线 README + FAQ | 在线文档 + 快速开始 | 完整培训文档、故障排查手册、管理员指南 |
| **授权人数** | 个人（社区） | 个人单用户绑定 | 按合同约定 |
| **价格模式** | 免费 | 一次性购买 | 年度合同 |

### 升级路径

- **免费版 → Pro 版**：通过官方渠道购买 Pro 授权，获取专属包编号与可安装 Pro 包，原有免费版配置可平滑迁移。
- **Pro 版 → 企业版**：联系作者获取企业版报价与定制方案。企业版需签订机构合同。

### 商业版咨询方式

Pro / 企业版**不**通过本 GitHub 仓库分发。如需咨询，请在本仓库的 GitHub Discussions 中创建标题为 "Commercial inquiry — [Pro|Enterprise]" 的讨论并附简要用例，作者会通过邮件跟进。

### 开源免费版**不**包含什么

为避免预期偏差，请注意以下事项：

- **无 SLA**：仅社区尽力支持。
- **无客户专属包编号**、**无嵌入式授权令牌**、**无在线激活**。
- **无 `enterprise` 网络 profile**、**无 Dify / LangGraph 适配器**。
- **无商业版技能**（UniProt、AlphaFold、ChEMBL、PubChem 等）。
- 不得在不履行 Apache-2.0 义务与上游署名要求的情况下，将本项目重新打包为您自有的 SaaS 服务对外提供。

开源免费版对 PubMed + PDB 工作流而言已是完整、独立可用的产品。商业版面向需要更广覆盖、私有部署或正式支持的用户。
