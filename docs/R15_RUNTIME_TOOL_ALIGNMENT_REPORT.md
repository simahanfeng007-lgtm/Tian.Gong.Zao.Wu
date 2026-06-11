# L6.70.2 R15 Runtime 工具注册表 / Skill / LLM 实操对齐报告

## 结论

R15 在 R14 基线之上完成全局对齐：Runtime 已注册工具、风险分级、Skill 来源、usage card、PlanBridge 入口和 LLM 路由演练均通过。

## 新增 Runtime 工具

- `runtime_tool_alignment_check`：检查全局 Runtime 工具注册表、风险分级、Skill 使用卡、LLM 入口与无污染断言。
- `runtime_llm_operational_drill`：模拟 LLM 从用户意图到 PlanBridge 再到 Runtime 工具名的路由链，确认工具名均已注册且无空路由。

## 新增命令

- `runtime-tools align`
- `runtime-tools drill`
- `runtime-tools tool <tool_name> {json_args}`

## 本轮实测

- Runtime 总工具数：127
- LLM usage cards：127
- 注册表对齐 issue：0
- LLM 路由演练场景：29
- 空路由：0
- 缺失工具路由：0
- 代表性真实执行链：19 组，全 PASS
- pytest：10 passed
- backend compileall：PASS
- frontend compileall：PASS
- Code-X Runtime smoke：PASS
- v1 clean import smoke：PASS
- frontend Code-X bridge smoke：PASS
- no-pollution：PASS

## 边界

- 不复制 v1 源码。
- 不 import v1。
- 不复用 v1 registry / executor / terminal / provider / self-iteration。
- 不 monkey patch。
- 不启动后台 loop。
- Runtime 对齐工具只读元数据，不执行目标工具，不修改注册表。
- Planner 只建议，LLM 保留最终裁决权。
