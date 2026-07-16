[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

# Folder Locker

An offline Windows folder-protection application with authenticated encrypted containers and an optional NTFS quick-lock mode.

![Last commit](https://img.shields.io/github/last-commit/NextWeb4/folder-locker?style=flat-square)
![Repository size](https://img.shields.io/github/repo-size/NextWeb4/folder-locker?style=flat-square)
![GitHub stars](https://img.shields.io/github/stars/NextWeb4/folder-locker?style=flat-square)
![Python 3.10 or newer](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![MIT License](https://img.shields.io/github/license/NextWeb4/folder-locker?style=flat-square)

## Protection Modes

### Encrypted container (recommended)

Folder Locker copies a source folder into a `.locked` container. It derives a key with PBKDF2-HMAC-SHA256 and streams filenames and file data through AES-256-GCM authenticated encryption.

- Creates and restores `.locked` containers.
- Reads supported legacy container versions.
- Rejects symbolic links and unsafe paths.
- Prevents archive path traversal during restore.
- Avoids leaving a partial output directory when authentication or restoration fails.
- Deliberately keeps the source folder after encryption.

Verify a real restore before deleting the source yourself. A forgotten password cannot be recovered.

### Windows quick lock (advanced)

The optional quick mode applies an NTFS ACL deny rule and obfuscates names to restrict the current user's access. It includes metadata and rollback behavior so it can restore names and permissions.

This mode is **not encryption**. Administrators, owners, or users who understand ACLs may bypass it. Use the encrypted container mode for confidentiality.

## Other Features

- Bilingual Chinese/English Tkinter UI.
- Local language preference stored by `src/utility_suite/settings.py`.
- Background file operations with progress reporting.
- Fully offline operation with no server, account, telemetry, browser, or runtime network requirement.
- Windows single-file EXE, portable ZIP, and SHA256 release output.

## Requirements and Source Setup

- Python 3.10 or newer.
- Windows for the Tkinter application, NTFS quick lock, and packaged executable.
- `cryptography>=42` at runtime.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m folder_locker.app
```

The quick-lock tab is Windows/NTFS-specific. The encrypted container implementation is still presented by a Windows desktop application in this repository.

## Use

### Create an encrypted container

1. Open **Encrypted container (recommended)**.
2. Select the source folder and destination `.locked` file.
3. Enter and confirm a password.
4. Create the container.
5. Restore it to a separate folder and verify the files before deleting anything manually.

### Restore a container

1. Select the `.locked` file.
2. Choose a new restore directory.
3. Enter the password and start restoration.

### Apply or remove a quick lock

1. Open **Windows quick lock (advanced)**.
2. Choose the target folder and enter/confirm the password to lock it.
3. To unlock it, select the same folder and enter the password used for its metadata.

Do not use a drive root, symbolic link, or folder whose contents you cannot afford to recover independently.

## Test and Verify

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m compileall -q src scripts tests
.\tests\run_ui_smoke.ps1
```

Use `.\tests\run_ui_smoke.ps1 -SkipLaunch` only when no interactive desktop is available. There is no separate lint or format command.

## Build a Release

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```

The build script runs tests and `compileall`, then uses PyInstaller 6.20.0 to create:

```text
release-assets\folder-locker-v1.0.0-windows-x64.exe
release-assets\folder-locker-v1.0.0-windows-x64.zip
release-assets\SHA256SUMS.txt
```

No MSI is generated because the repository has no installer project. Release executables are not digitally signed; verify downloads with `SHA256SUMS.txt`. The portable ZIP contains the EXE, README, LICENSE, and third-party notices.

## Project Structure

| Path | Responsibility |
| --- | --- |
| `src/folder_locker/core.py` | Container format, PBKDF2/AES-GCM, safe paths, name obfuscation, ACL commands, metadata, and rollback |
| `src/folder_locker/app.py` | Bilingual Tkinter UI, validation, background workers, progress, and messages |
| `src/utility_suite/` | Application identity and local language settings only |
| `tests/test_folder_locker.py` | Container, path, ACL, and failure-behavior regression coverage |
| `tests/run_ui_smoke.ps1` | Built GUI, ZIP, and metadata smoke checks |
| `scripts/build.ps1` | Test, compile, PyInstaller, portable ZIP, and checksum pipeline |
| `resources/folder-locker-version.txt` | Windows executable version resources |
| `docs/open-source-audit.md` | Dependency, license, compatibility, and packaging audit |

## Data Safety and Security

- Encryption never deletes or overwrites the source folder automatically.
- Container restoration must authenticate data and constrain every output path to the chosen destination.
- Passwords, derived keys, local paths, container contents, and ACL metadata must not enter logs, source control, or release archives.
- Quick-lock metadata is required for straightforward recovery; do not delete it casually.
- Unsigned PyInstaller executables may trigger Windows SmartScreen or antivirus warnings. Metadata is not a substitute for a digital signature.

## Author

- HaoXiang Huang
- [didadida1688@gmail.com](mailto:didadida1688@gmail.com)
- <https://nextweb4.github.io/>
- <https://github.com/NextWeb4>

## License

Folder Locker is licensed under the [MIT License](LICENSE). `cryptography` is distributed under Apache-2.0 or BSD terms; PyInstaller uses GPL-2.0-or-later with a bootloader exception. See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
