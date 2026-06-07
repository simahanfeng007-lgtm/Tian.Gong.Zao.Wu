# CHANGELOG L6.62

## 新增

1. `contracts/observability.py`：Trace / Observability 只读合约。
2. `RuntimeSnapshot.trace_records / trace_stats`：桌面端可渲染的运行观测投影。
3. `SseRuntimeClient`：Runtime SSE 事件进入 Agent UI 后同步生成 TraceRecord。
4. 桌面端新增「观测」二级页。
5. 新增 `run_observability_smoke.py`、`observability_preflight_l662.py`、`verify_l662_release.py`。
6. 新增 L6.62 启动脚本和文档。

## 未改变

- 后端核心主链未改。
- Runtime 仍是唯一执行调度中枢。
- TiangongWangguan 仍是统一网关入口。
- 前端仍只负责渲染、提交请求和展示回执。
- 真实 Runtime 解阻仍以 L6.61 脚本结果为准。
