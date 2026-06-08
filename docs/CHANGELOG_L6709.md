# CHANGELOG L6.70.9 / FE01 STEP31I

- 将桌面一体包启动链提升为 Windows / macOS / Linux 三端通用结构。
- 新增平台适配层 `desktop/platform_runtime_l6709.py`。
- 重写桌面启动器，三端统一走 Python 主入口，`.bat` / `.sh` / `.command` 只做薄封装。
- Provider 配置路径新增 macOS 标准目录，并保留 Windows / Linux 标准目录。
- 扩大聊天回执幂等治理范围：文件、工作区授权、连接器、自检、控制请求等状态通知不再因重复点击或刷新累积污染聊天区。
- 新增 `scripts/cross_platform_desktop_audit_l6709.py`，覆盖三端入口、脚本换行、可执行位、桥接探针、裸 append 守卫。
- 保持 `ready_for_combine=false`：桌面本地桥接不冒充正式 Runtime RC 解阻证据。
