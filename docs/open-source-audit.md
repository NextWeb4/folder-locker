# 开源方案审计

## 当前项目审计结论

- 技术栈：Python 3 / Tkinter / cryptography / Windows `icacls`。
- 架构：离线单机桌面工具，不需要服务端、浏览器或联网同步。
- 功能边界：强加密容器用于数据加密；ACL 快速锁用于本机权限限制和名称混淆。
- 打包目标：Windows 单文件 EXE 和便携 ZIP。

## 候选方案对比

| 方案名称 | 来源 | 许可证 | 核心能力 | 优点 | 缺点 | 维护状态 | 与当前项目的契合度 | 可能冲突点 | 是否采用 | 采用方式 |
|---|---|---|---|---|---|---|---|---|---|---|
| cryptography | PyPI / GitHub | Apache-2.0 or BSD | AES-GCM、PBKDF2 | 成熟稳定，已被原实现使用 | 增加包体积 | 活跃 | 高 | 需要明确忘记密码不可恢复 | 采用 | 用于容器加密和 ACL 元数据保护 |
| Python 标准库 Tkinter | Python 官方标准库 | PSF License | 桌面 GUI | 与原工具一致、离线、体积可控 | UI 组件基础 | 随 Python 维护 | 高 | 无 | 采用 | 直接作为 GUI |
| Windows `icacls` | Windows 系统工具 | Windows 系统组件 | 修改 NTFS ACL | 无额外依赖、与原实现一致 | 仅限 Windows/NTFS；不是加密 | 随 Windows 维护 | 高 | 必须避免宣传为强加密 | 采用 | 通过 `subprocess` 调用 |
| pywin32 | PyPI / GitHub | PSF-style | Windows ACL API | 可直接调用 Win32 安全 API | 代码复杂、打包体积和兼容面增加 | 活跃 | 中 | 替换 `icacls` 收益不明显 | 不采用 | 保留为未来高级权限编辑备选 |
| zipfile + 自研加密 | Python 标准库/自研 | PSF/MIT | 压缩和自定义加密 | 少依赖 | 自研密码学风险高 | 不适用 | 低 | 与安全目标冲突 | 不采用 | 坚持使用 cryptography |

## 最终采用范围

- 直接复用：`cryptography` 的 AESGCM/PBKDF2、Python Tkinter、Windows `icacls`、Python 标准库。
- 只借鉴设计：原离线工具套件中的模块边界和构建方式。
- 不采用：pywin32、Electron/Tauri、云同步、安装器工程、自研密码学。
- 需要适配：从套件拆出 `folder_locker` 和最小 `utility_suite` 模块，改为独立项目名、独立 README、独立 Release。
- 保留：AES-256-GCM 强加密容器、旧容器读取、ACL 快速锁、路径安全、symlink 拒绝、失败回滚。
- 替换：套件级文档、套件级构建脚本和套件产品名。
