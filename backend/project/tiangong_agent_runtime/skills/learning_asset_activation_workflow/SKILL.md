# R20 Learning Asset Activation Workflow

## 用途

把自主学习 / 经验总结成功后的 Tool/Skill 候选，从 R16 统一契约、R17 沙箱对齐、R18 候选包、R19 发布门，推进到 R20 active asset registry，并注册为可调用的 `learned_*` Runtime 工具。

R20 的目标不是只生成注册申请，而是：**学习成功 → 门禁通过 → 受控注册 → 立即可调用 → smoke 证明 → 可回滚**。

## 标准链路

1. `synthesize_experience_candidates`
2. `queue_skill_candidates`
3. `queue_tool_production_requests`
4. `learning_asset_contract_normalize`
5. `learning_asset_contract_validate`
6. `learning_asset_sandbox_align`
7. `learning_asset_sandbox_validate`
8. `learning_asset_candidate_sandbox_build`
9. `learning_asset_candidate_sandbox_validate`
10. `learning_asset_candidate_sandbox_review`
11. `learning_asset_release_gate_check`
12. `learning_asset_activation_apply`
13. `learning_asset_activation_smoke`
14. `runtime_tool_alignment_check`

## LLM 使用规则

- 学习成功后不要停在“注册申请”。通过 R19 后直接调用 `learning_asset_activation_apply`。
- 激活成功后必须立即调用 `learning_asset_activation_smoke`。
- `learned_tool_*` 会执行已通过门禁的候选 adapter：`candidate_adapter_draft(arguments)`。
- `learned_skill_*` 会返回已激活 Skill 卡、使用链、触发规则和下一步提示。
- 需要直接使用已激活资产时，调用：

```text
runtime-tools tool <learned_tool_name> {"query":"当前任务摘要"}
```

## 边界

- 只注册 `learned_tool_*` / `learned_skill_*`。
- 不覆盖内置 Runtime 工具。
- 不复制 / import v1。
- 不复用 v1 registry / executor / provider / self-iteration。
- 不 monkey patch。
- 不启动后台 loop。
- A5 仍硬拦，A0-A4 按 Runtime 审计链放行。
