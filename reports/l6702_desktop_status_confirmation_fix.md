# L6.70.2 桌面端状态/确认修复报告

## 修复目标

1. 修复真实本地桥接模式下任务塔台泄露 Mock Session，导致显示 `disconnected / 待同步 / 0%`、统计数量异常的问题。
2. 修复流式任务已完成后任务快照仍显示 `Runtime 正在流式输出 / 待确认 / 100%` 的状态滞留问题。
3. 修复确认按钮提交后 UI 快照未接收 Runtime 回执，导致“任务快照无法确认 / 确认后页面不变”的问题。

## 改动文件

- `frontend/linyuanzhe_frontend/contracts/runtime_snapshot.py`
  - Runtime SSE / JSON 等非 Mock 源不再自动注入 Mock execution、Mock session、Mock installer、Mock self-iteration 等演示数据。
  - `pending_confirmation_count` 默认值从 `1` 修正为 `0`。

- `frontend/linyuanzhe_frontend/clients/sse_runtime_client.py`
  - `/sessions/list` 返回空列表时清空旧 Session，避免 Mock Session 残留。
  - 增加 Session stats 规范化，兼容 `total_count` 与 `total` 两类键。
  - 流式任务 `run_terminal` 后将 stage 收口为 `Runtime SSE 已收口`，并刷新 Session 列表。
  - 按当前 run/task 上抛真实 Session 投影，完成态显示 `completed / 100%`。
  - 每次新任务清空上一轮待确认残留，重新从 ActionGuard / pending ticket 派生确认态。

- `frontend/linyuanzhe_frontend/ui/main_window.py`
  - 确认/拒绝请求后将 `client.submit_confirmation()` 返回值写回 `self.snapshot`。
  - 任务快照卡在存在待确认票据时直接展示“允许请求 / 拒绝”按钮；无票据时跳转执行详情。

- `desktop/linyuanzhe_local_runtime_bridge_l671.py`
  - `/sessions/list` 返回标准 Session stats 键：`total/running/waiting_confirmation/blocked/recoverable/completed/failed/queued`。
  - 完成任务不再错误标记为 recoverable。
  - `/confirmations/submit` 回执补充 `ticket_id`。

## 验证

- `python3 -m compileall -q frontend/linyuanzhe_frontend desktop backend/project`：通过。
- `python3 scripts/desktop_bundle_preflight_l671.py`：通过。
- `python3 scripts/verify_l671_release.py`：通过。
- 本地桥接 smoke：初始 Session=0、待确认=0；发送“你好”后：`COMPLETED / completed / Runtime SSE 已收口 / 100%`，Session 列表为真实 completed 任务，无 `SESS-MOCK-*` 残留。

## 边界

- 仍保持前端只读/请求信封边界；前端不会直接执行工具、写记忆、写审计或应用回滚。
- 本修复不触碰后端 Runtime 核心执行链，仅修复桌面桥接投影、前端状态同步与确认回执写回。
