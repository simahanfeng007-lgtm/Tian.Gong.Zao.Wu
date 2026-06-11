# CHANGELOG L6.70.2-CodeX Runtime 可用注册版

## 本轮目标

把 R3-R13A 的 Code-X 候选能力从旁路规格推进为 v2 Runtime 可调用工具链，解决“未注册就不可用”的核心问题。

## 主要变更

1. 新增 `tiangong_agent_runtime/code_x_native/`：v2 原生 Code-X 工具实现。
2. 新增 `tiangong_agent_runtime/code_x_runtime_adapters.py`：将 Code-X 工具接入 `RuntimeToolRegistry`。
3. 修改 `runtime_entry.py`：`build_default_registry()` 显式调用 `register_code_x_runtime_tools(registry)`。
4. 修改 `risk_classifier.py`：加入 Code-X 工具风险分级，危险命令仍 A5 硬阻断。
5. 修改 `execution_policy.py`：默认策略对齐 A0-A4 自动放行并审计，A5 阻断。
6. 修改 `plan_bridge.py`：新增 `code-x ...` DSL 触发入口。
7. 新增后端 smoke：`backend/project/run_codex_runtime_smoke.py`。
8. 新增 Runtime pytest：`backend/project/tests/test_codex_runtime_registration.py`。
9. 新增前端桥接 smoke：`frontend/linyuanzhe_frontend/run_codex_bridge_smoke.py`。
10. 修改前端 contract server：支持 Code-X SSE 可见投影。
11. 新增跨平台 launcher。

## 验证结果

- backend compileall：PASS
- frontend compileall：PASS
- Code-X Runtime pytest：3 passed
- Code-X Runtime smoke：PASS
- Code-X frontend bridge smoke：PASS
- no-pollution scan：PASS

## 剩余限制

- 当前是 Runtime 注册可用版，不等于已经接入真实模型自动选择全部 Code-X 工具的最终体验。
- 新前端完成后仍建议做 UI 层真实交互 smoke，包括任务快照、状态栏、next_action_hint 展示、patch/test/repair/rollback/handoff 可视化。
- 子代理仍是 evidence-only，符合主脑不夺权原则。
