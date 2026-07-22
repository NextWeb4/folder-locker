<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/English-0969da?style=flat-square" alt="English"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-c8102e?style=flat-square" alt="简体中文"></a>
  <a href="README.ja.md"><img src="https://img.shields.io/badge/%E6%97%A5%E6%9C%AC%E8%AA%9E-8250df?style=flat-square" alt="日本語"></a>
</p>

# Folder Locker

一个离线 Windows 文件夹保护应用，提供认证加密容器和可选的 NTFS 快速锁定模式。

![最近提交](https://img.shields.io/github/last-commit/NextWeb4/folder-locker?style=flat-square)
![仓库大小](https://img.shields.io/github/repo-size/NextWeb4/folder-locker?style=flat-square)
![GitHub 星标](https://img.shields.io/github/stars/NextWeb4/folder-locker?style=flat-square)
![Python 3.10 或更高版本](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![MIT 许可证](https://img.shields.io/github/license/NextWeb4/folder-locker?style=flat-square)

## 保护模式

### 加密容器（推荐）

Folder Locker 会把源文件夹复制到 `.locked` 容器，使用 PBKDF2-HMAC-SHA256 派生密钥，并通过 AES-256-GCM 对文件名和文件数据进行流式认证加密。

- 创建并恢复 `.locked` 容器。
- 读取受支持的旧版容器。
- 拒绝符号链接和不安全路径。
- 恢复时防止路径穿越。
- 身份验证或恢复失败时不保留半成品目录。
- 加密完成后刻意保留源文件夹。

请先实际恢复并验证文件，再自行删除源文件夹。忘记密码后无法恢复加密内容。

### Windows 快速锁定（高级）

快速模式通过 NTFS ACL 拒绝规则和名称混淆限制当前用户访问，并使用元数据与回滚逻辑恢复名称和权限。

该模式**不是加密**。管理员、所有者或熟悉 ACL 的用户可能绕过它。需要保密时应使用加密容器模式。

## 其他功能

- 中英文双语 Tkinter UI。
- `src/utility_suite/settings.py` 保存本机语言偏好。
- 后台文件操作和进度反馈。
- 完全离线，不需要服务端、账号、遥测、浏览器或运行时网络。
- 生成 Windows 单文件 EXE、便携 ZIP 和 SHA256 校验值。

## 环境要求与源码运行

- Python 3.10 或更高版本。
- Tkinter 应用、NTFS 快速锁和打包版面向 Windows。
- 运行时依赖 `cryptography>=42`。

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m folder_locker.app
```

快速锁标签仅适用于 Windows/NTFS；本仓库中的加密容器功能同样通过 Windows 桌面应用提供。

## 使用方法

### 创建加密容器

1. 打开“加密容器（推荐）”。
2. 选择源文件夹和目标 `.locked` 文件。
3. 输入并确认密码。
4. 创建容器。
5. 恢复到另一个目录并验证文件，之后再手动删除任何内容。

### 恢复容器

1. 选择 `.locked` 文件。
2. 选择新的恢复目录。
3. 输入密码并开始恢复。

### 应用或解除快速锁

1. 打开“Windows 快速锁定（高级）”。
2. 选择目标文件夹，输入并确认密码后加锁。
3. 解锁时选择同一文件夹，并输入该元数据对应的密码。

不要选择磁盘根目录、符号链接，或无法独立恢复其内容的文件夹。

## 测试与验证

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q src scripts tests
.\tests\run_ui_smoke.ps1
```

只有在没有交互式桌面时才使用 `.\tests\run_ui_smoke.ps1 -SkipLaunch`。当前没有独立的 lint 或 format 命令。

## 构建发布版

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
powershell -ExecutionPolicy Bypass -File scripts/build.ps1 -Python .\.venv\Scripts\python.exe
```

构建脚本先运行测试和 `compileall`，再使用 PyInstaller 6.20.0 生成：

```text
release-assets\folder-locker-v1.0.0-windows-x64.exe
release-assets\folder-locker-v1.0.0-windows-x64.zip
release-assets\SHA256SUMS.txt
```

仓库没有安装器工程，因此不生成 MSI。发布 EXE 未进行数字签名，请使用 `SHA256SUMS.txt` 校验下载文件。便携 ZIP 包含 EXE、README、LICENSE 和第三方声明。

## 项目结构

| 路径 | 职责 |
| --- | --- |
| `src/folder_locker/core.py` | 容器格式、PBKDF2/AES-GCM、安全路径、名称混淆、ACL 命令、元数据和回滚 |
| `src/folder_locker/app.py` | 双语 Tkinter UI、校验、后台线程、进度和消息 |
| `src/utility_suite/` | 仅保存应用身份和本机语言设置 |
| `tests/test_folder_locker.py` | 容器、路径、ACL 和失败行为回归测试 |
| `tests/run_ui_smoke.ps1` | 构建后 GUI、ZIP 和元数据冒烟测试 |
| `scripts/build.ps1` | 测试、编译、PyInstaller、便携 ZIP 和校验流水线 |
| `resources/folder-locker-version.txt` | Windows EXE 版本资源 |
| `docs/open-source-audit.md` | 依赖、许可证、兼容性和打包审计 |

## 数据安全

- 加密流程不会自动删除或覆盖源文件夹。
- 容器恢复必须验证数据，并把每个输出路径限制在所选目标目录内。
- 密码、派生密钥、本机路径、容器内容和 ACL 元数据不得进入日志、源码仓库或发布包。
- 快速恢复依赖锁定元数据，不要随意删除。
- 未签名 PyInstaller EXE 可能触发 Windows SmartScreen 或安全软件提示；版本元数据不等同于数字签名。

## 维护与贡献

- 加密、容器兼容、安全恢复、ACL 或回滚修改应放在 `src/folder_locker/core.py`，并在 `tests/test_folder_locker.py` 增加针对性用例；Tkinter 层只负责界面与后台任务编排。
- 中英文应用文案必须同步；行为、命令、产物、安全限制或许可变化时，三份 README 也必须保持一致。
- 审查前运行单元测试、`compileall` 和适用的 UI 冒烟；发布工作还需要重建 EXE/ZIP、检查内容与元数据，并验证 `SHA256SUMS.txt`。
- 修改依赖或打包前先查看[开源审计](docs/open-source-audit.md)，并保持运行时完全离线。

## 作者

- HaoXiang Huang
- [Rays688888@Gmail.com](mailto:Rays688888@Gmail.com)
- <https://nextweb4.github.io/>
- <https://github.com/NextWeb4>

## 许可证

Folder Locker 使用 [MIT License](LICENSE)。`cryptography` 使用 Apache-2.0 或 BSD 条款；PyInstaller 使用带引导程序例外的 GPL-2.0-or-later。详见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。


