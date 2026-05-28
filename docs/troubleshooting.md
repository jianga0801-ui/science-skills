# Science Skills 故障排查指南

本文档按症状分类提供 Science Skills 的常见问题诊断与解决方案。建议遇到问题时先运行 `python tools/science_doctor.py` 获取结构化诊断报告，再根据报告中的 `hint` 字段定位具体问题。

---

## 目录

1. [安装问题](#installation-issues)
2. [网络问题](#network-issues)
3. [运行时问题](#runtime-issues)
4. [诊断工具使用](#doctor-usage)
5. [数据库特定问题](#database-issues)
6. [Windows 特定问题](#windows-issues)

---

<a id="installation-issues"></a>

## 1. 安装问题

### 1.1 uv 未找到 / "uv not found"

**症状**: 运行脚本时提示 `'uv' is not recognized` 或 `command not found: uv`。

**原因**: uv 未安装或未加入系统 PATH。Science Skills 使用 uv 管理技能依赖，但部分安装路径可能需要重启终端后生效。

**解决方案**:

先运行诊断确认：
```powershell
python tools/science_doctor.py
```
查看 `checks.uv` 字段。若为 `"fail"` 或 `"warn"`，按以下步骤安装。

手动安装 uv：

- **PowerShell**:
  ```powershell
  pip install uv
  ```
- **CMD / 命令提示符**:
  ```cmd
  pip install uv
  ```
- **bash (Linux / macOS / Git Bash)**:
  ```bash
  pip install uv
  ```

安装后重启终端，再次运行诊断确认。若仍然未找到，使用带 `--auto-heal` 的诊断工具自动安装：

```powershell
python tools/science_doctor.py --auto-heal
```

`--auto-heal` 会根据当前网络 profile（如 china profile 使用清华 PyPI 镜像）自动选择合适的 PyPI 源进行安装。

---

### 1.2 pip install 失败 / 镜像不可达

**症状**: 执行 `pip install uv` 或 `pip install <package>` 时报网络超时或 404 错误。

**原因**: 国内网络连接 PyPI 官方源 (`https://pypi.org`) 可能较慢或不稳定。大文件下载或首次安装时尤其明显。

**解决方案**:

指定国内 PyPI 镜像安装 uv：

- **PowerShell**:
  ```powershell
  pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```
- **CMD / 命令提示符**:
  ```cmd
  pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```
- **bash (Linux / macOS / Git Bash)**:
  ```bash
  pip install uv -i https://pypi.tuna.tsinghua.edu.cn/simple
  ```

备选镜像：

| 镜像源 | URL |
|--------|-----|
| 清华 TUNA | `https://pypi.tuna.tsinghua.edu.cn/simple` |
| 阿里云 | `https://mirrors.aliyun.com/pypi/simple/` |
| 中科大 USTC | `https://pypi.mirrors.ustc.edu.cn/simple/` |

默认 `china` 网络 profile 已启用，`--auto-heal` 会自动使用清华镜像加速：
```powershell
python tools/science_doctor.py --auto-heal
```

---

### 1.3 技能安装后未被识别

**症状**: Agent 提示 "skill not found" 或调用技能时无响应。

**原因**: 技能文件夹未放置在正确位置，或目录结构不完整。

**解决方案**:

1. 确认技能文件夹已放置在正确路径：
   - **Windows**: `%USERPROFILE%\.agents\skills\science\`
   - **Linux / macOS**: `~/.agents/skills/science/`

   该目录下应包含 `SKILL.md` 和 `scripts/` 等子目录。

2. 确认 `science_skills_common` 包已正确安装。普通用户请在交付包根目录执行：

   ```powershell
   python -m pip install .\skills\science_skills_common
   ```

   仅开发者在本仓库内调试源码时使用 editable 模式：`python -m pip install -e .\skills\science_skills_common`。

3. **重启终端或重新扫描 skills**。部分 Agent 启动时一次性加载技能注册表，不重启不会识别新增技能。

4. 运行诊断确认环境：

   ```powershell
   python tools/science_doctor.py --no-network
   ```

   确认 `checks.python.executable` 指向正确的 Python 解释器。

---

### 1.4 Python 版本过旧

**症状**: 运行脚本时报语法错误（如类型注解等新语法不兼容），或提示 `requires Python >= 3.10`。

**原因**: Science Skills 依赖 Python 3.10+ 的语法和标准库特性。

**解决方案**:

1. 检查当前 Python 版本：

   - **PowerShell / CMD**:
     ```cmd
     python --version
     ```
   - **bash**:
     ```bash
     python3 --version
     ```

2. 如果低于 3.10，从 [python.org](https://www.python.org/downloads/) 下载最新版 Python 安装。建议使用 Python 3.11 或更新的稳定版本。

3. 安装新版后，确认 `python` 命令指向新版本：

   - **PowerShell**:
     ```powershell
     (Get-Command python).Source
     ```
   - **bash**:
     ```bash
     which python3
     ```

4. 重新安装 `science_skills_common`：

   ```powershell
   python -m pip install --force-reinstall .\skills\science_skills_common
   ```

---

<a id="network-issues"></a>

## 2. 网络问题

### 2.1 PubMed / NCBI 无法访问

**症状**: `science_doctor.py` 报告中 `checks.pubmed_api.status` 为 `"fail"`，提示 URL 为 `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi`。脚本调用 PubMed 技能时报 `Network error fetching ...: <urlopen error ...>` 或连接超时。

**原因**: 国内网络直连 NCBI 服务器 (`eutils.ncbi.nlm.nih.gov`) 可能因国际出口波动、DNS 污染或防火墙限制导致失败。

**解决方案**:

**方案 A — 确认默认 china profile 已生效**

默认 profile 已是 `china`，PubMed 官方源失败时会按配置尝试 Europe PMC 替代源。先运行诊断查看当前 profile：

```powershell
python tools/science_doctor.py
```

如技术用户曾经手动切换过 profile，可清除该变量或显式恢复：

```powershell
$env:SCIENCE_NETWORK_PROFILE="china"
```

**方案 B — 配置可选代理**（适用于已有本地代理的技术用户）

- **PowerShell**:
  ```powershell
  $env:SCIENCE_PROXY="http://127.0.0.1:7890"
  ```
- **CMD / 命令提示符**:
  ```cmd
  set SCIENCE_PROXY=http://127.0.0.1:7890
  ```
- **bash (Linux / macOS / Git Bash)**:
  ```bash
  export SCIENCE_PROXY="http://127.0.0.1:7890"
  ```

将 `7890` 替换为你的代理监听端口。设置后重新运行诊断：
```powershell
python tools/science_doctor.py
```

> **注意**: `SCIENCE_PROXY` 与系统级 `HTTP_PROXY` / `HTTPS_PROXY` 的区别：
> - `SCIENCE_PROXY` 仅影响 Science Skills 的网络请求，不会干扰其他程序。
> - 如果多个变量同时设置，优先级为 `SCIENCE_PROXY` > `HTTPS_PROXY` > `HTTP_PROXY`。
> - **切勿在聊天中发送你的代理地址和端口。**

---

### 2.2 PDB / PDBJ 镜像下载失败

**症状**: `science_doctor.py` 报告中 `checks.pdb_download_mirror.status` 为 `"fail"`，提示 URL 为 `https://data.pdbj.org/pub/pdb/data/structures/divided/mmCIF/cb/1cbs.cif.gz`。下载 PDB 结构文件时超时或 404。

**原因**:
- **default profile**: 使用 RCSB PDB 官方下载 (`https://files.rcsb.org/download/`)，国内访问可能慢或不稳定。
- **china profile**: 使用大阪大学 PDBJ 镜像 (`https://data.pdbj.org/`)，通常国内速度更好，但因网络波动仍可能短暂不可达。

**解决方案**:

1. 确认当前仍使用默认 `china` profile，以启用 PDBJ 镜像下载加速：

   ```powershell
   python tools/science_doctor.py --no-network
   ```

   注意区分：
   - **API 查询**（如检索 PDB 条目元数据）：仍然走 RCSB PDB 官方 API (`https://data.rcsb.org`)。
   - **文件下载**（如 `.cif` / `.pdb` 结构文件）：交由 PDBJ 镜像 (`data.pdbj.org`) 下载。

2. 如果 PDBJ 镜像也超时，配置 SCIENCE_PROXY：

   ```powershell
   $env:SCIENCE_PROXY="http://127.0.0.1:7890"
   ```

3. PDB 技能也支持 fallback 到 PDBe (`https://www.ebi.ac.uk/pdbe/`)，可在 profile 配置中启用。

---

### 2.3 UniProt 无法访问

**症状**: UniProt 查询脚本报网络错误或超时，提示 URL 为 `https://rest.uniprot.org`。

**原因**: UniProt REST API 仅提供官方源，没有官方镜像。国内直连可能因国际出口受限。

**解决方案**:

UniProt 目前没有内置镜像支持。解决方法：

1. 技术用户可配置可选代理（命令同上，2.1 方案 B），也可使用系统级 `HTTPS_PROXY` / `HTTP_PROXY`。
2. 增大查询超时时间：

   ```powershell
   python tools/science_doctor.py --timeout 30
   ```

   诊断默认超时 10 秒；生产请求的默认超时为 60 秒。如果网络环境确实很差，可在诊断中先用更大超时验证连通性。

3. 如果临时代理不可用，可尝试通过 IP 查询 UniProt，并将结果手动缓存在本地。

---

### 2.4 DNS 解析错误

**症状**: 错误信息中包含 `getaddrinfo failed`、`Name or service not known`、`Temporary failure in name resolution`。

**原因**: 系统 DNS 无法解析目标域名（如 `eutils.ncbi.nlm.nih.gov`）。常见于：
- 企业内网屏蔽了公共 DNS。
- 系统 DNS 配置被 ISP 劫持。
- 代理软件未同时代理 DNS 请求。

**解决方案**:

1. 在命令行中测试 DNS 解析：

   - **PowerShell**:
     ```powershell
     Resolve-DnsName eutils.ncbi.nlm.nih.gov
     ```
   - **CMD**:
     ```cmd
     nslookup eutils.ncbi.nlm.nih.gov
     ```
   - **bash**:
     ```bash
     nslookup eutils.ncbi.nlm.nih.gov
     ```

2. 如果返回 `Non-existent domain` 或超时：
   - 尝试更换 DNS 为公共 DNS（如 `8.8.8.8`、`114.114.114.114`）。
   - Windows: 在"网络和 Internet 设置" → "更改适配器选项" → 属性 → IPv4 DNS 中修改。
   - macOS: 在"系统设置" → "网络" → "DNS" 中添加 `8.8.8.8`。

3. 如果使用代理软件（Clash / V2Ray），确保代理软件开启了 "System Proxy" 或 "TUN 模式"，使 DNS 请求也走代理。

4. 确认 SCIENCE_PROXY 配置无误后，重新测试：

   ```powershell
   $env:SCIENCE_PROXY="http://127.0.0.1:7890"
   python tools/science_doctor.py
   ```

---

### 2.5 SSL 证书错误

**症状**: 错误信息中包含 `SSL: CERTIFICATE_VERIFY_FAILED`、`certificate verify failed` 或 `[SSL] record layer failure`。

**原因**:
- 系统 CA 证书过期或缺失。
- 企业代理对 HTTPS 做了中间人拦截（MITM），替换了证书。
- 系统时间不正确导致证书验证失败。

**解决方案**:

1. 检查系统时间是否正确。证书验证依赖准确的系统时钟，时间偏差过大会导致所有 HTTPS 连接失败。

2. 更新 CA 证书：
   - **Windows**: 运行 Windows Update 或手动安装最新根证书。
   - **Linux (Debian/Ubuntu)**:
     ```bash
     sudo apt update && sudo apt install ca-certificates
     ```
   - **macOS**: 更新操作系统即可。

3. 如果使用的是公司内网代理且代理做了 HTTPS 拦截：
   - 联系 IT 部门获取代理的 CA 证书并安装到系统信任根证书存储中。
   - 开源免费版仅含 `china`（默认）与 `base` 两个 profile；如果需要私有镜像 / 内网终点的 `enterprise` profile，请查看 [editions-comparison.md](editions-comparison.md) 中的企业版说明。也可以通过 `SCIENCE_NETWORK_PROFILE_DIR` 指向本地自定义 profile 目录。

---

### 2.6 如何确认网络 Profile 已生效

运行诊断，查看 `checks.network_profile`：

```powershell
python tools/science_doctor.py
```

JSON 输出中：
- `checks.network_profile.profile` — 当前激活的 profile 名称（默认 `china`；可选 `base`）。`enterprise` 仅在商业企业版中提供。
- `checks.network_profile.sources` — 当前 profile 中已配置的数据源列表（如 `["alphafold", "chembl", "openalex", "pdb", "pubmed", "..."]`）。

若 `status` 为 `"fail"`，检查：
- 是否手动设置了错误的 `SCIENCE_NETWORK_PROFILE`；普通用户不设置时默认使用 `china`（国内优化，API 查询优先官方源，大文件下载使用镜像）。
- 对应的 profile JSON 文件是否存在。运行时读取的是合并后的完整 JSON（如 `china.json`），而非 overlay 源文件：
  - 包内资源 `skills/science_skills_common/network_profiles/`（优先）
  - `config/network_profiles/`（fallback）
- overlay 源文件位于 `config/network_profiles/`（`base.json` + `*.overlay.json`），仅用于构建包，运行时不直接读取。

---

### 2.7 环境变量持久化

当前终端中设置的环境变量（`$env:...` / `set` / `export`）仅对该会话有效，关闭终端后失效。

**永久设置方法**：

- **Windows PowerShell** (用户级):
  ```powershell
  [Environment]::SetEnvironmentVariable("SCIENCE_NETWORK_PROFILE", "china", "User")
  [Environment]::SetEnvironmentVariable("SCIENCE_PROXY", "http://127.0.0.1:7890", "User")
  ```
  修改后需重启终端生效。

- **Windows CMD** (系统级，需管理员):
  ```cmd
  setx SCIENCE_NETWORK_PROFILE "china"
  setx SCIENCE_PROXY http://127.0.0.1:7890
  ```

- **Linux / macOS** (用户级):
  将以下内容追加到 `~/.bashrc` 或 `~/.zshrc`：
  ```bash
  export SCIENCE_NETWORK_PROFILE="china"
  export SCIENCE_PROXY="http://127.0.0.1:7890"
  ```
  然后执行 `source ~/.bashrc` 或重启终端。

---

<a id="runtime-issues"></a>

## 3. 运行时问题

### 3.1 ModuleNotFoundError: science_skills 或 science_skills_common

**症状**:

```
ModuleNotFoundError: No module named 'science_skills'
ModuleNotFoundError: No module named 'science_skills_common'
ModuleNotFoundError: No module named 'science_skills.science_skills_common'
```

**原因**: `science_skills_common` 包未安装或 Python 的 site-packages 中没有该包的路径。

**解决方案**:

1. 普通用户请在交付包根目录安装内置本地包：

   ```powershell
   python -m pip install .\skills\science_skills_common
   ```

   如果供应商另行提供私有 PyPI 源或预构建 wheel，请以交付说明中的私有源命令为准。仅开发者在本仓库内调试源码时使用 editable 模式：`python -m pip install -e .\skills\science_skills_common`。该包使用 `pyproject.toml` + `hatchling` 构建，确保 pip 版本 >= 21.3。

2. 验证安装：

   ```powershell
   pip show science-skills-common
   ```

   输出应显示 `Location:` 指向你的 site-packages 目录及包版本 `1.2.0`。

3. 确认 Python 解释器与 pip 属于同一环境：

   ```powershell
   python -c "from science_skills.science_skills_common import http_client; print(http_client.__file__)"
   ```

4. 如果使用虚拟环境（venv / conda），确保已激活正确的环境后再执行上述命令：

   - **PowerShell (venv)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **CMD (venv)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **bash (venv)**:
     ```bash
     source .venv/bin/activate
     ```

---

### 3.2 锁文件权限错误

**症状**: 运行技能脚本时报 `PermissionError` 或 `OSError` 涉及临时目录中的 `.lock` 文件，路径类似：
```
C:\Users\<用户名>\AppData\Local\Temp\science-skills-ncbi.nlm.nih.gov.lock
```

**原因**: Science Skills 使用系统临时目录 (`tempfile.gettempdir()`) 存放跨进程速率限制锁文件。如果临时目录不可写或锁文件被其他进程（如杀毒软件）锁定，会导致错误。

**解决方案**:

1. 先运行诊断确认临时目录是否可写：

   ```powershell
   python tools/science_doctor.py --no-network
   ```

   查看 `checks.temp_lock.status`。如果为 `"fail"`，检查临时目录权限。

2. 手动验证临时目录可写：

   - **PowerShell**:
     ```powershell
     $tempDir = [System.IO.Path]::GetTempPath()
     Write-Output "Temp: $tempDir"
     $testFile = Join-Path $tempDir "science-skills-test.tmp"
     "test" | Out-File -FilePath $testFile -Encoding UTF8
     Remove-Item $testFile
     Write-Output "Read/Write OK"
     ```
   - **bash**:
     ```bash
     echo "Temp: $(python -c 'import tempfile; print(tempfile.gettempdir())')"
     echo "test" > "$(python -c 'import tempfile; print(tempfile.gettempdir())')/science-skills-test.tmp"
     rm "$(python -c 'import tempfile; print(tempfile.gettempdir())')/science-skills-test.tmp"
     echo "Read/Write OK"
     ```

3. 常见原因及处理：
   - **杀毒软件锁定**: 将 Science Skills 的临时目录添加到杀毒软件白名单。Windows 下通常是 `%TEMP%`。
   - **磁盘已满**: 清理临时文件或释放磁盘空间。
   - **权限不足**: 以管理员身份运行终端（右键 -> "以管理员身份运行"），特别是企业管理的 Windows 设备。
   - **路径包含特殊字符**: 确保 Windows 用户名不包含 Unicode 特殊字符（参见 6.3 节）。

4. 清理残留锁文件：

   - **PowerShell**:
     ```powershell
     Remove-Item -LiteralPath "$env:TEMP\science-skills-*.lock"
     ```
   - **bash**:
     ```bash
     rm -f /tmp/science-skills-*.lock
     ```
   注意：仅当所有 Science Skills 进程均已停止时才执行。

---

### 3.3 临时目录问题

**症状**: 脚本启动时报错涉及 `/tmp`（Linux/macOS）或 `%TEMP%`（Windows）目录创建失败。

**原因**: 系统临时目录不存在或不可访问。常见于某些精简版 Linux 发行版或企业锁定的 Windows 桌面。

**解决方案**:

1. 确认临时目录路径：

   ```powershell
   python -c "import tempfile; print(tempfile.gettempdir())"
   ```

2. 确保该目录存在且有写入权限：
   - **Windows**: 通常是 `C:\Users\<用户名>\AppData\Local\Temp`，应始终存在。
   - **Linux**: 通常是 `/tmp`，确认 `ls -la /tmp` 有写入权限。

3. 可以绕过系统默认临时目录，手动设置：

   - **Windows PowerShell**:
     ```powershell
     $env:TMPDIR="C:\Users\$env:USERNAME\Documents\science-tmp"
     New-Item -ItemType Directory -Force -Path $env:TMPDIR
     ```
   - **Linux / macOS**:
     ```bash
     export TMPDIR="$HOME/science-tmp"
     mkdir -p "$TMPDIR"
     ```

   `tempfile.gettempdir()` 会优先使用 `TMPDIR` 环境变量。

---

### 3.4 文件编码问题

**症状**: 脚本输出中文乱码，或读取 JSON 配置文件时报 `UnicodeDecodeError`。

**原因**: Windows 控制台默认编码可能是 `cp936`（GBK），与 Python 3 默认的 UTF-8 不匹配。

**解决方案**:

1. 在运行 Python 脚本前，设置控制台编码为 UTF-8：

   - **PowerShell**:
     ```powershell
     [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
     $env:PYTHONIOENCODING = "utf-8"
     ```
   - **CMD**:
     ```cmd
     chcp 65001
     set PYTHONIOENCODING=utf-8
     ```

2. 启用 Windows 全局 UTF-8 支持（Windows 10 1903+）：

   打开"设置" -> "时间和语言" -> "语言和区域" -> "管理语言设置" -> "更改系统区域设置" -> 勾选 "Beta 版: 使用 Unicode UTF-8 提供全球语言支持" -> 重启。

3. 在 PowerShell profile 中永久设置：

   ```powershell
   if (!(Test-Path $PROFILE)) { New-Item -ItemType File -Path $PROFILE -Force }
   Add-Content $PROFILE '$env:PYTHONIOENCODING = "utf-8"'
   ```

4. 所有 Science Skills 的 JSON 配置文件（`config/network_profiles/*.json`）和诊断输出均使用 UTF-8 编码，确保编辑时也用 UTF-8 保存。

---

<a id="doctor-usage"></a>

## 4. 诊断工具使用

### 4.1 Science Doctor 概览

`tools/science_doctor.py` 是 Science Skills 的本地诊断工具，输出 JSON 格式的结构化报告。它不会读取或打印任何密钥（`.env` 内容、代理地址值等），Agent 可安全地解析使用。

**基本用法**:

| 命令 | 说明 |
|------|------|
| `python tools/science_doctor.py` | 全面诊断（本地 + 网络） |
| `python tools/science_doctor.py --no-network` | 仅本地检查，不访问网络 |
| `python tools/science_doctor.py --timeout 15` | 设置网络探测超时 15 秒（默认 10） |
| `python tools/science_doctor.py --root-dir D:\my-project` | 指定项目根目录（用于 `.env` 检测） |
| `python tools/science_doctor.py --auto-heal` | 自动修复（如自动安装缺失的 uv） |
| `python tools/science_doctor.py --fix` | `--auto-heal` 的别名 |

---

### 4.2 JSON 输出解读

诊断输出是一个 JSON 对象，包含 `status` 和 `checks` 两个顶层字段。

**顶层 status**: 整体健康状态：
- `"ok"` --- 所有检查通过。
- `"warn"` --- 存在警告但不影响基本使用。
- `"fail"` --- 存在严重问题，需立即处理。

**checks 字段**: 包含各项检查的详细结果，每项均有 `status`（`"ok"` / `"warn"` / `"fail"` / `"skip"`）和 `hint`（中文提示信息）。

| 检查项 | 说明 | 关键字段 |
|--------|------|----------|
| `python` | Python 版本和解释器路径 | `version`: 三位版本号（如 `"3.11.9"`）；`executable`: `python` 解释器的完整路径 |
| `uv` | uv 包管理器检测 | `path`: uv 可执行文件完整路径；`auto_installed`: 是否由 `--auto-heal` 自动安装 |
| `network_profile` | 网络 profile 加载状态 | `profile`: 激活的 profile 名；`sources`: 已配置的数据源列表 |
| `temp_lock` | 临时目录及锁文件写入 | `temp_dir`: 系统临时目录路径。若 `status` 为 `"fail"`，检查磁盘空间和权限 |
| `env_file` | `.env` 文件存在性 | `present`: `true` / `false`。诊断工具不会读取 `.env` 内容，仅检测是否存在 |
| `proxy` | 代理配置状态 | `configured`: `true` / `false`；`env`: 生效的代理变量名。不会打印代理地址的具体值 |
| `pubmed_api` | PubMed 官方 API 连通性 | `url`: 探测的 URL。仅在全网络扫描（非 `--no-network`）时执行 |
| `pdb_download_mirror` | PDBJ 镜像连通性 | `url`: 探测的 URL。仅在全网络扫描时执行 |

**JSON 输出示例**:

```json
{
  "status": "warn",
  "checks": {
    "python": {
      "status": "ok",
      "version": "3.11.9",
      "executable": "C:\\Python311\\python.exe"
    },
    "uv": {
      "status": "ok",
      "path": "C:\\Python311\\Scripts\\uv.exe",
      "auto_installed": false
    },
    "network_profile": {
      "status": "ok",
      "profile": "china",
      "sources": ["alphafold", "chembl", "openalex", "pdb", "pubmed", "..."]
    },
    "temp_lock": {
      "status": "ok",
      "temp_dir": "C:\\Users\\Alice\\AppData\\Local\\Temp"
    },
    "env_file": {
      "status": "ok",
      "present": false
    },
    "proxy": {
      "status": "ok",
      "hint": "未检测到代理；默认 china profile 已启用，代理仅作为高级排障选项。",
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

---

### 4.3 何时使用 `--no-network`

| 场景 | 建议 |
|------|------|
| 刚完成安装，只确认本地环境 | `--no-network`（快速，不触发防火墙） |
| 安装后首次全量检查 | 不带 `--no-network`（验证数据库连通性） |
| 在公司防火墙内，不确定外网是否可达 | 先用 `--no-network` 确认本地环境，再逐步加网络检查 |
| CI/CD 或自动化脚本中 | `--no-network` + `--auto-heal`（不依赖外部网络） |
| 网络故障排查 | 先用不带 `--no-network` 定位问题数据库，再针对性修复 |

---

### 4.4 何时使用 `--auto-heal`

`--auto-heal`（别名 `--fix`）允许诊断脚本执行自动修复操作。当前支持的自动修复：

1. **自动安装 uv**: 如果 uv 未安装，脚本会通过 `pip install uv` 自动安装。根据当前网络 profile 的 PyPI 配置选择镜像源（如 china profile 使用清华镜像）。
2. **自动生成 uv.toml**: 如果 profile 配置了 PyPI 镜像，脚本会在项目根目录自动生成 `uv.toml`，使后续 `uv pip install` 操作自动使用国内镜像。

推荐用法：

```powershell
$env:SCIENCE_NETWORK_PROFILE="china"
python tools/science_doctor.py --auto-heal
```

---

### 4.5 诊断工具返回值的含义

`science_doctor.py` 的退出码：

| 退出码 | 含义 |
|--------|------|
| `0` | 所有检查通过（status 为 `"ok"` 或 `"warn"`） |
| `1` | 至少一项检查失败（status 为 `"fail"`） |

可用于 CI/CD 脚本：

- **PowerShell**:
  ```powershell
  python tools/science_doctor.py --no-network
  if ($LASTEXITCODE -ne 0) { Write-Error "Diagnostics failed; check environment." }
  ```
- **bash**:
  ```bash
  python tools/science_doctor.py --no-network || { echo "Diagnostics failed; check environment."; exit 1; }
  ```

---

<a id="database-issues"></a>

## 5. 数据库特定问题

### 5.1 NCBI 速率限制 (HTTP 429)

**症状**: PubMed / NCBI 查询返回 HTTP 429 `Too Many Requests`，或诊断报告中显示 `HttpError: HTTP Error 429`。

**原因**: NCBI E-utilities 对无 API Key 的请求限制为 **每秒 3 次**（`qps=3`）。如果注册了 API Key，限制可提升到每秒 10 次。Science Skills 的 `HttpClient` 会对每个主机名维护跨进程速率限制器，但如果同时运行多个 Agent 或其他工具访问 NCBI，仍可能触发 429。

**解决方案**:

1. 确认 Science Skills 内置的速率限制生效。诊断不会触发速率限制（仅发 HEAD 请求 0 字节数据）。

2. 如果频繁触发 429，注册 NCBI API Key：
   - 访问 [NCBI API Key 管理页面](https://www.ncbi.nlm.nih.gov/account/settings/) 注册。
   - 注册后，设置环境变量 `NCBI_API_KEY`，或在查询 URL 中加入 `&api_key=<your_key>` 参数。

3. 脚本内置了自动重试机制：遇到 429 会以指数退避重试最多 7 次（首次 3 秒，最大 180 秒），并支持 `Retry-After` 头部。如果多次重试后仍失败，检查是否有其他程序在同时密集请求 NCBI。

4. 使用 Europe PMC 作为替代方案。默认 `china` profile 已配置此策略；如果曾切换 profile，请恢复为 `china`。

---

### 5.2 PDB mmCIF 下载失败

**症状**: 下载 `.cif.gz` 文件时超时、404 或文件损坏。

**原因**:
- **default profile**: 从 RCSB PDB (`files.rcsb.org`) 直接下载，国内可能慢。
- **china profile**: 通过 PDBJ 镜像下载，路径转换可能失败（如非标准 PDB ID 格式）。
- 大文件（如完整的 mmCIF 数据集）下载可能超过默认 60 秒超时。

**解决方案**:

1. 默认 `china` profile 已启用 PDBJ 镜像加速；如果曾切换 profile，请恢复为 `china`。

   PDBJ 镜像的文件路径格式与 RCSB 不同，`http_client.py` 中的 `_format_pdbj_divided_structure_url` 函数会自动进行路径转换。支持的格式：
   - `1cbs.cif.gz` -> `mmCIF/cb/1cbs.cif.gz`
   - `pdb_00001cbs.ent.gz` -> `pdb/cb/pdb1cbs.ent.gz`

   如果 PDB ID 格式异常（含非标准字符），转换可能失败并 fallback 到原始 URL，此时需检查 PDB ID 是否合法（应为 4 位字母数字，如 `1cbs`、`4hhb`）。

2. 对于大文件下载，增大超时（脚本中可将 `timeout` 参数设大，如 300 秒）。诊断工具也可调大超时：

   ```powershell
   python tools/science_doctor.py --timeout 30
   ```

3. 如果 PDBJ 也失败，尝试 PDBe (`https://www.ebi.ac.uk/pdbe/`) 作为第二替代源。

---

### 5.3 OpenAlex 礼貌池（Polite Pool）要求

**症状**: OpenAlex API 请求被限速或返回错误，提示需要提供 email。

**原因**: OpenAlex 对无身份标识的请求有更严格的速率限制。进入"礼貌池"（polite pool）需要提供联系邮箱，速度可达每秒 10 次请求；否则默认为匿名池，速度极低。

**解决方案**:

1. 配置 OpenAlex 礼貌池身份。在本机 `.env` 或终端环境中添加一个有效邮箱地址：

   ```powershell
   [Environment]::SetEnvironmentVariable("OPENALEX_MAILTO", "your-email@example.com", "User")
   ```

2. Science Skills 的 OpenAlex 技能脚本会把 `OPENALEX_MAILTO` 追加为 `mailto` 查询参数；日志中不打印该值。

3. 对于商业或高频使用，建议同时配置 `OPENALEX_API_KEY`。

---

### 5.4 PubChem QPS 限制

**症状**: PubChem PUG-REST API 返回 `X-Throttling-Control` 头部中含 `Red` 或 `Black` 状态，请求被严重限速或直接拒绝。

**原因**: PubChem 对 PUG-REST API 有实时速率限制，通过 `X-Throttling-Control` 头部实时反馈当前负载。状态含义：
- **Green** (<50%): 正常，无额外延迟。
- **Yellow** (50%-75%): 轻度拥堵，增加 1 秒延迟。
- **Red** (>75%): 严重拥堵，增加 5 秒延迟。
- **Black** (blocked): 超限封锁，增加 30 秒延迟。

Science Skills 的 `HttpClient` 会解析该头部并自动施加背压延迟（参见 `_THROTTLE_BACKPRESSURE` 字典），但这只能减缓症状，不能从根本上解决。

**解决方案**:

1. 让 `HttpClient` 自动处理背压。正常情况下不需要手动干预。

2. 如果频繁触发 Black 状态：
   - 降低 QPS（查询频率）。
   - 将批量请求分散到更长时间窗口。
   - 考虑使用 PubChem 的批量下载服务（FTP/HTTPS bulk download），而非逐条 API 查询。

3. PubChem 的替代源 ChEMBL (`https://www.ebi.ac.uk/chembl/`) 已配置为备选：

   ```powershell
   $env:SCIENCE_NETWORK_PROFILE="china"
   ```

---

<a id="windows-issues"></a>

## 6. Windows 特定问题

### 6.1 PowerShell 执行策略

**症状**: 运行 `.ps1` 脚本时报 `running scripts is disabled on this system` 或无法执行 PowerShell 脚本。

**原因**: Windows PowerShell 默认执行策略为 `Restricted`，禁止运行任何脚本。

**解决方案**:

1. 查看当前执行策略：

   ```powershell
   Get-ExecutionPolicy
   ```

2. 如果是 `Restricted`，修改为 `RemoteSigned`（允许本地脚本运行）：

   ```powershell
   Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

   注意：可能需要以管理员身份运行 PowerShell。

3. 如果企业策略禁止修改，可以逐次绕过：

   ```powershell
   powershell -ExecutionPolicy Bypass -File .\your-script.ps1
   ```

   Science Skills 的 Python 脚本不依赖 PowerShell 执行策略（直接调用 `python`），但部分辅助脚本或安装脚本可能涉及。

---

### 6.2 路径过长 (Path Too Long)

**症状**: 文件操作时报 `FileNotFoundError`、`OSError: [Errno 2]` 或 Windows 资源管理器无法访问某路径。

**原因**: Windows 传统 API 限制路径长度为 260 字符（`MAX_PATH`）。Science Skills 的锁文件位于 `%TEMP%`（通常如 `C:\Users\<长用户名>\AppData\Local\Temp\`），如果用户名或项目路径较长，加上文件名后可能超限。

**解决方案**:

**方案 A --- 启用 Windows 长路径支持**（推荐，Windows 10 1607+）：

> **警告**: 下面的设置会修改 `HKLM` 系统级注册表，影响本机所有应用。修改前请确认已具备管理员权限，并先创建还原点或导出注册表备份。

1. 以管理员身份运行 PowerShell，先创建还原点并导出注册表备份：

   ```powershell
   Checkpoint-Computer -Description "Before enabling Windows long paths" -RestorePointType "MODIFY_SETTINGS"
   reg export "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" "$env:USERPROFILE\Desktop\FileSystem.reg" /y
   ```

2. 确认备份成功后再启用长路径支持：

   ```powershell
   New-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem" -Name "LongPathsEnabled" -Value 1 -PropertyType DWORD -Force
   ```

3. 重启计算机。

**方案 B --- 缩短路径**：

1. 将项目克隆到短路径，如 `C:\ssp\`。
2. Python 3.6+ 在 Windows 上会自动处理长路径（通过 `\\?\` 前缀），但某些场景仍需手动处理。

**方案 C --- 使用短路径访问**：

- **PowerShell**:
  ```powershell
  (New-Object -ComObject Scripting.FileSystemObject).GetFolder("C:\Users\VeryLongName").ShortPath
  ```

---

### 6.3 路径中的 Unicode / 中文

**症状**: 当 Windows 用户名或项目路径包含中文字符时，Python 报 `UnicodeEncodeError` 或 `OSError`。

**原因**: 虽然 Python 3 默认使用 UTF-8 处理字符串，但某些 Windows API 和底层库（如 `msvcrt` 文件锁）可能使用系统默认编码（GBK/`cp936`）处理路径。

**解决方案**:

1. 设置 Python 的编码环境变量：

   ```powershell
   $env:PYTHONUTF8 = "1"
   $env:PYTHONIOENCODING = "utf-8"
   ```

2. 启用 Windows 全局 UTF-8 支持（参见 3.4 节）。

3. 如果仍有问题，考虑将项目移动到纯 ASCII 路径，或创建一个不含中文的 Windows 用户账户用于科研工作。

4. 通过诊断工具验证临时目录路径不含乱码：

   ```powershell
   python tools/science_doctor.py --no-network
   ```
   检查 `checks.temp_lock.temp_dir` 字段的路径是否正常显示。

---

### 6.4 文件锁兼容性

**症状**: 在多进程环境下（如同时运行多个 Agent 的 Python 脚本），偶尔出现 `PermissionError` 或锁争用错误。

**原因**: Science Skills 的 `_RateLimiter` 使用跨平台文件锁实现速率限制。在 Windows 上使用 `msvcrt.locking`（基于 `LockFileEx` API），在 Unix 上使用 `fcntl.flock`。两种实现的行为差异可能导致极端情况下的竞态条件。

**解决方案**:

1. 确保杀毒软件不会扫描或锁定 `%TEMP%\science-skills-*.lock` 文件。将 `%TEMP%` 目录或 `science-skills-*.lock` 模式添加到实时扫描排除列表。

2. 如果问题持续出现：
   - 避免同时运行多个 Science Skills 进程访问同一数据库。
   - 进程结束后，手动清理残留锁文件（参见 3.2 节第 4 步）。

3. 锁文件是自清理的（每个进程结束后释放），但如果进程异常终止（如强制结束），锁文件可能残留。这种情况下直接删除锁文件即可，它们不包含任何持久化数据。

---

## 参考信息

### 环境变量汇总

| 变量名 | 用途 | 可选值 |
|--------|------|--------|
| `SCIENCE_NETWORK_PROFILE` | 激活的网络策略 profile | `china`（国内优化，默认）、`base`（仅官方源）。`enterprise`（企业内网）仅在商业企业版中提供。默认值为 `china` |
| `SCIENCE_PROXY` | 专属 HTTP(S) 代理地址 | `http://127.0.0.1:7890` |
| `SCIENCE_NETWORK_PROFILE_DIR` | 自定义 profile 文件目录 | 绝对路径，如 `/opt/profiles` |
| `SCIENCE_SKILLS_USER_AGENT` | 自定义 HTTP User-Agent 头 | 任意字符串 |

### 网络 Profile 文件位置

开源免费版交付的是**预合并后的**完整 profile 文件 `config/network_profiles/default.json` 与 `china.json`。运行时直接读取这些 JSON，不再涉及 overlay 合并。商业版构建链路使用 base + overlay 架构（base.json + `<profile>.overlay.json`），但这部分不在开源仓内。

运行时加载优先级为：
1. `SCIENCE_NETWORK_PROFILE_DIR` 指定的目录（如果设置了该环境变量）。
2. 包内资源 `skills/science_skills_common/network_profiles/`（预合并的完整 JSON）。
3. 项目根目录 `config/network_profiles/`（作为 fallback）。

注意：运行时只读取合并后的 `{name}.json`，不读取 `.overlay.json` 文件。`config/network_profiles/archive/` 中保留了旧版完整 profile 文件供历史参考，不再用于运行时。

### 诊断工具网络探测细节

- **PubMed**: 发送 HEAD 请求到 `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/einfo.fcgi?db=pubmed`。如果 HEAD 失败，fallback 到 GET 请求（Range: bytes=0-0），只取 0 字节。不会触发 NCBI 速率限制。
- **PDBJ 镜像**: 发送 HEAD 请求到 PDBJ 上的一个已知小文件 `1cbs.cif.gz`。同样有 GET fallback 的 0 字节请求策略。

### 联系与反馈

如果在本文档中未找到你的问题，请先运行完整诊断并保留 JSON 输出：

```powershell
python tools/science_doctor.py > doctor_report.json 2>&1
```

然后在 GitHub 上提交 Issue 并附上 `doctor_report.json`（报告不包含密钥或代理地址值）。

---

**Science Skills --- 面向国内科研用户的 Agent 科研数据库工作流增强包**
