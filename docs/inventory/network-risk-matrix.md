# 技能包网络可用性与风险矩阵 (Network Risk Matrix)

为了向国内科研用户交付高可用性的数据库辅助能力，本文件对 `science-skills` 所依赖的主要外部网络域名进行了国内直连可用性、延迟风险、限流与阻断风险的评估，并提供了网络 profile 优化对策。

---

## 1. 域名网络可用性与风险评级表

| 域名 (Domain) | 归属机构 / 数据库 | 国内直连可用性 | 延迟与抖动风险 | 限流/阻断风险 | 推荐网络 profile 对策 |
| :--- | :--- | :---: | :---: | :---: | :--- |
| `eutils.ncbi.nlm.nih.gov` | 美国 NCBI (PubMed/ClinVar/dbSNP/PubChem) | 🟡 中等 (偶尔受干扰) | 🔴 高 (延迟 200ms+) | 🔴 高 (Anonymous 匿名限流 3 QPS) | 1. 强制在 `.env` 中配置 `NCBI_API_KEY`<br>2. 推荐配置 `SCIENCE_PROXY` 代理加速 |
| `rest.uniprot.org` | 欧洲 UniProt 联盟 | 🟡 中等 (易受出口路由影响) | 🟡 中等 (延迟 150ms+) | 🟡 中等 (高并发时易限流) | 1. 使用内置缓存机制避免重复请求<br>2. 推荐配置 `SCIENCE_PROXY` |
| `search.rcsb.org`<br>`data.rcsb.org`<br>`files.rcsb.org` | 美国 RCSB PDB | 🔴 极差 (files 下载节点常阻断) | 🔴 极高 (直连极慢或超时) | 🟡 中等 | 1. 启用 `SCIENCE_NETWORK_PROFILE=china`<br>2. 自动 fallback 到日本大阪大学 **PDBJ** (`data.pdbj.org`) 镜像节点加速下载 mmCIF 文件 |
| `api.openalex.org`<br>`content.openalex.org` | OpenAlex 学术文献图谱 | 🟡 中等 (Polite 优雅通道直连可达) | 🟡 中等 (延迟 120ms+) | 🟡 中等 (超额限流) | 1. 通过 `OPENALEX_MAILTO` 自动注入 `mailto` 进入 Polite 优雅池<br>2. 商业或高频使用时配置 `OPENALEX_API_KEY` |
| `alphafold.ebi.ac.uk` | 欧洲 EMBL-EBI / DeepMind AlphaFold | 🟡 中等 (直连经常超时) | 🔴 高 (大文件 PDB/CIF 下载慢) | ❌ 低 | 1. 推荐启用 `SCIENCE_PROXY`<br>2. 针对高频结构引入本地冷缓存目录 |
| `rest.ensembl.org` | 欧洲 Ensembl | 🟡 中等 (直连可通，偶有慢速) | 🟡 中等 | 🔴 高 (VEP 大并发易触发 429) | 1. 严格控制并发请求 QPS $\le 3$<br>2. 推荐通过代理进行安全出口转发 |
| `gnomad.broadinstitute.org` | 美国 Broad 研究所 (gnomAD) | 🔴 差 (GraphQL 接口常有长延迟) | 🔴 高 (延迟 250ms+) | ❌ 低 | 1. 推荐配置 `SCIENCE_PROXY`<br>2. 大批量变异查询时优先合并为 single batch 请求 |
| `gtexportal.org` | GTEx Project (基因表达) | 🟡 中等 (直连时通时断) | 🟡 中等 | ❌ 低 | 1. 推荐配置 `SCIENCE_PROXY` |
| `www.proteinatlas.org` | 瑞典 HPA (蛋白质图谱) | 🟡 中等 | 🟡 中等 | ❌ 低 | 1. 大图片/大染色切片下载推荐单独导出 link 提醒用户在浏览器下载 |
| `www.ebi.ac.uk` | 欧洲 EMBL-EBI (ChEMBL/OLS/InterPro/QuickGO) | 🟡 中等 | 🟡 中等 (延迟 180ms+) | ❌ 低 | 1. 合并高频 Ontology 查询<br>2. 推荐配置 `SCIENCE_PROXY` |
| `genome.ucsc.edu` | 美国加州大学圣克鲁兹分校 (UCSC) | 🔴 极差 (直连高概率握手超时) | 🔴 极高 (250ms+) | ❌ 低 | 1. 强制建议通过 `SCIENCE_PROXY` 代理访问以防查询失败 |
| `jaspar.elixir.no` | 挪威 Elixir (JASPAR) | 🟡 中等 | 🟡 中等 | ❌ 低 | 1. 缓存高频转录因子结合矩阵 |
| `reactome.org` | Reactome (通路数据库) | 🟡 中等 | 🟡 中等 | ❌ 低 | 1. 通路分析使用 lightweight json 接口，不主动下载超大 diagram svg |

---

## 2. 三大推荐网络配置 Profile 详述

为了消除上述网络可用性风险，本产品支持通过环境变量 `SCIENCE_NETWORK_PROFILE` 激活针对性的优化配置文件。配置文件采用 **base + overlay** 架构（详见 `config/network_profiles/README.md`）：

- `base.json`：定义所有数据源的官方地址、镜像、备选源和许可证备注，同时也是 `default` profile。
- `china.overlay.json`：仅包含国内优化差异（PDBJ 镜像、Europe PMC fallback、清华 PyPI 镜像），构建时合并到 base 上生成完整的 `china.json`。
- `enterprise.overlay.json`：企业内网模板，通配覆盖所有源为自定义策略，实际私有地址在交付时通过 `SCIENCE_NETWORK_PROFILE_DIR` 注入。

默认 profile 为 `china`，普通用户无需手动设置 `SCIENCE_NETWORK_PROFILE`。

### 2.1 `default` (官方源优先 Profile)
- **适用场景**：海外科研机构、香港/澳门等能直接连通全球学术网 of 科研用户。
- **机制**：
  - 优先调用各个数据库 of 官方主服务器（如 `rcsb.org`, `ebi.ac.uk` 等）。
  - 直连速度快，QPS 限制正常。

### 2.2 `china` (国内优化 Profile)
- **适用场景**：国内高校、科研院所、企业研发中心（未配备专线或全局透明代理 of 直连环境）。
- **机制**：
  - **PDB 大文件加速**：下载三维蛋白质结构坐标文件时，强制绕过美国 `files.rcsb.org`，自动 fallback 到日本大阪大学 of **PDBJ 镜像源** (`https://data.pdbj.org/pub/pdb/data/structures/divided/mmCIF/`)，国内下载速率可提升 5~10 倍。
  - **优雅重试与指数退避**：对于 `ncbi.nlm.nih.gov` 等易受出口路由波动干扰 of 域名，HTTP 客户端自动开启 QPS 平滑退避（Backoff），最大重试次数根据系统底层代码默认配置设定为 **7 次**（提供极高 of 出口闪断容忍度），确保请求不易因瞬间抖动而报错崩溃。
  - **自动注入身份**：通过 `OPENALEX_MAILTO` 自动为 OpenAlex 注入用于 Polite 通道的 `mailto` 信息，提升访问优先级。

### 2.3 `enterprise` (企业私有化隔离 Profile)
- **适用场景**：高安全等级 of 制药企业内网、完全断网 of 私有化部署环境。
- **机制**：
  - 将所有外部 API 重定向至企业内网架设 of 本地私有镜像（如私有 Ensembl 数据库、私有 UniProt TSV 缓存等）。
  - 彻底阻断任何主动 of 外部 Internet 请求，完全规避网络资产泄漏与敏感数据上传风险。

---

## 3. 防范非法解密与速率限制红线

本产品在设计上恪守学术网络道德与第三方服务协议，杜绝任何非常规技术手段：
1. **绝不破解或规避 NCBI/PubChem/Ensembl 官方速率限制**：我们通过公共 HTTP 客户端模块级别内置的 `_RateLimiter` 强制限制每个主机的请求频率和连接间隔。任何时候都**不得**为了并发速度而绕过此限流器控制，否则会导致用户 IP 遭到数据源的系统封锁。
2. **严防敏感凭证泄漏**：本地 `.env` 中的 `NCBI_API_KEY`、`OPENALEX_API_KEY` 等敏感密钥只在本地内存中由 `dotenv` 加载供 HTTP Header 注入使用，**绝对不会**在诊断日志中打印、不会返回给 Agent 上下文，也不会发送到任何第三方服务器上。
