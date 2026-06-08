临渊者桌面端 FE01 STEP31Q / L6.71.7

本包已按人类使用入口重新归类。根目录不再堆放大量启动脚本。

推荐打开路径：

1. Windows
   打开：01_启动入口/Windows/01_启动临渊者桌面端_自动模式_L6710.bat

2. macOS
   打开：01_启动入口/macOS/01_启动临渊者桌面端_自动模式_L6710.command
   如系统拦截执行权限，在终端运行：chmod +x "01_启动入口/macOS/01_启动临渊者桌面端_自动模式_L6710.command"

3. Linux
   终端运行：bash "01_启动入口/Linux/01_start_desktop_auto_l6710.sh"

入口说明：
- 自动模式：有 Provider Key 时走真实模型；无 Key 时走本地演示桥。
- 真实模型：强制 provider 模式。
- 演示Mock：强制 mock 模式，只做桌面交互验证。
- 一键自检：检查 Python、Tk、项目根目录、桥接入口、配置路径。
- DataUp 一键安全更新：进入系统页点击“检查更新/一键安全更新”，或使用 05_DataUp 一键安全更新入口。

DataUp 三端入口：
- Windows：01_启动入口/Windows/05_DataUp一键安全更新_L6717.bat
- macOS：01_启动入口/macOS/05_DataUp一键安全更新_L6717.command
- Linux：01_启动入口/Linux/05_dataup_safe_update_l6717.sh
- 通用 Python：01_启动入口/通用Python/DATAUP_SAFE_UPDATE_L6717.py

DataUp 边界：
- 只启动独立安全更新器，不由前端直接覆盖文件。
- 更新前创建回滚点，更新后自检，失败自动回滚。
- 不覆盖 Provider 配置、API Key、记忆、日志、审计私密数据、credentials 或用户工作区。

旧版 L6705-L6709 根目录入口已移动到：90_历史入口归档/旧版根目录入口_L6705-L6709。
不要再用旧入口做验收。
