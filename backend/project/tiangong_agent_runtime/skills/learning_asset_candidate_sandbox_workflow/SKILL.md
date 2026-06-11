# R18 Tool/Skill 候选包生产沙箱工作流

用途：当 R16 统一资产契约和 R17 沙箱前置映射已经通过后，LLM 可以要求 Runtime 生成隔离候选包，完成静态扫描、smoke、回滚证据和注册审阅。

## 命令

- `asset-candidate-sandbox guide`：查看 R18 边界和链路。
- `asset-candidate-sandbox build <notes>`：把当前 Tool/Skill 契约落盘为隔离候选包。
- `asset-candidate-sandbox validate`：复核候选包 manifest、静态扫描、smoke、回滚证据。
- `asset-candidate-sandbox review`：生成注册审阅结论，只供 LLM 裁决后续质量门/发布门。
- `asset-candidate-sandbox drill <notes>`：全链演练，从经验候选到候选包审阅。

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

## 硬边界

- 只允许写入 `.linyuanzhe/candidate_sandbox/r18` 下的候选包文件。
- 不得写正式 Skill 注册表。
- 不得注册 Runtime Tool。
- 不得激活 Skill。
- 不得释放工具句柄。
- 不得调用候选工具。
- 不得导入或复制 v1 源码。
- 不得调用模型、网络、shell。
- 不得启动后台 loop。

LLM 是最终裁决者；R18 只提供证据与 next_action_hint。
