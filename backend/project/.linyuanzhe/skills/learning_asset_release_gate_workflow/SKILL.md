# R19 Tool/Skill 候选发布门轻量工作流

用途：当 R18 候选包已经 `review_ready` 后，LLM 用本 Skill 把证据压成四项直接结论：质量门、发布门、回滚证据、注册申请。执行力第一，去掉复杂评分和多级审批。

## 命令

- `asset-release guide`：查看 R19 轻量发布门边界。
- `asset-release gate`：读取当前 R18 候选包审阅报告，生成四项门结论。
- `asset-release drill <notes>`：从经验候选到 R18 候选包，再到 R19 四项门的完整演练。

## 最短链路

1. `learning_asset_candidate_sandbox_review`
2. `learning_asset_release_gate_check`

## 全链演练

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

## 四项门

- 质量门：`review_ready + static_scan_pass + smoke_pass + candidate_boundary_clean`。
- 发布门：只允许形成注册申请，不允许自动注册或激活。
- 回滚证据：每个候选包必须有 `rollback_evidence_path`。
- 注册申请：生成 `.linyuanzhe/candidate_sandbox/r19/r19_release_gate_request.json`，仅供 LLM 审阅。

## 硬边界

- 不得写正式 Skill 注册表。
- 不得注册 Runtime Tool。
- 不得激活 Skill。
- 不得释放工具句柄。
- 不得调用候选工具。
- 不得导入或复制 v1 源码。
- 不得调用模型、网络、shell。
- 不得启动后台 loop。

LLM 是最终裁决者；R19 只输出 ready/block 证据，不自动激活。
