# CHANGELOG L6.67

## Added

- 多任务 Session 管理器契约与只读投影。
- 「任务」二级页。
- Session 搜索与恢复请求入口。
- 顶栏「任务塔台」入口。
- 首页输入栏「任务」入口。
- `run_session_manager_smoke.py`。
- `scripts/session_manager_preflight_l667.py`。
- `scripts/verify_l667_release.py`。
- `launchers/run_session_manager_preflight_l667.*`。
- `launchers/verify_l667_release.*`。
- 统一启动器新增 `--session-manager-preflight` 与 `--verify-l667`。

## Fixed

- 修复 SSE 文件授权 HookBus 参数错位，避免真实 SSE 客户端在文件授权请求时发生 TypeError。

## Boundaries

- 前端不恢复工具。
- 前端不切换 Runtime 执行上下文。
- 前端不写记忆、审计、回滚。
- 前端恢复/搜索仅提交 Runtime envelope。
- 真实 Runtime smoke 未执行时，`ready_for_combine` 保持 `false`。
