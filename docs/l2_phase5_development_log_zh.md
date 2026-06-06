# 天工造物 L2 第五阶段开发日志

生成日期：2026-06-03

## 阶段目标

第五阶段新增 L2 观察面状态对象，用于稳定记录外部观察系统、端口、适配器、工具、模型、执行面或测试系统已经给出的观察事实。

本阶段只回答“发生过什么、从哪里观察到、可信度如何、是否完整、是否延迟、是否冲突、是否可用于反馈、审计、候选、验证与恢复的后续判断”。本阶段不做真实观察采集、不读取日志、不采样指标、不写审计、不调用模型或工具、不进入第六阶段。

## 前置检查

- L2 第一至第四阶段回归：78 passed。
- `python -m compileall -q tiangong_kernel tests`：通过。
- L1 最终归档记录：326 passed。
- L0 hash 归档记录：58 个文件，无新增、无删除、无变更。
- 第四阶段验证报告显示完整 pytest：404 passed。

## 新增源码

- `tiangong_kernel/l2_state/observation_source_state.py`
- `tiangong_kernel/l2_state/observation_channel_state.py`
- `tiangong_kernel/l2_state/observation_frame_state.py`
- `tiangong_kernel/l2_state/event_stream_state.py`
- `tiangong_kernel/l2_state/observation_metric_state.py`
- `tiangong_kernel/l2_state/audit_observation_state.py`
- `tiangong_kernel/l2_state/observation_quality_state.py`
- `tiangong_kernel/l2_state/observation_projection_state.py`

## 修改源码

- `tiangong_kernel/l2_state/__init__.py`
  - 仅新增第五阶段对象导入和 `__all__` 导出。
  - 未删除或改名第一至第四阶段公开导出。

## 新增测试

- `tests/test_l2_phase5_imports.py`
- `tests/test_l2_phase5_observation_source_state.py`
- `tests/test_l2_phase5_observation_channel_state.py`
- `tests/test_l2_phase5_observation_frame_state.py`
- `tests/test_l2_phase5_event_stream_state.py`
- `tests/test_l2_phase5_observation_metric_state.py`
- `tests/test_l2_phase5_audit_observation_state.py`
- `tests/test_l2_phase5_observation_quality_state.py`
- `tests/test_l2_phase5_observation_projection_state.py`
- `tests/test_l2_phase5_no_real_observers_or_io.py`
- `tests/test_l2_phase5_no_upper_layer_imports.py`
- `tests/test_l2_phase5_cross_phase_references.py`

## 状态对象摘要

### ObservationSourceState

作用：记录观察源引用、来源类型、来源状态、边界、安全、环境、可信标签和前置主链对象引用。

边界：这是状态对象，不是观察器、采集器或监听器；不读取模型输出、工具结果、日志、事件源或外部适配器。

### ObservationChannelState

作用：记录观察通道引用、通道类型、通道状态、观察源、边界、资源、安全和可见范围引用。

边界：不实现通道、订阅、发布、传输、队列、监听或轮询。

### ObservationFrameState

作用：记录一次观察事实的结构化快照，包括来源、通道、被观察对象、短摘要、payload 引用、质量、边界和安全引用。

边界：不解析真实日志、真实模型输出或真实工具结果；`observed_summary` 为短摘要，`observed_payload_ref` 只能保存引用。

### EventStreamState

作用：记录外部报告的事件流状态、来源、通道、最新帧、帧计数、中断和截断原因引用。

边界：不实现事件总线、SSE、WebSocket、generator、iterator 或真实队列消费。

### ObservationMetricState

作用：记录外部给出的指标快照，包括指标类型、状态、名称、值表示、单位、窗口、资源、运行、任务和质量引用。

边界：不采样、不统计、不读取系统指标、不扣减资源预算或配额。

### AuditObservationState

作用：记录审计相关观察事实引用，连接帧、事件流、指标、Run、Task、Skill、ToolGroup、ToolIntent、Action、Effect、Boundary 和 Security。

边界：不写审计日志、不写数据库、不签名、不验签、不归档、不做最终责任归因。

### ObservationQualityState

作用：记录外部给出的观察质量维度、质量状态、质量标签、短摘要、帧、指标、审计、边界和安全引用。

边界：不计算质量评分、不计算可信度、不解决冲突、不自动决定观察是否可用。

### ObservationProjectionState

作用：记录由观察帧、事件流、指标、审计和质量状态组成的观察面局部结构化投影。

边界：不生成聊天文本、不生成最终模型提示词、不做自然语言总结器、不选择下一步行动、不触发候选、验证或恢复。

## 跨阶段接线

第五阶段新增测试构造了纯状态链：

RunState → SkillState → ToolIntentState → ActionIntentState → EffectObservationState → ObservationFrameState → ObservationQualityState → AuditObservationState → ObservationProjectionState

同时连接第四阶段 BoundaryCheckState、ResourceBudgetState、EnvironmentState、SecurityBoundaryState。所有连接均通过 `TypedRef` / `state_ref` 完成，不嵌入执行器、监听器、观察器、模型客户端、工具实例或可变对象。

## 前置阶段兼容修复

无。

## 明确未做

- 未开发第六阶段记忆、上下文、检索、学习状态。
- 未开发第七阶段候选、变更、实验、验证、恢复状态。
- 未开发第八阶段全局状态投影、组件或兼容迁移总收口。
- 未实现真实观察器、日志读取器、指标采样器、事件总线、审计写入、链路追踪、外设读取、环境探测、安全扫描、模型调用、工具调用、调度器、运行循环、插件宿主或存储层。
- 未恢复旧能力包、CapabilityPort、AbilityPackagePort、“神枢”或旧 Runtime 主链。
