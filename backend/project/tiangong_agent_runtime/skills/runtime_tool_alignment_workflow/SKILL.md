# Runtime Tool Alignment Workflow

用途：让 LLM 在使用临渊者 Runtime 时，先确认“工具已注册、风险已对齐、Skill/usage card 可见、Planner 路由可达”，再执行真实工具链。

## 入口命令

- `runtime-tools align`：检查全局 Runtime 注册表、风险分级、usage card、Skill 来源和无污染断言。
- `runtime-tools drill`：模拟 LLM 从用户意图到 PlanBridge 到 Runtime 工具名的路由链。
- `runtime-tools tool <tool_name> {json_args}`：由 LLM 明确选择任意已注册工具，并交给 Runtime 审计链执行。

## 使用规则

1. 不确定该用哪个工具时，先调用 `runtime_tool_alignment_check`。
2. 确认任务属于代码生产链时，转入 `code_x_skill_guide`。
3. 确认任务属于非 Code-X 搜索/文档/学习/ToolSkill 草案时，转入 `v1_clean_import_guide`。
4. 写 workspace 前必须先有快照或明确的 Runtime 写入工具审计。
5. 测试失败后不能停止，必须进入失败归因或 handoff。
6. Planner 只给建议；最终工具选择、是否写入、是否回滚由 LLM 裁决。

## 边界

- 本 Skill 不执行目标工具。
- 本 Skill 不修改注册表。
- 本 Skill 不复制或 import v1。
- 本 Skill 不启动后台 loop。
- A0-A4 默认允许并留痕，A5 才硬拦。
