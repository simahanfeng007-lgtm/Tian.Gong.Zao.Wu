# FE01 STEP31I / L6.70.9 三端通用深度优化报告

## 目标

同类问题不再逐点修补，改为根除：

1. Windows / macOS / Linux 三端统一从 Python 启动器进入。
2. `.bat` 仅作为 Windows 薄封装；`.sh` / `.command` 仅作为 POSIX 薄封装。
3. 桌面端状态回执、文件授权、连接器注册、自检等非模型内容统一走幂等追加，避免重复点击、F5 刷新、断流重连导致聊天区污染。
4. 配置路径按平台落点，不再只按 Windows/Linux 双分支处理。

## 核心改动

- 新增 `desktop/platform_runtime_l6709.py`：集中三端平台差异。
- 重写 `desktop/start_linyuanzhe_desktop_l671.py`：变为三端通用主启动器。
- 新增 `START_DESKTOP_L6709.py` / `SELF_CHECK_L6709.py`：跨平台 Python 入口。
- 新增 Windows 入口：`启动临渊者桌面端_L6709.bat`、`START_DESKTOP_L6709.bat` 等。
- 新增 macOS 入口：`启动临渊者桌面端_L6709.command` 等。
- 新增 Linux/macOS 终端入口：`start_desktop_l6709.sh` 等。
- 本地桥 provider 配置路径调整为：
  - Windows：`%APPDATA%/LinyuanzheDesktop/provider_config.json`
  - macOS：`~/Library/Application Support/LinyuanzheDesktop/provider_config.json`
  - Linux：`${XDG_CONFIG_HOME:-~/.config}/linyuanzhe_desktop/provider_config.json`
- RuntimeSnapshot 新增 `append_assistant_notice_once()`，把文件、连接器、安装自检、控制回执等 UI 通知收敛为统一幂等消息。
- 客户端侧裸 `chat_messages.append()` 已压缩，只保留真实用户消息与 RuntimeSnapshot 内部核心追加口。

## 验证

- `compileall`：通过。
- `cross_platform_desktop_audit_l6709.py`：通过。
- `desktop_bundle_preflight_l671.py`：通过。
- `verify_l671_release.py`：通过。
- `verify_l6708_release.py`：通过。
- `desktop_windows_line_ending_audit_l6707.py`：通过，Windows 脚本 CRLF。

## 使用入口

Windows：

- `启动临渊者桌面端_L6709.bat`
- `一键自检_L6709.bat`

macOS：

- `启动临渊者桌面端_L6709.command`
- `一键自检_L6709.command`

Linux / macOS 终端：

- `./start_desktop_l6709.sh`
- `./self_check_l6709.sh`

## 边界

`ready_for_combine=false` 保持不变。原因仍是本地桌面桥接不冒充正式 TiangongWangguan / Runtime RC 解阻证据；这不是三端桌面包失败。
