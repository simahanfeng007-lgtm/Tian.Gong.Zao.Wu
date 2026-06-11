# L6.70.2-R17 ToolSkill 统一资产契约与既有沙箱对齐报告

## 结论

R16 的结论需要修正：沙箱并非未做。当前包内已经存在 L6.22 Tool 生产请求沙箱化与验证前置链：

- `ToolProductionRequestBridge`
- `SandboxValidationPlan`
- `ToolProductionQueueItem`
- `queue_tool_production_requests`
- sandbox_profile: `isolated_workspace_candidate_only`

R17 不新建真实执行沙箱，而是把 R16 统一资产契约硬接到上述既有 L6.22 沙箱前置链。

## 新增 Runtime 工具

- `learning_asset_sandbox_guide`
- `learning_asset_sandbox_align`
- `learning_asset_sandbox_validate`

## 新增 Skill

- `skill.learning_asset_sandbox_alignment_workflow`

## 新增命令

```bash
asset-sandbox guide
asset-sandbox align
asset-sandbox validate
asset-sandbox drill pytest missing tests
```

## 对齐后的标准链

```text
synthesize_experience_candidates
→ queue_skill_candidates
→ queue_tool_production_requests
→ learning_asset_contract_normalize
→ learning_asset_contract_validate
→ learning_asset_sandbox_align
→ learning_asset_sandbox_validate
→ quality_gate / release_gate / runtime registration review
```

## 边界

- 当前仍是候选 / 元数据 / preflight 阶段。
- 不生产 Tool。
- 不注册 Tool。
- 不释放工具句柄。
- 不调用候选工具。
- 不启动后台 loop。
- 不复制或 import v1。

## 验证

- backend compileall: PASS
- pytest: 14 passed
- R17 sandbox alignment smoke: PASS
- Runtime alignment smoke: PASS
- R16 contract smoke: PASS
- Code-X smoke: PASS
- v1 clean import smoke: PASS
- no-pollution scan: PASS
