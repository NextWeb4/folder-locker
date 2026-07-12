# Initial Clean Release v1.0.0

## 中文

这是 Folder Locker 的首次独立发布。它从原离线工具套件中拆分出来，保留完整的强加密容器模式和 Windows 快速权限锁模式。

### 下载说明

- `folder-locker-v1.0.0-windows-x64.exe`：Windows x64 单文件 Folder Locker。
- `folder-locker-v1.0.0-windows-x64.zip`：便携 ZIP，包含 EXE、README、LICENSE 和第三方声明。
- `SHA256SUMS.txt`：发布资产的 SHA256 校验值。

强加密容器模式使用 PBKDF2-HMAC-SHA256 与 AES-256-GCM。Windows 快速权限锁模式只修改 NTFS 权限并混淆名称，不是加密。EXE 未进行数字签名；作者、版权、产品名和版本元数据已写入。请校验 SHA256 后使用。

作者：HaoXiang Huang
邮箱：didadida1688@gmail.com
主页：https://nextweb4.github.io/
GitHub：https://github.com/NextWeb4

## English

This is the first standalone release of Folder Locker. It is split out from the original offline utility suite and keeps both the strong encrypted container mode and the Windows quick permission lock mode.

### Downloads

- `folder-locker-v1.0.0-windows-x64.exe`: Windows x64 single-file Folder Locker.
- `folder-locker-v1.0.0-windows-x64.zip`: Portable ZIP with the EXE, README, LICENSE, and third-party notices.
- `SHA256SUMS.txt`: SHA256 checksums for release assets.

The strong encrypted container mode uses PBKDF2-HMAC-SHA256 and AES-256-GCM. The Windows quick permission lock mode only changes NTFS permissions and obfuscates names; it is not encryption. The EXE is not digitally signed; author, copyright, product, and version metadata are present. Verify SHA256 before use.

Author: HaoXiang Huang
Email: didadida1688@gmail.com
Homepage: https://nextweb4.github.io/
GitHub: https://github.com/NextWeb4
