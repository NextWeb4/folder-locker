# AGENTS.md

## 1. Project structure

- `src/folder_locker/core.py` owns container formats, cryptography, path validation, name obfuscation, ACL calls, metadata, and rollback.
- `src/folder_locker/app.py` owns the bilingual Tkinter UI, validation, background workers, progress, and user messages.
- `src/utility_suite/` stores application identity and local language preference only.
- `tests/`, `scripts/`, `resources/`, and `docs/open-source-audit.md` own regression coverage, release tooling, executable metadata, and dependency decisions respectively.
- Generated artifacts belong only in ignored `release-assets/` and build directories.

## 2. Run commands

- Set `$env:PYTHONPATH='src'`, then run `python -m folder_locker.app`.
- Install runtime dependencies from `requirements.txt`; do not assume the build-only `requirements-dev.txt` is needed for normal execution.
- GUI operation must remain offline and must not require a browser, account, server, telemetry, or remote resource.

## 3. Test commands

- Run automated tests with `$env:PYTHONPATH='src'; python -m unittest discover -s tests -v`.
- Run built GUI/ZIP/metadata smoke tests with `.\tests\run_ui_smoke.ps1`; use `-SkipLaunch` only without an interactive desktop.
- Run `python -m compileall -q src scripts tests` before completion.
- No lint/format command was found in the current repository; add and document one before claiming a lint/format gate.

## 4. Build commands

- Build with `powershell -ExecutionPolicy Bypass -File scripts/build.ps1`.
- The script must test and compile first, then generate the Windows x64 single-file EXE, portable ZIP, and `SHA256SUMS.txt`.
- Do not add an MSI unless an installer project and its compatibility/license/rollback audit are added first.

## 5. Code style
- Keep the opening centered language badge row byte-for-byte identical across `README.md`, `README.zh-CN.md`, and `README.ja.md`; preserve the Shields URLs and native labels `English`, `简体中文`, and `日本語`.
- Keep the three README documents in the same section order with matching commands, paths, versions, links, images, numeric facts, and code fences; translate prose and headings naturally.
- Use UTF-8, four-space indentation, type hints, and small functions.
- Keep cryptography, ACL, path safety, and container parsing out of UI callbacks.
- Keep all bilingual UI text synchronized in the `TEXT` mapping in `src/folder_locker/app.py`.
- New dependencies require compatibility, license, size, maintenance, offline-network, packaging, and rollback review.

## 6. Module boundaries

- Core must preserve authenticated AES-256-GCM container behavior, PBKDF2 key derivation, safe restore paths, symlink rejection, and failure cleanup.
- App may validate inputs and invoke Core on background threads; it must not implement encryption, container framing, ACL commands, or irreversible deletion.
- `src/utility_suite/settings.py` may store language preference only, never passwords, folder lists, keys, tokens, or recovery metadata.
- Quick-lock operations must remain Windows/NTFS-specific and must restore permissions/names or roll back on failure.

## 7. Prohibited changes

- Never commit secrets, local paths, containers, recovered folders, ACL metadata, build caches, or release files.
- Never describe NTFS quick lock as encryption or a protection against administrators/owners.
- Never delete or overwrite the source folder after encryption; the user verifies restoration and decides what to remove.
- Never allow drive roots, symbolic links, path traversal, unauthenticated restoration output, or partial recovery directories.
- Never fake a digital signature; product/version metadata is permitted but must be described accurately.

## 8. Completion criteria

- Container creation and restoration pass regression tests, including wrong-password, corrupted-container, legacy-read, symlink, traversal, and failure-cleanup cases.
- ACL lock/unlock is reversible and rollback behavior is tested on Windows.
- Unit tests, `compileall`, applicable UI smoke, archive inspection, executable metadata, and checksums pass.
- README and release notes retain the source-retention, forgotten-password, quick-lock limitation, unsigned-binary, and SHA256 warnings.

## 9. Review criteria
- Confirm the three opening language badge rows are identical and render the labels inside SVG images rather than browser-translatable text.
- Compare all three README versions for matching facts, section order, commands, paths, links, images, numbers, and code fences.
- Review AES-GCM nonce/AAD use, PBKDF2 parameters, container version parsing, authentication-before-commit, output containment, symlink handling, and temporary-file cleanup.
- Review ACL drive-root rejection, metadata recovery, Windows-only behavior, name restoration, and rollback.
- Any `core.py` change requires regression coverage; GUI appearance alone is not evidence of correctness.
- Packaging review must verify author/version resources, portable contents, third-party notices, unsigned status, and SHA256 coverage.

## 10. Common risks

- Lost passwords make encrypted containers unrecoverable.
- ACL quick lock is access control and obfuscation, not cryptographic confidentiality.
- Deleting quick-lock metadata complicates recovery.
- Unsafe restore paths or symlinks can write outside the selected directory if validation regresses.
- Unsigned PyInstaller one-file executables may trigger SmartScreen or antivirus warnings.
