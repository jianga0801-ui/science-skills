# Science Skills 安装指南（开源免费版）

**版本**: 0.1.0
**许可**: Apache License 2.0（详见 `LICENSE`）

> 本文是开源免费版的安装指南。商业 Pro / 企业版的安装与配置流程不同，且不通过本仓库分发，详见 [editions-comparison.md](editions-comparison.md)。

---

## 目录

1. [系统要求](#requirements)
2. [安装步骤](#installation)
3. [环境变量配置](#environment-variables)
4. [国内网络优化](#network-optimization)
5. [验证安装](#verification)
6. [版本更新](#upgrade)
7. [卸载](#uninstall)
8. [常见问题](#faq)

---

<a id="requirements"></a>

## 1. 系统要求

### 操作系统

| 系统 | 最低版本 |
|------|---------|
| Windows | Windows 10 或更高版本 |
| macOS | macOS 12 Monterey 或更高版本 |
| Linux | 主流发行版（Ubuntu 20.04+、Debian 11+、CentOS 7+ 等） |

### 必需软件

| 软件 | 最低版本 | 用途 |
|------|---------|------|
| Python | 3.10+ | 运行核心脚本与诊断工具 |
| pip | 随 Python 自带 | 从交付包本地目录安装 `science-skills-common` 共享库；如 `pip` 命令不可用，请改用 `python -m pip` |
| uv | 最新版（自动安装） | Python 包管理器，用于科学数据库客户端依赖 |

### 磁盘空间

- 技能包本身：约 **50 MB**
- 后续运行过程中下载的数据库文件（如 PDB mmCIF 结构、序列文件等）不计算在内，请预留额外空间

---

<a id="installation"></a>

## 2. 安装步骤

安装只需两步：**部署技能文件 → 安装 Python 依赖**。完成后即可使用，无需额外配置。

### 第一步：部署技能文件

将产品包内的 `skills` 文件夹复制到 Agent 技能的安装目录：

**Windows（PowerShell）**:
```powershell
Copy-Item -Recurse -LiteralPath ".\skills" -Destination "$env:USERPROFILE\.agents\skills\"
```

**macOS / Linux（bash）**:
```bash
cp -r ./skills ~/.agents/skills/
```

> **注意**: 如果目标目录已存在旧版本的 `science` 技能，请先将其删除或备份后再复制，避免新旧文件混杂。

### 第二步：安装 Python 依赖

科学数据库客户端依赖通过 `pip` 从交付包内置源码安装。打开终端，进入交付包根目录（能看到 `skills/` 和 `tools/` 的目录）后执行：

```powershell
# Windows PowerShell / CMD
python -m pip install .\skills\science_skills_common
```

```bash
# macOS / Linux / Git Bash
python -m pip install ./skills/science_skills_common
```

> 如果供应商另行提供私有 PyPI 源或预构建 wheel，请以交付说明中的私有源命令为准；默认交付包不假设 `science-skills-common` 已发布到公开 PyPI。

> **uv 包管理器**: 本项目使用 `uv` 管理各科学技能的独立依赖。首次使用时会自动检测本地 `uv` 安装状态：
> - 若已安装：直接使用，无需额外操作。
> - 若未安装：诊断工具在使用 `--auto-heal` 参数时会自动通过 `python -m pip install uv` 安装（国内网络下自动使用清华 PyPI 镜像加速）。
> - 您也可以手动执行 `python -m pip install uv` 进行安装。

### 完成

以上两步完成后，**重启终端或重新扫描 skills**即可使用。本项目默认启用面向国内用户的 `china` 网络 Profile，普通用户无需手动设置网络策略。

### （可选）故障排查

如果安装后遇到问题，可以运行诊断工具排查：

```powershell
# 全面诊断（含数据库连通性测试）
python tools/science_doctor.py
```

```powershell
# 仅本地检查（不访问外部网络）
python tools/science_doctor.py --no-network
```

诊断工具是可选的，仅用于排查问题。如果诊断发现特定数据库不可达，再阅读 [第4节：国内网络优化](#network-optimization) 中的高级排障选项。

---

<a id="environment-variables"></a>

## 3. 环境变量配置

普通用户通常不需要设置环境变量。本项目内置默认网络策略为 `china`；以下变量用于技术用户、企业内网或故障排查时覆盖默认行为：

| 环境变量 | 说明 | 可选值 | 默认值 |
|---------|------|--------|--------|
| `SCIENCE_NETWORK_PROFILE` | 网络策略 Profile | `china`（默认）/ `base`（`enterprise` 仅在商业企业版中提供） | `china` |
| `SCIENCE_PROXY` | 可选专属代理地址 | HTTP(S) 代理 URL（如 `http://127.0.0.1:7890`） | 空（自动检测系统代理或直连） |
| `SCIENCE_NETWORK_PROFILE_DIR` | 自定义 Profile 目录 | 本地目录绝对路径 | 项目内置目录 |

### 临时生效（当前会话）

以下方法仅在当前终端窗口内生效，关闭窗口后变量丢失：

**Windows PowerShell**:
```powershell
# 如需回到官方源优先策略，可显式指定 default
$env:SCIENCE_NETWORK_PROFILE="base"

# 如需指定 Science Skills 专用代理，可选配置
$env:SCIENCE_PROXY="http://127.0.0.1:7890"
```

**Windows CMD（命令提示符）**:
```cmd
set SCIENCE_NETWORK_PROFILE=base
set SCIENCE_PROXY=http://127.0.0.1:7890
```

**macOS / Linux（bash / zsh）**:
```bash
export SCIENCE_NETWORK_PROFILE="base"
export SCIENCE_PROXY="http://127.0.0.1:7890"
```

### 永久生效

如希望每次打开终端都自动加载这些变量：

**Windows**:
1. 按下 `Win + R`，输入 `sysdm.cpl` 回车。
2. 切换到"高级"选项卡 → 点击"环境变量"。
3. 在"用户变量"区域点击"新建"，按需添加 `SCIENCE_NETWORK_PROFILE` 或 `SCIENCE_PROXY`。
4. 确定保存，**重新打开终端**后生效。

**macOS / Linux（bash）**:
```bash
echo 'export SCIENCE_NETWORK_PROFILE="base"' >> ~/.bashrc
echo 'export SCIENCE_PROXY="http://127.0.0.1:7890"' >> ~/.bashrc
source ~/.bashrc
```

**macOS / Linux（zsh，macOS 默认 Shell）**:
```bash
echo 'export SCIENCE_NETWORK_PROFILE="base"' >> ~/.zshrc
echo 'export SCIENCE_PROXY="http://127.0.0.1:7890"' >> ~/.zshrc
source ~/.zshrc
```

---

<a id="network-optimization"></a>

## 4. 国内网络优化

由于国内直连访问国际学术数据库（如 RCSB PDB、NCBI PubMed、UniProt 等）易受国际出口网络波动影响，本项目提供了一套完整的国内网络优化方案。

### 4.1 内置默认国内网络 Profile

默认网络策略已经是 `china` 模式，系统开箱即自动启用以下优化：
- **PDB mmCIF 文件下载**: 自动 fallback 至大阪大学 **PDBj 镜像**（`data.pdbj.org`），速度可提升 5–10 倍。
- **PubMed API**: 官方源失败时自动 fallback 至 Europe PMC。
- **请求重试**: 自动启用指数级高容错重试机制。
- **PyPI 镜像**: `uv` 包安装自动使用清华/阿里云 PyPI 镜像加速。

技术用户如需回到官方源优先策略，可临时设置 `SCIENCE_NETWORK_PROFILE=base`。

### 4.2 可选代理加速

如果本地已有学术上网代理（如 Clash、V2Ray 等），可将代理地址配置给本项目。代理属于高级排障选项，不是普通用户的必填安装步骤：

```powershell
# Windows PowerShell（请替换为您的实际端口）
$env:SCIENCE_PROXY="http://127.0.0.1:7890"
```

```bash
# macOS / Linux（请替换为您的实际端口）
export SCIENCE_PROXY="http://127.0.0.1:7890"
```

> **同时启用国内 Profile + 代理的效果**:
> - PDB 大文件下载走国内 PDBJ 镜像（无需代理流量）
> - NCBI API 查询走代理（绕过出口瓶颈）
> - 兼得低延迟与高稳定性

### 4.3 PyPI 镜像加速（uv）

默认 `china` profile 下，uv 安装 Python 包会自动使用以下镜像源：

| 优先级 | 镜像源 URL |
|--------|-----------|
| 1（主） | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| 2（备） | `https://mirrors.aliyun.com/pypi/simple/` |

> 这是通过 `config/network_profiles/china.overlay.json` 中的 `pypi` 配置段实现的，无需手动配置 `uv`。

---

<a id="verification"></a>

## 5. 验证安装

安装完成后，运行科学健康诊断脚本进行全面验证。

### 5.1 全面诊断（推荐）

```powershell
# Windows PowerShell / CMD
python tools/science_doctor.py
```

```bash
# macOS / Linux / Git Bash
python tools/science_doctor.py
```

### 5.2 离线诊断（仅本地检查）

如果只需验证本地环境（Python 版本、uv 安装状态、临时目录权限等），不访问外部网络：

```powershell
python tools/science_doctor.py --no-network
```

### 5.3 自动修复模式

如果在国内网络下诊断发现 `uv` 未安装，可使用 `--auto-heal` 让诊断工具自动修复：

```powershell
python tools/science_doctor.py --auto-heal
```

> `--auto-heal` 会在检测到 `uv` 缺失时自动通过 `pip install uv` 安装（国内网络下自动使用清华 PyPI 镜像），并自动注入项目级 `uv.toml` 指向国内镜像源。

### 5.4 自定义超时时间

```powershell
# 将网络探测超时设为 30 秒（默认 10 秒）
python tools/science_doctor.py --timeout 30
```

### 5.5 预期输出

诊断工具输出 JSON 格式报告，便于 Agent 解析。以下是各网络环境下的典型输出示例：

#### ✅ 全部通过（`status: "ok"`）

```json
{
  "status": "ok",
  "checks": {
    "python": {
      "status": "ok",
      "version": "3.12.3",
      "executable": "C:\\Users\\Jinxiao\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
    },
    "uv": {
      "status": "ok",
      "path": "C:\\Users\\Jinxiao\\AppData\\Local\\Programs\\Python\\Python312\\Scripts\\uv.exe",
      "auto_installed": false
    },
    "network_profile": {
      "status": "ok",
      "profile": "china",
      "sources": ["alphafold", "chembl", "openalex", "pdb", "pubmed", "..."]
    },
    "temp_lock": {
      "status": "ok",
      "temp_dir": "C:\\Users\\Jinxiao\\AppData\\Local\\Temp"
    },
    "env_file": {
      "status": "ok",
      "present": false
    },
    "proxy": {
      "status": "ok",
      "configured": false,
      "env": "SCIENCE_PROXY"
    },
    "pubmed_api": {
      "status": "ok",
      "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi?db=pubmed"
    },
    "pdb_download_mirror": {
      "status": "ok",
      "url": "https://data.pdbj.org/pub/pdb/data/structures/divided/mmCIF/cb/1cbs.cif.gz"
    }
  }
}
```

#### ⚠️ 有警告但可用（`status: "warn"`）

典型场景：存在 `.env` 文件但诊断工具不会读取密钥，或个别可选检查需要人工确认。未配置代理本身不再作为警告：

```json
{
  "status": "warn",
  "checks": {
    "proxy": {
      "status": "ok",
      "hint": "未检测到代理；默认 china profile 已启用，代理仅作为高级排障选项。",
      "configured": false,
      "env": "SCIENCE_PROXY"
    }
  }
}
```

#### ❌ 存在关键失败（`status: "fail"`）

典型场景：科学数据库无法访问。请根据 `hint` 字段中的中文提示检查网络环境与配置：

```json
{
  "status": "fail",
  "checks": {
    "pubmed_api": {
      "status": "fail",
      "hint": "PubMed 官方 API 访问失败，可能是网络、代理或远端服务限制。请检查网络 profile，必要时再配置代理后重试。错误类型: URLError",
      "url": "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi?db=pubmed"
    }
  }
}
```

> **诊断结果字段说明**:
> - `"status": "ok"` — 该项检查通过，无需处理。
> - `"status": "warn"` — 存在潜在问题，当前可用但建议优化。
> - `"status": "fail"` — 检查失败，需要根据 `hint` 提示修复。
> - `"status": "skip"` — 已跳过（如使用 `--no-network` 时）。

---

<a id="upgrade"></a>

## 6. 版本更新

当新版本发布时，按以下步骤更新：

### 6.1 更新技能文件

```powershell
# Windows PowerShell：列出旧版本 → 移入备份目录 → 复制新版
$skillRoot = Join-Path $env:USERPROFILE ".agents\skills"
$archive = Join-Path $env:USERPROFILE ".agents\skills.archive.$(Get-Date -Format 'yyyyMMddHHmmss')"
$oldSkills = Get-ChildItem -LiteralPath $skillRoot -Directory -Filter "science*"
$oldSkills | Select-Object FullName
New-Item -ItemType Directory -Path $archive | Out-Null
$oldSkills | ForEach-Object { Move-Item -LiteralPath $_.FullName -Destination $archive }
Copy-Item -Recurse -LiteralPath ".\skills" -Destination "$env:USERPROFILE\.agents\skills\"
```

```bash
# macOS / Linux：列出旧版本 → 移入备份目录 → 复制新版
skill_root="${HOME}/.agents/skills"
archive="${HOME}/.agents/skills.archive.$(date +%s)"
find "$skill_root" -maxdepth 1 -type d -name 'science*' -print
mkdir -p "$archive"
find "$skill_root" -maxdepth 1 -type d -name 'science*' -exec mv {} "$archive"/ \;
cp -r ./skills ~/.agents/skills/
```

### 6.2 更新 Python 依赖

```powershell
python -m pip install --upgrade --force-reinstall .\skills\science_skills_common
```

### 6.3 重新验证

```powershell
python tools/science_doctor.py
```

确保诊断报告状态为 `"ok"` 或 `"warn"`（无可修复的 `"fail"`）。

---

<a id="uninstall"></a>

## 7. 卸载

卸载本项目只需删除技能文件夹。

### 7.1 删除技能文件

**Windows（PowerShell）**:
```powershell
$skillRoot = Join-Path $env:USERPROFILE ".agents\skills"
$archive = Join-Path $env:USERPROFILE ".agents\skills.uninstalled.$(Get-Date -Format 'yyyyMMddHHmmss')"
$matchedSkills = Get-ChildItem -LiteralPath $skillRoot -Directory -Filter "science*"
$matchedSkills | Select-Object FullName
New-Item -ItemType Directory -Path $archive | Out-Null
$matchedSkills | ForEach-Object { Move-Item -LiteralPath $_.FullName -Destination $archive }
```

**macOS / Linux（bash）**:
```bash
skill_root="${HOME}/.agents/skills"
archive="${HOME}/.agents/skills.uninstalled.$(date +%s)"
find "$skill_root" -maxdepth 1 -type d -name 'science*' -print
mkdir -p "$archive"
find "$skill_root" -maxdepth 1 -type d -name 'science*' -exec mv {} "$archive"/ \;
```

### 7.2 （可选）卸载 Python 依赖

如您不再需要使用科学数据库查询功能：

```powershell
python -m pip uninstall science-skills-common
```

### 7.3 （可选）清除项目文件

删除产品包根目录即可。

---

<a id="faq"></a>

## 8. 常见问题

### Q1: 运行诊断时提示 "未检测到 uv"

**原因**: `uv` 包管理器未安装或未加入系统 PATH。

**解决**:
```powershell
# 方案一：手动安装
pip install uv

# 方案二：使用诊断工具自动安装（国内网络下自动使用清华镜像）
python tools/science_doctor.py --auto-heal
```

如果方案一失败（国内网络访问 PyPI 慢或超时），可以指定清华镜像：
```powershell
pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q2: PubMed 或 PDB 诊断显示 `"fail"`

**原因**: 网络策略不匹配当前网络环境。

**解决方案（按推荐顺序）**:

1. **普通国内用户**: 默认已经启用 `china` Profile，无需额外配置。先重新运行诊断确认是否只是远端短时波动。

2. **有本地代理的技术用户**: 配置代理变量：
   ```powershell
   $env:SCIENCE_PROXY="http://127.0.0.1:7890"
   ```

3. **需要官方源优先策略的技术用户**: 可切换到 `base`：
   ```powershell
   $env:SCIENCE_NETWORK_PROFILE="base"
   ```

配置完成后重新运行 `python tools/science_doctor.py`。

### Q3: "临时目录或锁文件不可写"

**原因**: 系统临时目录权限异常或磁盘空间不足。

**解决**:
- 检查 `%TEMP%`（Windows）或 `/tmp`（macOS/Linux）的读写权限。
- 清理系统磁盘空间后重试。
- 如果在企业内网受限环境中，请联系 IT 管理员确认临时目录权限。

### Q4: 技能加载后 Agent 不识别

**原因**: Agent 未重启，或技能文件路径不正确。

**解决**:
1. 确认技能文件夹位于正确路径：
   - Windows: `%USERPROFILE%\.agents\skills\` 下存在 `science_skills_common` 等子文件夹。
   - macOS/Linux: `~/.agents/skills/` 下存在相应子文件夹。
2. **完全退出并重新启动** AI Agent 终端。
3. 重新运行 `python tools/science_doctor.py` 确认本地环境正常。

### Q5: 企业内网环境如何配置

开源免费版**不**包含 `enterprise` profile。企业用户若需要私有镜像 / 内网终点 / 子账号管理，请查看 [editions-comparison.md](editions-comparison.md) 中的企业版说明。

如果只是想用自定义的 profile 文件（不依赖商业企业版），可通过 `SCIENCE_NETWORK_PROFILE_DIR` 指向本地目录：

```powershell
$env:SCIENCE_NETWORK_PROFILE_DIR="D:\my-network-profiles"
$env:SCIENCE_NETWORK_PROFILE="base"   # 或保持 china
```

### Q6: 如何确认当前生效的网络 Profile

运行诊断工具，查看输出中的 `network_profile` 项：

```json
"network_profile": {
  "status": "ok",
  "profile": "china",
  "sources": ["alphafold", "chembl", "openalex", "pdb", "pubmed", "..."]
}
```

`profile` 字段即为当前生效的 Profile 名称。

---

*本文档最后更新: 2026 年 5 月*
