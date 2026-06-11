# R17 Learning Asset Sandbox Alignment Workflow

## 定位

本 Skill 用于把 R16 统一 Tool/Skill 资产契约对齐到已经存在的 L6.22 Tool 生产请求沙箱化与验证前置链。它不创建新沙箱，不生产 Tool，不注册 Tool，不释放工具句柄，不调用候选工具。

## 既有沙箱

- `ToolProductionRequestBridge`
- `SandboxValidationPlan`
- `ToolProductionQueueItem`
- sandbox_profile: `isolated_workspace_candidate_only`
- 工具入口：`queue_tool_production_requests`

## 标准链路

1. `synthesize_experience_candidates`
2. `queue_skill_candidates`
3. `queue_tool_production_requests`
4. `learning_asset_contract_normalize`
5. `learning_asset_contract_validate`
6. `learning_asset_sandbox_align`
7. `learning_asset_sandbox_validate`
8. 通过后才进入质量门、发布门、Runtime 注册审阅或 handoff。

## 命令入口

```bash
asset-sandbox guide
asset-sandbox align
asset-sandbox validate
asset-sandbox drill pytest missing tests
```

## LLM 使用规则

- LLM 是主脑和最终裁决者。
- Planner 只建议，不得夺权。
- 沙箱对齐工具只返回 mapping / issues / next_action_hint。
- Tool 资产没有通过 `learning_asset_sandbox_validate` 前，不得进入 Tool 生产、注册或激活。
- A5 边界：凭证、私钥、裸 shell/network、破坏性写入、monkey patch、后台 loop、v1 registry/executor/provider/self-iteration 复用。
