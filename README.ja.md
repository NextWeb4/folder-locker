<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/English-0969da?style=flat-square" alt="English"></a>
  <a href="README.zh-CN.md"><img src="https://img.shields.io/badge/%E7%AE%80%E4%BD%93%E4%B8%AD%E6%96%87-c8102e?style=flat-square" alt="简体中文"></a>
  <a href="README.ja.md"><img src="https://img.shields.io/badge/%E6%97%A5%E6%9C%AC%E8%AA%9E-8250df?style=flat-square" alt="日本語"></a>
</p>

# Folder Locker

認証付き暗号化コンテナと、任意の NTFS クイックロックモードを備えた、オフライン Windows フォルダー保護アプリです。

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
- シンボリックリンクと危険なパスの拒否
- 復元時のパストラバーサル防止
- 認証または復元に失敗した場合の不完全な出力ディレクトリの除去
- 暗号化後も元フォルダーを意図的に保持

元フォルダーを自分で削除する前に、実際に復元してファイルを確認してください。パスワードを忘れると復元できません。

### Windows quick lock（上級者向け）

任意のクイックモードは NTFS ACL の拒否規則と名前の難読化で、現在のユーザーからのアクセスを制限します。名前と権限を戻すためのメタデータとロールバック処理があります。

これは**暗号化ではありません**。管理者、所有者、ACL の知識があるユーザーは回避できる可能性があります。機密性が必要な場合は暗号化コンテナを使用してください。

## その他の機能

- 中国語/英語の Tkinter UI
- `src/utility_suite/settings.py` に保存するローカル言語設定
- バックグラウンド処理と進捗表示
- サーバー、アカウント、テレメトリー、ブラウザ、実行時ネットワークを必要としない完全オフライン動作
- Windows 単一 EXE、ポータブル ZIP、SHA256 のリリース出力

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

クイックロックタブは Windows/NTFS 専用です。暗号化コンテナ機能も、このリポジトリでは Windows デスクトップアプリとして提供されます。

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

### クイックロックの適用と解除

1. **Windows quick lock (advanced)** を開きます。
2. 対象フォルダーを選び、パスワードを入力・確認してロックします。
3. 解除時は同じフォルダーとメタデータに対応するパスワードを指定します。

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

ビルドスクリプトはテストと `compileall` を行い、PyInstaller 6.20.0 で次を生成します。

```text
release-assets\folder-locker-v1.0.0-windows-x64.exe
release-assets\folder-locker-v1.0.0-windows-x64.zip
release-assets\SHA256SUMS.txt
```

インストーラープロジェクトがないため MSI は作りません。EXE はデジタル署名されていないので、`SHA256SUMS.txt` で確認してください。ポータブル ZIP には EXE、README、LICENSE、第三者ライセンス通知が含まれます。

## プロジェクト構成

| パス | 役割 |
| --- | --- |
| `src/folder_locker/core.py` | コンテナ形式、PBKDF2/AES-GCM、安全なパス、名前難読化、ACL コマンド、メタデータ、ロールバック |
| `src/folder_locker/app.py` | 二言語 Tkinter UI、入力検証、バックグラウンド処理、進捗、メッセージ |
| `src/utility_suite/` | アプリ識別情報とローカル言語設定のみ |
| `tests/test_folder_locker.py` | コンテナ、パス、ACL、失敗動作の回帰テスト |
| `tests/run_ui_smoke.ps1` | ビルド済み GUI、ZIP、メタデータのスモークテスト |
| `scripts/build.ps1` | テスト、コンパイル確認、PyInstaller、ポータブル ZIP、チェックサム |
| `resources/folder-locker-version.txt` | Windows EXE のバージョンリソース |
| `docs/open-source-audit.md` | 依存関係、ライセンス、互換性、パッケージの監査 |

## データ安全性

- 暗号化処理は元フォルダーを自動削除・上書きしません。
- 復元では認証を行い、すべての出力パスを選択した復元先の内側に制限しなければなりません。
- パスワード、導出鍵、ローカルパス、コンテナ内容、ACL メタデータをログ、Git、リリースアーカイブに含めないでください。
- 容易な復旧にはクイックロックのメタデータが必要です。不用意に削除しないでください。
- 未署名の PyInstaller EXE は Windows SmartScreen やセキュリティ製品に警告される場合があります。バージョンメタデータはデジタル署名の代わりではありません。

## 保守とコントリビューション

- 暗号処理、コンテナ互換性、安全な復元、ACL、ロールバックの変更は `src/folder_locker/core.py` に置き、`tests/test_folder_locker.py` に対象を絞ったテストを追加してください。Tkinter 層は画面表示とバックグラウンド処理の調整だけを担当します。
- 中国語と英語のアプリ文言を同期し、動作、コマンド、成果物、セキュリティ上の制約、ライセンス情報を変えた場合は 3 言語の README も揃えてください。
- レビュー前に単体テスト、`compileall`、該当する UI スモークテストを実行します。リリース作業では EXE/ZIP を再ビルドし、内容とメタデータを検査して `SHA256SUMS.txt` を確認してください。
- 依存関係やパッケージを変更する前に[オープンソース監査](docs/open-source-audit.md)を確認し、実行時の完全オフライン動作を維持してください。

## 作者

- HaoXiang Huang
- [didadida1688@gmail.com](mailto:didadida1688@gmail.com)
- <https://nextweb4.github.io/>
- <https://github.com/NextWeb4>

## ライセンス

Folder Locker は [MIT License](LICENSE) です。`cryptography` は Apache-2.0 または BSD、PyInstaller は bootloader exception 付き GPL-2.0-or-later です。詳細は [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) を参照してください。
