# 临渊者 L6.37 执行链冻结契约

- schema: `tiangong.l6_37.execution_chain_freeze.v1`
- source_version: `L6.37-execution-chain-freeze-baseline`
- status: `frozen`

## 唯一治理链

- CLI/API/UserTask
- SessionContextInjection
- ModelPlanner/RulePlanner/HybridPlanner
- DeepSeekPlanShapeNormalizer
- PlanSchemaValidator
- PlannerExecutionController
- LongChainRunner
- ExecutionSpine
- RiskClassifier
- PermitGateway
- RuntimeToolRegistry
- Adapter
- AuditBridge
- PlannerExecutionReport
- L6.36FailureRecoveryReplayQuality

## 禁止第二执行通道

- plugin_direct_tool_call
- provider_naked_sdk_call
- skill_direct_activation
- handoff_recursive_spawn_without_ticket
- frontend_bypass_planner_execution_controller
- direct_adapter_call_outside_execution_spine
- registry_mutation_during_task_run
- kernel_mutation_from_l6_shell
- secret_read_in_planner_or_report

## 后续系统接入原则

Provider、Skill、Handoff、预算、回滚、情志、前端、安装产品化等系统只能提交 Hint / Step / Ticket / Evidence / Report，不能直接执行工具、裸调模型 SDK、激活 Skill、派生子智能体或修改内核。