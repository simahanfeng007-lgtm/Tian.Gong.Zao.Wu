# R13B Code-X Runtime 可用注册报告

## 判定

R13B 通过。Code-X 已进入 v2 Runtime 可调用状态。

## 可用性证据

- `RuntimeEntry().registry.names()` 可见 Code-X 工具。
- `RuntimeEntry.execute_plan(...)` 可执行 repo_map、workspace_patch_applier、python_quality_runner、failure_attribution_analyzer、code_x_package_workflow。
- `RuntimeEntry.run_text("code-x smoke .")` 可由 PlanBridge 触发 Code-X smoke。
- 前端 contract server 能输出 Code-X SSE tool_result 投影，客户端可解析。

## 工具注册口径

- `code_x_native/*`：纯净 v2 原生工具实现。
- `code_x_runtime_adapters.py`：Runtime 适配层。
- `risk_classifier.py`：Code-X 风险分级。
- `plan_bridge.py`：文本触发入口。
- `execution_policy.py`：A0-A4 自动放行，A5 阻断。

## no-pollution 结论

PASS。未发现 v1 import、v1 registry、v1 executor、v1 terminal、v1 provider、自迭代器复用或后台 loop。
