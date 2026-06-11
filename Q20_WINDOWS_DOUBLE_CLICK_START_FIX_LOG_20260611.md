# Q20 Windows 双击一键启动修复日志（2026-06-11）

## 背景

用户反馈：Windows 系统点击一键启动后直接崩溃 / 秒退。

本轮不再只做 Linux/headless 入口回归，而是把 Windows 用户双击路径作为主问题处理：BAT 层、Python 入口层、本地桥接层、前端启动层均纳入修复。

## 根因归纳

1. Windows 用户入口 BAT 过重：
   - 旧 BAT 同时承担 root 搜索、Python/Tk 探测、入口执行和错误处理。
   - 在真实 Windows 双击场景下，路径含中文/空格、Python launcher 异常、Tk 缺失、子进程异常时容易表现为窗口秒退或不可读错误。

2. Python 子进程隔离不完整：
   - BAT 调用第一层 Python 时使用 `-S -B`。
   - 但桌面入口内部再拉起本地 bridge / frontend 时没有继续使用 `-S -B`。
   - 宿主 `sitecustomize` / 用户站点包可能在启动阶段输出异常甚至拖慢启动。

3. Bridge 报告目录仍可能默认写包根：
   - 本地 bridge 的 `REPORTS` 默认仍是 `ROOT / "reports"`。
   - 如果包所在目录权限受限或用户不希望交付树被写入，会增加启动失败和污染风险。

4. 失败路径缺少 Windows 双击友好日志：
   - 用户双击时一旦发生异常，难以看到完整原因。
   - 需要稳定写入用户目录日志，并在 BAT 层对非零退出码保持窗口可见。

## 修复内容

### 1. 新增 Windows 安全启动器

新增：

```text
00_ASCII_START_HERE/python/WIN_SAFE_LAUNCHER_L6738.py
```

职责：

- 由 Python 接管 root 发现、日志、入口调用和异常拦截。
- 所有子入口使用 `sys.executable -S -B -u` 启动。
- 失败日志写入用户目录：
  - Windows: `%APPDATA%/LinyuanzheDesktop/logs/last_windows_launch.log`
  - POSIX verifier: `<user-state>/linyuanzhe_desktop/logs/last_windows_launch.log`
- 默认将 `LINYUANZHE_REPORT_DIR` 指向用户诊断目录，不写包根。
- 对桌面进程“过快 0 退出”做保护，避免用户看到窗口秒退却没有错误。

### 2. 重写 Windows BAT 模板

修改：

```text
scripts/launcher_templates/windows_entry.template.bat
```

并重新生成 17 个 manifest Windows 用户入口 BAT。

新 BAT 仅负责：

- 设置 UTF-8 / Python 环境变量。
- 定位 `WIN_SAFE_LAUNCHER_L6738.py`。
- 查找 Python 3.10-3.14。
- 调用安全启动器。
- 非零退出码时 `pause` 保持窗口可见。

移除旧 BAT 中的重型 `for /f "usebackq"` Python 探测链和 `PYTHON_EXE` 传递链。

### 3. 桌面入口子进程隔离

修改：

```text
desktop/start_linyuanzhe_desktop_l671.py
```

- Bridge 子进程改为：

```text
sys.executable -S -B -u desktop/linyuanzhe_local_runtime_bridge_l671.py ...
```

- Frontend 子进程改为：

```text
sys.executable -S -B -u -m linyuanzhe_frontend.app ...
```

- 本地桥接启动状态输出增加 `flush=True`，避免双击 / 管道场景看不到进度。

### 4. Bridge 报告目录默认移出包根

修改：

```text
desktop/linyuanzhe_local_runtime_bridge_l671.py
```

- 新增 `_default_reports_dir()`。
- 默认报告目录改到用户目录 / 临时目录。
- 只有显式设置 `LINYUANZHE_ALLOW_PACKAGE_REPORTS=1` 才允许写包根 `reports`。

### 5. 新增 Q20 verifier

新增：

```text
scripts/verify_l6738_q20_windows_double_click_launcher.py
```

覆盖：

- 17 个 manifest Windows BAT 均为 CRLF + ASCII。
- BAT 均包含 Q20 safe launcher marker。
- BAT 不再包含旧 `for /f "usebackq"` 探测链。
- BAT 不再包含旧 `PYTHON_EXE` 调用链。
- Safe launcher 存在且子进程使用 `-S -B -u`。
- 桌面 bridge/frontend 子进程使用 `-S -B -u`。
- Bridge 报告目录默认不写包根。
- Safe launcher 自检路径可运行。
- Bridge-only 启动能输出本地桥接 URL。
- 输出不含 `artifact_tool` 噪声。
- 不生成 `.linyuanzhe`、`reports`、`__pycache__`、`*.pyc` 包根污染。

## 回归摘要

已在 clean 工作树执行：

```text
python -S -B scripts/generate_launchers_l67220.py --check
python -S -B backend/project/run_bat_line_ending_smoke_l67219.py
python -S -B scripts/verify_l6738_q20_windows_double_click_launcher.py
python -S -B scripts/verify_l6738_q19_history_entry_permissions.py
python -S -B scripts/verify_l6738_q18_write_fix_pack_loop.py
python -S -B scripts/verify_l6738_mock_llm_long_chain_cli.py
python -S -B backend/project/run_agent.py --mock --status
```

结果：

- Q20 Windows double-click safe launcher verifier：PASS
- Q19 history/permission verifier：PASS
- Q18 write/fix/package loop verifier：PASS
- Mock LLM long-chain verifier：PASS
- BAT line ending smoke：PASS，65 个 BAT
- `run_agent.py --mock --status`：PASS，不污染包根
- 额外测试：复制到“空格 + 中文路径”后，safe launcher 自检 PASS

## 用户侧建议

Windows 用户优先点击：

```text
01_启动入口/Windows/01_启动临渊者桌面端_自动模式_L6710.bat
```

如果仍失败，窗口现在不会直接秒退，会显示错误码，并在日志里写明原因。
