# 项目协作规则

## 1. 项目结构
- 当前项目是从 `offline-utility-suite` 独立出来的完整 Folder Locker：包含 AES-256-GCM 强加密容器和 Windows NTFS 快速权限锁两种模式。
- 应用源码放在 `src/folder_locker/`；共享作者/设置模块放在 `src/utility_suite/`；测试放在 `tests/`；构建脚本放在 `scripts/`；版本资源放在 `resources/`；发布产物只放在被 Git 忽略的 `release-assets/`。
- 原始 EXE 和旧套件仓库只作为行为来源，不复制进本仓库。

## 2. 运行命令
- 源码运行前设置 `$env:PYTHONPATH='src'`，再运行 `python -m folder_locker.app`。
- GUI 必须保持离线运行，不得要求浏览器、服务端、账号或网络连接。

## 3. 测试命令
- 自动测试：`$env:PYTHONPATH='src'; python -m unittest discover -s tests -v`。
- 构建后 GUI/ZIP/元数据烟雾测试：`.\tests\run_ui_smoke.ps1`；无交互桌面或 CI 可使用 `-SkipLaunch`。
- 当前未发现独立 lint / format 命令；提交前至少运行 `python -m compileall -q src scripts tests`。

## 4. 构建命令
- 构建命令：`powershell -ExecutionPolicy Bypass -File scripts/build.ps1`。
- 构建脚本必须先运行测试和 `compileall`，再生成 Windows 单文件 EXE、便携 ZIP 和 SHA256。
- 不强行生成 MSI；没有安装器工程时只发布 EXE 和 ZIP。

## 5. 代码风格
- Python 使用 UTF-8、4 空格缩进、类型提示和小函数；核心加密/ACL/路径安全逻辑不得写进 UI 回调。
- UI 文案集中在 `src/folder_locker/app.py` 的 `TEXT` 映射；新增文案必须中英文同步。
- 新增依赖必须先完成兼容性、许可证、体积、维护状态和离线边界审计。

## 6. 模块边界
- `src/folder_locker/core.py` 负责容器格式、AES-GCM 加解密、PBKDF2、路径安全、名称混淆、元数据、`icacls` 调用和失败回滚。
- `src/folder_locker/app.py` 只负责 Tkinter UI、输入校验、后台线程和用户提示。
- `src/utility_suite/settings.py` 只保存本机语言偏好，不得保存密码、令牌或被锁文件夹列表。

## 7. 禁止事项
- 不得提交 `.env`、令牌、密钥、凭据、本机路径缓存、构建目录、Release 资产或测试产生的容器/恢复目录。
- 不得把 ACL 快速锁描述为强加密；强加密只指 AES-256-GCM 加密容器模式。
- 不得采用不可逆删除/覆盖流程；加密成功后必须保留源文件夹，由用户验证恢复后自行删除。
- 不得伪造数字签名；无证书时只设置作者、版权、产品名、公司名和版本元数据。

## 8. 完成标准
- 项目包含可维护源码、双语 UI、双语 README、MIT License、作者信息、依赖审计、构建脚本、测试和 Release Notes。
- 强加密模式必须能创建 `.locked` 容器并恢复文件夹；ACL 模式必须能失败回滚并正确恢复名称。
- Release 资产必须包含 EXE、ZIP 和 `SHA256SUMS.txt`。

## 9. Review 标准
- Review 必须核对：AES-GCM nonce/AAD、PBKDF2 参数、容器路径穿越防护、SRT/旧功能无关代码是否混入、ACL Windows-only 边界、drive root 禁止、symlink 拒绝、元数据版本、失败回滚和作者元数据。
- 修改 `core.py` 必须增加或更新回归测试；仅凭 GUI 外观不得判定功能正确。

## 10. 常见风险
- 忘记密码无法恢复强加密容器；文档必须明确。
- ACL 快速锁只是权限控制和名称混淆，不等于加密，可能被管理员或所有者绕过。
- PyInstaller 未签名单文件包可能被安全软件误报；发布说明必须明确未签名和 SHA256 校验方式。
- 解锁依赖元数据文件，删除元数据会增加恢复难度。
