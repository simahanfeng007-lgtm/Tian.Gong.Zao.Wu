# L6.70.2 R18 Tool/Skill 候选包生产沙箱报告

## 结论

R18 已在 R16 统一资产契约与 R17 沙箱前置对齐之后，补上真实候选包生产沙箱。

本阶段允许：

- 在受治理 workspace 的 `.linyuanzhe/candidate_sandbox/r18` 下真实落盘候选包。
- 为 Tool 候选生成 `tool_adapter_draft.py`、manifest、静态扫描、smoke、回滚证据、注册审阅文件。
- 为 Skill 候选生成隔离 `SKILL.md` 草案、manifest、静态扫描、smoke、回滚证据、注册审阅文件。
- 生成 `candidate_package.zip` 供 LLM 和后续质量门审查。

本阶段禁止：

- 写正式 Skill 注册表。
- 注册 Runtime Tool。
- 激活 Skill。
- 释放工具句柄。
- 调用候选工具。
- 导入或复制 v1 源码。
- 调用模型、网络、shell。
- 启动后台 loop。

## 新增 Runtime 工具

- `learning_asset_candidate_sandbox_guide`
- `learning_asset_candidate_sandbox_build`
- `learning_asset_candidate_sandbox_validate`
- `learning_asset_candidate_sandbox_review`

## 新增 CLI / PlanBridge 入口

- `asset-candidate-sandbox guide`
- `asset-candidate-sandbox build <notes>`
- `asset-candidate-sandbox validate`
- `asset-candidate-sandbox review`
- `asset-candidate-sandbox drill <notes>`
- `候选包沙箱 drill <notes>`

## 标准链路

```text
synthesize_experience_candidates
→ queue_skill_candidates
→ queue_tool_production_requests
→ learning_asset_contract_normalize
→ learning_asset_contract_validate
→ learning_asset_sandbox_align
→ learning_asset_sandbox_validate
→ learning_asset_candidate_sandbox_build
→ learning_asset_candidate_sandbox_validate
→ learning_asset_candidate_sandbox_review
```

## 实测

- Runtime 总工具数：137
- usage card：137 / 137 全覆盖
- backend compileall：PASS
- frontend compileall：PASS
- pytest：16 passed
- Code-X Runtime smoke：PASS
- frontend bridge smoke：PASS
- R18 candidate sandbox smoke：PASS
- no-pollution：PASS

## 边界判断

R18 是候选包生产沙箱，不是自动 Tool/Skill 发布器。它解决“有契约、有沙箱前置，但没有真实候选包产物”的缺口；后续激活仍必须经 LLM 裁决、质量门、发布门、回滚证据和审计。
