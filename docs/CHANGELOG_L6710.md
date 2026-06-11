# CHANGELOG L6710 / FE01 STEP31J

## 目标

将 L6709 三端通用桌面入口从“根目录脚本堆叠”调整为“按平台归类的人类可用入口”。

## 变更

- 新增 `01_启动入口/Windows`：Windows 用户启动、自检、真实模型、Mock 演示入口。
- 新增 `01_启动入口/macOS`：macOS `.command` 启动、自检、真实模型、Mock 演示入口。
- 新增 `01_启动入口/Linux`：Linux `.sh` 启动、自检、真实模型、Mock 演示入口。
- 新增 `01_启动入口/通用Python`：三端共用 Python 主入口。
- 根目录清理：不再保留 `.bat/.sh/.command/.py` 启动脚本。
- 旧版 L6705-L6709 根目录入口移动到 `90_历史入口归档/旧版根目录入口_L6705-L6709`。
- Windows `.bat/.cmd/.ps1` 统一保持 CRLF。
- macOS/Linux `.command/.sh` 保持 LF 并设置可执行位。
- 程序主体 `backend/desktop/frontend/installer` 保持原相对位置，避免破坏导入路径。

## 推荐入口

- Windows：`01_启动入口/Windows/01_启动临渊者桌面端_自动模式_L6710.bat`
- macOS：`01_启动入口/macOS/01_启动临渊者桌面端_自动模式_L6710.command`
- Linux：`01_启动入口/Linux/01_start_desktop_auto_l6710.sh`

## 验证

- `scripts/desktop_entry_layout_audit_l6710.py` 通过。
- `scripts/cross_platform_desktop_audit_l6710.py` 通过。
- `scripts/desktop_windows_line_ending_audit_l6707.py` 通过。
- `scripts/desktop_bundle_preflight_l671.py` 通过。
- `scripts/verify_l671_release.py` 通过。
