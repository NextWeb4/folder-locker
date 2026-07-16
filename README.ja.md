[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md)

# Folder Locker

認証付き暗号化コンテナと、任意の NTFS quick-lock mode を備えた、オフライン Windows フォルダー保護アプリです。

![最終コミット](https://img.shields.io/github/last-commit/NextWeb4/folder-locker?style=flat-square)
![リポジトリサイズ](https://img.shields.io/github/repo-size/NextWeb4/folder-locker?style=flat-square)
![GitHub Stars](https://img.shields.io/github/stars/NextWeb4/folder-locker?style=flat-square)
![Python 3.10 以降](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![MIT ライセンス](https://img.shields.io/github/license/NextWeb4/folder-locker?style=flat-square)

## 保護モード

### 暗号化コンテナ（推奨）

Folder Locker は元フォルダーを `.locked` コンテナへコピーします。PBKDF2-HMAC-SHA256 で鍵を導出し、ファイル名とファイルデータを AES-256-GCM でストリーム認証暗号化します。

- `.locked` コンテナの作成と復元
- 対応する旧コンテナ形式の読み込み
- symbolic link と危険なパスの拒否
- 復元時の path traversal 防止
- 認証または復元に失敗した場合の不完全な出力ディレクトリの除去
- 暗号化後も元フォルダーを意図的に保持

元フォルダーを自分で削除する前に、実際に復元してファイルを確認してください。パスワードを忘れると復元できません。

### Windows quick lock（上級者向け）

任意の quick mode は NTFS ACL deny rule と名前の難読化で、現在のユーザーからのアクセスを制限します。名前と権限を戻すための metadata と rollback 処理があります。

これは**暗号化ではありません**。管理者、所有者、ACL の知識があるユーザーは回避できる可能性があります。機密性が必要な場合は暗号化コンテナを使用してください。

## その他の機能

- 中国語/英語の Tkinter UI
- `src/utility_suite/settings.py` に保存するローカル言語設定
- バックグラウンド処理と進捗表示
- サーバー、アカウント、テレメトリー、ブラウザ、実行時ネットワークを必要としない完全オフライン動作
- Windows 単一 EXE、portable ZIP、SHA256 のリリース出力

## 必要環境とソース実行

- Python 3.10 以降
- Tkinter アプリ、NTFS quick lock、配布 EXE は Windows 向け
- 実行時依存 `cryptography>=42`

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m folder_locker.app
```

quick-lock tab は Windows/NTFS 専用です。暗号化コンテナ機能も、このリポジトリでは Windows デスクトップアプリとして提供されます。

## 使い方

### 暗号化コンテナの作成

1. **Encrypted container (recommended)** を開きます。
2. 元フォルダーと出力先 `.locked` ファイルを選びます。
3. パスワードを入力して確認します。
4. コンテナを作成します。
5. 別の場所へ復元して内容を確認してから、必要な削除を手動で行います。

### コンテナの復元

1. `.locked` ファイルを選びます。
2. 新しい復元先ディレクトリを選びます。
3. パスワードを入力して復元します。

### quick lock の適用と解除

1. **Windows quick lock (advanced)** を開きます。
2. 対象フォルダーを選び、パスワードを入力・確認してロックします。
3. 解除時は同じフォルダーと metadata に対応するパスワードを指定します。

ドライブのルート、symbolic link、独立した復旧手段がない重要フォルダーは対象にしないでください。

## テストと検証

```powershell
$env:PYTHONPATH = "src"
python -m unittest discover -s tests -v
python -m compileall -q src scripts tests
.\tests\run_ui_smoke.ps1
```

対話デスクトップがない場合に限り `.\tests\run_ui_smoke.ps1 -SkipLaunch` を使用します。独立した lint/format コマンドはありません。

## リリースビルド

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build.ps1
```

ビルドスクリプトは test と `compileall` を行い、PyInstaller 6.20.0 で次を生成します。

```text
release-assets\folder-locker-v1.0.0-windows-x64.exe
release-assets\folder-locker-v1.0.0-windows-x64.zip
release-assets\SHA256SUMS.txt
```

インストーラープロジェクトがないため MSI は作りません。EXE はデジタル署名されていないので、`SHA256SUMS.txt` で確認してください。portable ZIP には EXE、README、LICENSE、third-party notices が含まれます。

## プロジェクト構成

| パス | 役割 |
| --- | --- |
| `src/folder_locker/core.py` | コンテナ形式、PBKDF2/AES-GCM、安全なパス、名前難読化、ACL command、metadata、rollback |
| `src/folder_locker/app.py` | 二言語 Tkinter UI、入力検証、background worker、進捗、message |
| `src/utility_suite/` | アプリ識別情報とローカル言語設定のみ |
| `tests/test_folder_locker.py` | コンテナ、パス、ACL、失敗動作の regression test |
| `tests/run_ui_smoke.ps1` | ビルド済み GUI、ZIP、metadata の smoke test |
| `scripts/build.ps1` | test、compile、PyInstaller、portable ZIP、checksum |
| `resources/folder-locker-version.txt` | Windows EXE の version resource |
| `docs/open-source-audit.md` | 依存、ライセンス、互換性、package の監査 |

## データ安全性

- 暗号化処理は元フォルダーを自動削除・上書きしません。
- 復元では認証を行い、すべての出力パスを選択した復元先の内側に制限しなければなりません。
- パスワード、導出鍵、ローカルパス、コンテナ内容、ACL metadata をログ、Git、リリース archive に含めないでください。
- 容易な復旧には quick-lock metadata が必要です。不用意に削除しないでください。
- 未署名の PyInstaller EXE は Windows SmartScreen やセキュリティ製品に警告される場合があります。version metadata はデジタル署名の代わりではありません。

## 作者

- HaoXiang Huang
- [didadida1688@gmail.com](mailto:didadida1688@gmail.com)
- <https://nextweb4.github.io/>
- <https://github.com/NextWeb4>

## ライセンス

Folder Locker は [MIT License](LICENSE) です。`cryptography` は Apache-2.0 または BSD、PyInstaller は bootloader exception 付き GPL-2.0-or-later です。詳細は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。
