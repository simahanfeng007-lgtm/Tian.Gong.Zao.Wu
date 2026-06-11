天工造物v2·0-临渊者
====================

当前最高基线：FE01 STEP68 / L6.73.8
本轮主题：Q12 交付卫生与第 11 轮新增问题闭环复检。

核心口径：
- LLM 是主脑，临渊者是 LLM 的生命体机甲执行外骨骼。
- Runtime 是神经系统，工具是身体，Skill 是经验性神经回路。
- 启动器只负责定位、校验、启动；不负责 Runtime 决策、PromptCore 编码、Planner 决策或工具执行。

L6.73.8 / Q12 入口与交付口径：
- 当前交付身份统一为 FE01 STEP68 / L6.73.8。
- 00_ASCII_START_HERE、01_启动入口、根目录兼容 BAT/SH/COMMAND 由 scripts/launcher_manifest_l67220.json + scripts/launcher_templates/* 当前契约生成。
- scripts/generate_launchers_l67219.py 与 scripts/verify_launchers_l67219.py 仅作为历史兼容 shim，实际委托 L6.73.8 / l67220 当前契约。
- Windows BAT 统一 ASCII + CRLF，禁止 CRCRLF，路径中的 cd /d %~dp0 必须加引号。
- Linux / macOS 入口统一 LF、Bash 检测、PYTHON_BIN 兼容 python3.x 与绝对路径 Python。
- smoke / validator / preflight 默认不污染源码树；运行态 .linyuanzhe、reports、__pycache__、*.pyc 不进入交付 ZIP。

推荐入口：
1. Windows：01_启动入口/Windows/01_启动临渊者桌面端_自动模式_L6710.bat
2. Windows 自检：01_启动入口/Windows/04_一键自检_L6710.bat
3. macOS：01_启动入口/macOS/01_启动临渊者桌面端_自动模式_L6710.command
4. Linux：bash "01_启动入口/Linux/01_start_desktop_auto_l6710.sh"
5. 依赖检测：00_ASCII_START_HERE/windows/DEPENDENCY_CHECK.bat 或 bash "00_ASCII_START_HERE/linux_macos/dependency_check.sh"

开发维护规则：
- 修改入口脚本时，不要直接手改 BAT/SH/COMMAND。
- 先改 scripts/launcher_manifest_l67220.json 或 scripts/launcher_templates/*。
- 然后运行：python -S scripts/generate_launchers_l67220.py
- 打包前运行：python -S scripts/verify_launchers_l67220.py

DataUp 边界继承 L6.72.17/L6.72.18：
- 无签名、签名错误、公钥缺失或 sha256 错误的 DataUp 包禁止 apply。
- 不覆盖模型服务配置、API Key、记忆、日志、审计私密数据、credentials 或用户工作区。
- 外围 I/O 仍走 BridgeEnvelope / NetworkPolicy / AssetRegistry 边界，远程 HTTP 默认阻断，loopback/local 显式允许。
