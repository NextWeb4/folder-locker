# Folder Locker

## 中文

Folder Locker 是一个离线 Windows 文件夹上锁工具，包含两种模式：

1. **强加密容器模式（推荐）**：把文件夹内容复制进 `.locked` 容器，使用 PBKDF2-HMAC-SHA256 派生密钥，并用 AES-256-GCM 流式加密文件名和文件数据。
2. **Windows 快速权限锁模式（高级）**：使用 NTFS ACL deny 权限和文件名混淆快速限制当前用户访问。此模式不是加密。

强加密容器模式会保留原文件夹，避免误操作导致数据丢失。请先确认容器可以成功解密恢复，再自行删除原文件夹。

### 功能特点

- 创建 AES-256-GCM `.locked` 加密容器。
- 从 `.locked` 容器恢复文件夹。
- 支持旧版容器读取。
- Windows NTFS 快速权限锁和解除锁定。
- 路径穿越防护、符号链接拒绝和失败回滚。
- 中英文 UI 切换，语言偏好保存在本机。
- 完全离线运行，不需要服务端、账号或网络连接。

### 安装方法

下载 Release 中的 `folder-locker-v1.0.0-windows-x64.exe` 后直接运行，或下载 `folder-locker-v1.0.0-windows-x64.zip` 解压后运行其中的 EXE。

EXE 未进行数字签名。请使用 Release 中的 `SHA256SUMS.txt` 校验文件完整性。

### 使用方法

#### 强加密容器

1. 打开“加密容器（推荐）”标签。
2. 选择源文件夹。
3. 设置 `.locked` 容器输出路径。
4. 输入并确认密码。
5. 点击“创建加密容器”。
6. 需要恢复时选择 `.locked` 文件、恢复目录和密码，点击“解密并恢复”。

忘记密码无法恢复加密容器。

#### Windows 快速权限锁

1. 打开“Windows 快速锁定（高级）”标签。
2. 选择目标文件夹。
3. 输入并确认密码。
4. 点击“应用快速锁定”。
5. 解锁时选择同一文件夹并输入密码，点击“解除快速锁定”。

此模式只修改 NTFS 权限并混淆名称，不加密文件内容。

### 打包说明

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```

构建脚本会先运行测试和 `compileall`，再使用 PyInstaller 生成 Windows 单文件 EXE、便携 ZIP 和 SHA256 校验文件。

### 作者信息

- Author: HaoXiang Huang
- Email: didadida1688@gmail.com
- Homepage: https://nextweb4.github.io/
- GitHub: https://github.com/NextWeb4

### License

MIT License

## English

Folder Locker is an offline Windows folder locking tool with two modes:

1. **Strong encrypted container mode (recommended)**: copies a folder into a `.locked` container, derives a key with PBKDF2-HMAC-SHA256, and streams filenames and file data through AES-256-GCM.
2. **Windows quick permission lock mode (advanced)**: uses an NTFS ACL deny rule and filename obfuscation to restrict the current user's access quickly. This mode is not encryption.

The encrypted container mode deliberately keeps the source folder to prevent data loss. Verify that the container restores correctly before deleting the source yourself.

### Features

- Create AES-256-GCM `.locked` encrypted containers.
- Restore folders from `.locked` containers.
- Read legacy containers.
- Apply and remove Windows NTFS quick locks.
- Path traversal protection, symlink rejection, and rollback on failure.
- Switch between Chinese and English; the preference is stored locally.
- Fully offline; no server, account, or network connection is required.

### Installation

Download `folder-locker-v1.0.0-windows-x64.exe` from the Release page and run it directly, or download `folder-locker-v1.0.0-windows-x64.zip`, extract it, and run the EXE inside.

The EXE is not digitally signed. Verify file integrity with `SHA256SUMS.txt` from the Release page.

### Usage

#### Strong Encrypted Container

1. Open the "Encrypted container (recommended)" tab.
2. Choose the source folder.
3. Set the `.locked` container output path.
4. Enter and confirm a password.
5. Click "Create encrypted container".
6. To restore, choose the `.locked` file, output folder, and password, then click "Decrypt and restore".

Forgotten passwords cannot be recovered.

#### Windows Quick Permission Lock

1. Open the "Windows quick lock (advanced)" tab.
2. Choose the target folder.
3. Enter and confirm a password.
4. Click "Apply quick lock".
5. To unlock, choose the same folder and enter the password, then click "Remove quick lock".

This mode only changes NTFS permissions and obfuscates names. It does not encrypt file contents.

### Packaging

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```

The build script runs tests and `compileall`, then uses PyInstaller to create a Windows single-file EXE, portable ZIP, and SHA256 checksums.

### Author

- Author: HaoXiang Huang
- Email: didadida1688@gmail.com
- Homepage: https://nextweb4.github.io/
- GitHub: https://github.com/NextWeb4

### License

MIT License
