# FE01 STEP31E / L6.70.5 启动稳定与交互回执修复报告

## 用户反馈

1. 双击/执行桌面端闪退，PowerShell 显示 `tkinter.TclError: Can't find a usable tk.tcl`。
2. 启动脚本存在 `#cd /d "%~dp0"` 这类错误注释/工作目录不稳定问题。
3. 文件授权请求显示写入，但点击后像上传文件。
4. MCP 提交注册请求后没有明显反应。
5. 记忆界面留白过多。
6. 桌面背景颜色不应只有黑色，需要两三个可选配色。

## 根因归类

- 闪退：本机默认 `python` 指向缺少 Tcl/Tk 的 Python 解释器，截图中是 Python315；Tk 前端无法初始化。
- 启动脚本：工作目录依赖不稳，且未主动筛选可用 Python/Tk 环境。
- 写入授权：旧交互使用保存文件对话框，用户感知类似上传/选文件。
- MCP：请求进入桥接后缺少强反馈提示。
- 记忆页：信息密度低，部分大屏下空白明显。
- 主题：配色选项藏在设置页，不够直接。

## 修复

1. 新增启动前 Tk 预检：
   - Python < 3.10 直接拒绝。
   - 尝试修复 `TCL_LIBRARY/TK_LIBRARY` 环境指向。
   - Tk 不可用时不再先启动桥接后崩溃，改为输出明确错误，并写入 `reports/desktop_startup_failure_l6705.txt`。

2. 新增/替换根目录启动器：
   - `启动临渊者桌面端_L6705.bat`
   - `启动临渊者桌面端_真实模型_L6705.bat`
   - `START_DESKTOP_L6705.bat`
   - `START_DESKTOP_PROVIDER_L6705.bat`
   - 自动尝试 `py -3.12`、`py -3.11`、`py -3.10`、`python`、`python3`，只选择 Python 3.10+ 且 Tk 可用的解释器。
   - 明确 `cd /d "%~dp0"`，消除启动目录漂移。

3. 文件授权写入交互：
   - 写入授权改为“选择输出目录并申请写入”。
   - 使用目录选择器，不再像上传文件。
   - scope 固定为 `workspace_outbox`，purpose 为 `workspace_output_write_directory`。

4. MCP 注册交互：
   - 提交后状态栏显示“已生成注册回执”。
   - 弹出明确确认：默认禁用、只读待审、前端未安装/执行 MCP。
   - 本地桥接 POST `/connectors/register/request` 与 GET `/connectors/registry` 回归通过。

5. 记忆页：
   - 改为紧凑记忆驾驶舱。
   - 新增摘要带、五层记忆表、召回/遗忘/升级信号、最近脱敏对话/候选区。
   - 去除大面积空卡感。

6. 桌面配色：
   - 设置页保留下拉选择。
   - 侧边栏新增快捷按钮：极夜、暖灰、墨绿。
   - 只影响前端显示，不影响 Runtime、工具、记忆、审计。

## 验证

- `python -m compileall -q backend/project frontend scripts launchers installer desktop`：通过。
- `scripts/desktop_bundle_preflight_l671.py`：通过。
- `scripts/verify_l671_release.py`：通过。
- `reports/l6705_bridge_interaction_probe.json`：通过。

## 边界

本修复仍是桌面端前端 + 本地桥接层修复。前端继续只提交 request envelope，不直接执行工具、不写长期记忆、不写审计、不应用回滚、不安装 MCP。
