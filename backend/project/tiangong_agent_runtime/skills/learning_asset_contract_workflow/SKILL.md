# R16 未来 Tool / Skill 统一资产契约 Skill

## 目标

未来所有由自主学习、经验总结、失败复盘、作业复用、Skill 候选、Tool 缺口候选产生的资产，必须先归一为 `tiangong.l6702.r16.learning_asset_contract.v1`，再进入审阅、沙箱、质量门和发布门。

## LLM 使用顺序

1. 需要查看格式：调用 `learning_asset_contract_guide`。
2. 已有经验候选 / Skill 草案 / Tool 请求：调用 `learning_asset_contract_normalize`。
3. 准备进入后续生产、激活或发布前：调用 `learning_asset_contract_validate`。
4. 校验通过后才允许 LLM 裁决是否进入沙箱生产链；候选阶段不得写 Skill 注册表，不得生成真实 Tool 代码，不得注册工具。

## 统一字段

每个资产必须包含：

- `schema`
- `asset_ref`
- `asset_kind`
- `namespace`
- `name`
- `version`
- `status`
- `source_trace`
- `purpose`
- `trigger_rules`
- `input_contract`
- `output_contract`
- `runtime_binding`
- `usage_card`
- `chain_recipe`
- `risk_profile`
- `validation_contract`
- `rollback_contract`
- `audit_contract`
- `llm_policy`
- `lifecycle`

## 硬边界

- LLM 是主脑；Planner 只建议。
- 候选阶段只能产生元数据，不得自动激活。
- 子代理只能提供 evidence / summary / next_action_hint。
- 不复制 v1 源码，不 import v1，不复用 v1 registry / executor / terminal / provider / self-iteration。
- 不 monkey patch，不启动后台 loop。
- A5 才硬拦，A0-A4 默认允许并留痕。

## 常用命令

```text
asset-contract guide
asset-contract normalize
asset-contract validate
asset-contract drill 未来所有自主学习和经验总结生产的 tool 与 skill 格式统一
```
