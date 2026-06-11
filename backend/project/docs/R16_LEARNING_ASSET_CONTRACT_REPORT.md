# L6.70.2 R16 未来 Tool/Skill 统一资产契约报告

## 结论

R15 只能部分保证未来资产格式统一：已有 L6.20 经验候选、L6.21 Skill 队列、L6.22 Tool 请求，但三者 schema 分离，没有统一契约和强制校验入口。

R16 已补齐：

- `learning_asset_contract_guide`
- `learning_asset_contract_normalize`
- `learning_asset_contract_validate`
- `skill.learning_asset_contract_workflow`
- PlanBridge 路由：`asset-contract guide / normalize / validate / drill`
- Runtime 风险分类：A2 元数据工具，不生产、不注册、不激活
- Runtime alignment usage card 覆盖

## 未来强制规则

未来所有自主学习、经验总结、Skill 草案、Tool 缺口和 Tool 生产请求，必须先转换为：

```text
tiangong.l6702.r16.learning_asset_contract.v1
```

通过 `learning_asset_contract_validate` 前，不得进入正式 Tool 生产、Skill 激活或 Runtime 注册。

## 候选阶段边界

- 不写 Skill 注册表
- 不生产 Tool 代码
- 不注册 Tool
- 不释放工具句柄
- 不调用未注册工具
- 不触碰内核
- 不启动后台 loop
- 不复用 v1 源码 / import / registry / executor / provider / self-iteration

## 推荐未来链路

```text
synthesize_experience_candidates
→ queue_skill_candidates / queue_tool_production_requests
→ learning_asset_contract_normalize
→ learning_asset_contract_validate
→ quality_gate
→ release_gate
→ LLM 最终裁决是否进入沙箱生产链
```
