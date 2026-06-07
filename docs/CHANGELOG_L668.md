# CHANGELOG L6.68

- 新增安装器 RC 前置结构：`installer/`。
- 新增安装 manifest、版本槽、启动自检、崩溃报告模板、更新器骨架、离线修复和回滚计划脚本。
- 新增前端 `installer_rc` 合约和 RuntimeSnapshot 只读投影。
- 新增桌面端「安装」二级页。
- 新增 `run_installer_rc_smoke.py`、`installer_rc_preflight_l668.py`、`verify_l668_release.py`。
- 统一启动器新增 `--installer-rc-preflight` 与 `--verify-l668`。
- 修补上一包中任务页与记忆页 UI 方法缺失/错位问题。
- 补齐 SSE RuntimeClient 的 Session 投影读取 helper，避免真实刷新时降级为错误提示。

不变边界：

- Runtime 仍是唯一执行调度中枢。
- TiangongWangguan 仍是统一网关入口。
- 前端不裸调 Provider、工具、记忆、审计、回滚。
- 安装器结构仍不是最终 exe/msi 安装包。
