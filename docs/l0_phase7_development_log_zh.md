# 天工造物新版 L0 零依赖原语层第七阶段开发日志

## 本阶段目标

本阶段只完成 L0 第七阶段：外部世界引用层。目标是在不引入任何真实 IO、网络、模型、工具调用、资源管理、通信协议实现、Skill 执行或包管理逻辑的前提下，补齐外部世界相关引用事实语言。

本阶段继续遵守《天工造物全局架构宪法 v0.1》和《天工造物 L0 零依赖原语层设计 v0.1》：L0 只定义可稳定序列化、可审计、可哈希、不可变的最小事实语言；不执行真实动作；不依赖 L1-L6；只使用 Python 标准库。

## 新增模块清单

- `tiangong_kernel/l0_primitives/resource.py`
- `tiangong_kernel/l0_primitives/cost_budget.py`
- `tiangong_kernel/l0_primitives/environment.py`
- `tiangong_kernel/l0_primitives/location.py`
- `tiangong_kernel/l0_primitives/communication.py`
- `tiangong_kernel/l0_primitives/tool_adapter.py`
- `tiangong_kernel/l0_primitives/skill_capability.py`
- `tiangong_kernel/l0_primitives/component_package.py`

## 每个模块新增对象清单

### resource.py

- `ResourceRef`
- `ResourceKind`
- `ResourceQuantity`
- `ResourceUsage`
- `ResourceBudget`
- `ResourceLimit`
- `ResourcePressure`
- `EnergyBudget`

### cost_budget.py

- `CostRef`
- `CostKind`
- `CostAmount`
- `BudgetRef`
- `BudgetKind`
- `BudgetWindow`
- `BudgetState`
- `QuotaRef`
- `QuotaKind`
- `QuotaWindow`
- `QuotaState`
- `RateLimitRef`
- `RateLimitKind`
- `RateLimitWindow`
- `RateLimitState`
- `CostEstimateRef`
- `CostActualRef`

### environment.py

- `EnvironmentRef`
- `EnvironmentKind`
- `EnvironmentState`
- `SandboxRef`
- `SandboxKind`
- `IsolationBoundaryRef`
- `IsolationLevel`
- `EnvironmentFingerprint`
- `EnvironmentCapabilityRef`

### location.py

- `LocationRef`
- `LocationKind`
- `AddressRef`
- `AddressKind`
- `URIRef`
- `URIKind`
- `LocatorRef`
- `LocatorKind`
- `LocationState`
- `ResolutionHintRef`

### communication.py

- `CommunicationRef`
- `MessageEnvelopeRef`
- `MessageKind`
- `MessageDirection`
- `ChannelRef`
- `ChannelKind`
- `ProtocolRef`
- `ProtocolKind`
- `DeliveryState`
- `ReplyToRef`
- `ConversationRef`
- `HandoffRef`

### tool_adapter.py

- `ToolRef`
- `AdapterRef`
- `ToolKind`
- `AdapterKind`
- `ToolState`
- `ToolVersionRef`
- `AdapterVersionRef`

### skill_capability.py

- `SkillRef`
- `CapabilityRef`
- `CapabilityKind`
- `CapabilityState`
- `CapabilityOriginRef`
- `CapabilityRiskRef`
- `CapabilityVersionRef`

### component_package.py

- `ComponentRef`
- `ComponentKind`
- `ComponentState`
- `ModuleRef`
- `ModuleKind`
- `ModuleState`
- `PackageRef`
- `PackageKind`
- `PackageState`
- `PackageDigest`
- `PackageVersionRef`
- `ComponentInterfaceRef`
- `ComponentBoundaryRef`

## 关键设计取舍

1. 资源只表达引用与数量事实，不表达真实资源采集和分配。`ResourceUsage`、`ResourceBudget`、`ResourceLimit` 都是事实对象，不承担管理职责。
2. 成本、预算、配额和频率限制只表达边界事实，不绑定真实 API 价格、token 计算、限流和扣费。
3. 环境与沙箱只表达环境引用、隔离边界与环境指纹，不启动容器、虚拟机、浏览器或进程。
4. 位置、地址、URI 与定位器只表达可寻址事实，不解析 URI、不规范化路径、不访问文件或网络。
5. 通信层只表达消息外壳、通道、协议和交接事实，不实现任何传输协议、路由、重试或队列。
6. 工具与适配器只表达引用、类别、状态与版本，不定义工具 schema、不执行工具、不绑定外部协议实现。
7. Skill 与 Capability 只表达可复用方法或能力引用，不执行、选择、组合、扫描或分发能力。
8. Component、Module、Package 只表达可组合、可替换、可治理单元引用，不加载插件、不安装包、不解析依赖。
9. 所有新增 dataclass 均使用 `frozen=True, slots=True`，字段仅保存不可变值、枚举或引用对象。
10. 所有新增对象均保持可 `stable_json_dumps` 与 `stable_hash`。

## 明确未做事项

- 未做第八阶段。
- 未实现真实资源管理、计费、限流、沙箱、URI 解析、通信协议、工具执行、Skill 执行、插件加载、包管理、依赖解析。
- 未写 Runtime、ToolExecutor、PluginHost、ModelClient、MemorySystem、PolicyEngine、ResourceManager、SandboxManager、CommunicationBus、ToolRegistry、SkillSystem、PackageManager 等上层系统逻辑。
- 未引入第三方依赖。
- 未引入真实 IO、网络、模型或工具调用。

## 测试命令

```bash
python -m compileall -q tiangong_kernel tests
python -m pytest -q tests
```

## 测试结果

```text
93 passed in 0.74s
```

## 失败测试说明与下一步建议

本阶段无失败测试。

下一步建议：在新对话中进入第八阶段前，先做一次 L0 阶段 1-7 的聚合质检，重点检查：枚举命名一致性、Ref 字段命名一致性、稳定序列化覆盖率、禁止执行逻辑覆盖率、中文 docstring 完整性，以及是否存在 L0 概念膨胀。
