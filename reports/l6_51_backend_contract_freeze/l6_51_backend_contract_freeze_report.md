# L6.51 后端接口契约冻结报告

## 本轮结论

- 是否完成：是。
- 是否动到核心主链：未改 ExecutionSpine / Runtime 执行语义 / tiangong_kernel。
- 是否补前端契约：是。
- 是否覆盖 L6.50 在线 smoke 结果：是，按用户回传结果固化到报告与 Runbook。
- 契约自检：`True`。

## 本轮新增/修改

1. 新增 `tiangong_agent_runtime/frontend_contract.py`，冻结 SSE / Provider 设置 / 底部状态字段 / 前端禁区。
2. 修改 `tiangong_agent_shell/config_loader.py`，保留 canonical `TIANGONG_*` 的同时补 `DEEPSEEK_*` 受控别名。
3. 新增 `tests/test_l6_51_frontend_contract_runtime_events.py`，验证事件顺序、Provider 脱敏、状态栏字段、DeepSeek env alias。
4. 新增前端契约文档与 Provider Runbook。

## L6.50 基线继承说明

用户确认 L6.50 已完成：Mock 7/7、真实在线 4/4、deepseek-v4-pro 基础对话 2.3s、Plan 生成 5.0s、deepseek-v4-flash 0.8s、凭证脱敏无泄漏、Runbook 固化、CI allowlist 5 工具。

本地工作区发现 `L6_50` zip 与 sha256 不一致且包内缺少运行主链文件，因此本轮以完整 `L6_49_5` 包为代码基底，重新补入 L6.50 必要配置别名与 L6.51 契约文件。该风险已记录，不伪造本地 L6.50 包完整性。

## 验收点

- `/chat/stream-events` 固定为 SSE 接入点。
- `assistant_final -> run_terminal` 顺序冻结。
- `api_key/base_url` 只写不读。
- 底部状态栏字段固定为 9 项。
- 前端禁止裸调 Provider、裸调工具、裸写记忆、裸写审计、直接回滚、直接合入自我迭代。
- A5 极高危仍由 QualityGate 硬拦截或人工确认。


## 验证结果补充

```json
{
  "compileall": "PASS: python3 -m compileall -q tiangong_agent_runtime tiangong_agent_shell tiangong_kernel tests",
  "l6_51_targeted": "PASS: 6 passed",
  "runtime_frontend_contract_subset": "PASS: 14 passed (L6.51 + L6.49.3 + L6.49.5)",
  "l6_49_to_l6_51_targeted": "PASS: 30 passed",
  "l0_segment": "PASS: 117 passed",
  "l1_segment": "PASS: 231 passed",
  "l2_segment": "PASS: 193 passed",
  "l3_segment": "PASS: 170 passed",
  "l4_segment": "PASS: 237 passed across 3 chunks",
  "l5_segment": "PASS: 377 passed across 4 chunks",
  "docs_filename_hotfix": "PASS after restoring readable 五模型 docs/hash aliases",
  "secret_leak_scan": "PASS: strict_finding_count=0; marker labels classified as non-secret fixtures/references",
  "bare_except_pass_scan": "PASS: finding_count=0",
  "full_pytest": "NOT COMPLETED: repository-wide pytest timed out in this environment around L6 long CLI/subprocess tests; no additional failure observed before timeout after docs filename repair"
}

```

## 剩余风险

1. 本地可用的 `L6_50` zip 与 sha256 不一致且包内缺少运行主链文件；本轮交付以完整 `L6_49_5` 包为代码基底，并补入 DeepSeek 受控 env alias 与 L6.51 契约层。用户确认的 L6.50 在线 smoke 结果已固化到文档，但本地未能复验残缺 `L6_50` 包完整性。
2. Repository-wide full pytest 在当前执行环境中于 L6 长 CLI/subprocess 测试附近超时，未取得一次完整绿色总跑结果；已完成 compileall、L6.51 定向、L6.49-L6.51 目标段、L0-L5 分段回归、secret scan 与 bare except scan。
3. 前端仍不能正式施工业务逻辑，只能按 L6.51 契约接壳；真实桌面端接入建议在 L6.52 进行。
