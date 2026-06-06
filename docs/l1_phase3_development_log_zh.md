# 天工造物新版 L1 端口协议层第三阶段开发日志

## 1. 本阶段目标

本阶段只开发 L1 第三阶段：内容、通信、资源、环境端口协议。

目标是为后续 L2-L6 提供稳定、只声明边界、不实现能力的协议层：

- 内容端口：表达内容引用、载荷引用、写入意图、产物登记、证据绑定。
- 通信端口：表达消息、通道、协议、交接、会话引用边界。
- 资源端口：表达资源、预算、配额、速率限制、资源预约边界。
- 环境端口：表达环境、沙箱、位置解析、运行上下文、环境观察边界。

本阶段坚持：工程生命体优先；大模型执行力与绝对边界并重。L1 只定义界限、输入、输出与失败表达方式，不替大模型判断，不提前阻碍后续工具调用链路。

## 2. 新增文件清单

新增源码文件：

1. `tiangong_kernel/l1_ports/content_ports.py`
2. `tiangong_kernel/l1_ports/communication_ports.py`
3. `tiangong_kernel/l1_ports/resource_ports.py`
4. `tiangong_kernel/l1_ports/environment_ports.py`

新增测试文件：

1. `tests/test_l1_phase3_content_ports.py`
2. `tests/test_l1_phase3_communication_ports.py`
3. `tests/test_l1_phase3_resource_ports.py`
4. `tests/test_l1_phase3_environment_ports.py`

新增开发日志：

1. `docs/l1_phase3_development_log_zh.md`

## 3. 新增端口清单

内容端口：

- `ContentStorePort`
- `ContentReadPort`
- `ContentWriteIntentPort`
- `PayloadPort`
- `ArtifactPort`
- `EvidencePort`

通信端口：

- `MessagePort`
- `ChannelPort`
- `ProtocolPort`
- `HandoffPort`
- `ConversationPort`

资源端口：

- `ResourcePort`
- `BudgetPort`
- `QuotaPort`
- `RateLimitPort`
- `ResourceReservationPort`

环境端口：

- `EnvironmentPort`
- `SandboxPort`
- `LocationResolverPort`
- `RuntimeContextPort`
- `EnvironmentObservationPort`

本阶段合计新增 21 个抽象端口。

## 4. 每个端口职责

### 4.1 内容端口

- `ContentStorePort`：定义内容引用进入内容边界的协议。
- `ContentReadPort`：定义按内容引用读取内容事实的协议。
- `ContentWriteIntentPort`：定义写入意图的结构化表达协议。
- `PayloadPort`：定义载荷引用、编码、解码边界的声明协议。
- `ArtifactPort`：定义产物引用、产物登记与产物边界协议。
- `EvidencePort`：定义证据引用与内容、载荷、产物、资源引用之间的绑定协议。

### 4.2 通信端口

- `MessagePort`：定义消息提交、消息读取与消息引用协议。
- `ChannelPort`：定义通道引用和通道启用意图协议。
- `ProtocolPort`：定义通信协议引用和协议声明边界。
- `HandoffPort`：定义交接引用、交接内容与交接边界协议。
- `ConversationPort`：定义会话引用与会话边界协议。

### 4.3 资源端口

- `ResourcePort`：定义资源引用、资源声明与资源边界协议。
- `BudgetPort`：定义预算声明和预算检查协议。
- `QuotaPort`：定义配额引用和配额边界协议。
- `RateLimitPort`：定义速率限制引用和检查边界协议。
- `ResourceReservationPort`：定义资源预约请求协议。

### 4.4 环境端口

- `EnvironmentPort`：定义环境引用和环境边界协议。
- `SandboxPort`：定义沙箱引用和沙箱边界协议。
- `LocationResolverPort`：定义位置引用和位置解析边界协议。
- `RuntimeContextPort`：定义运行上下文边界协议。
- `EnvironmentObservationPort`：定义环境观察结果协议。

## 5. 每个端口明确不做什么

### 5.1 内容端口不做

- 不实现真实内容存储。
- 不读取真实文件、网络或数据库。
- 不执行真实文件写入或覆盖。
- 不生成真实产物。
- 不复制、上传或读取真实证据材料。

### 5.2 通信端口不做

- 不连接真实聊天系统。
- 不建立真实通道。
- 不实现协议解析器。
- 不发送真实交接消息。
- 不实现对话存储或真实上下文拼接算法。

### 5.3 资源端口不做

- 不占用真实资源。
- 不计算真实预算。
- 不连接真实限额系统。
- 不实现真实限流器。
- 不锁定真实资源。

### 5.4 环境端口不做

- 不读取真实系统环境变量。
- 不探测真实机器。
- 不启动真实沙箱或进程。
- 不读取真实路径、不访问地理位置、不扫描文件系统。
- 不创建真实运行时、不调度任务。
- 不采集真实环境。

## 6. 与 L0 的依赖关系

本阶段继续复用 L0 原语和值对象，未重新发明同义引用对象。主要复用：

- `CoreResult`
- `TraceContext`
- `ContentRef`
- `PayloadRef`
- `ArtifactRef`
- `EvidenceRef`
- `MessageRef`
- `ChannelRef`
- `ProtocolRef`
- `HandoffRef`
- `ConversationRef`
- `ResourceRef`
- `BudgetRef`
- `QuotaRef`
- `RateLimitRef`
- `EnvironmentRef`
- `SandboxRef`
- `LocationRef`
- `ObservationRef`
- `SignalRef`
- `ActorRef`
- `ScopeRef`
- `SchemaRef`
- `VersionRef`
- `NamespaceRef`
- `ValidationRef`
- `VerificationRef`

所有端口方法返回 `CoreResult` 或 `PortResult`，没有返回裸 `dict`、裸 `bool`、裸 `str` 或裸 `list` 作为主返回值。

## 7. 与 L1 第一、第二阶段骨架的关系

本阶段未修改 L0。

本阶段未修改 L1 第一阶段公共骨架：

- `__init__.py`
- `base.py`
- `port_result.py`
- `port_error.py`
- `port_boundary.py`
- `port_health.py`
- `port_lifecycle.py`
- `envelope.py`

本阶段未重构 L1 第二阶段内容：

- `infrastructure_ports.py`
- `event_ports.py`
- `observation_ports.py`
- `metric_ports.py`
- `audit_ports.py`

本阶段只新增第三阶段允许的端口协议模块、专项测试和开发日志。

## 8. 面向 L2-L6 的前瞻引用说明

- L2 生命体状态层可引用内容、通信、资源、环境端口记录状态来源和边界来源。
- L3 运行编排层可通过这些端口组织消息、内容流、资源预算、环境边界，但真实编排不在 L1 实现。
- L4 外部适配层可实现真实文件、网络、通道、环境、沙箱适配器，但 L1 只保留协议。
- L5 插件宿主层可借这些端口隔离插件通信、资源预算和环境边界，但插件宿主不在本阶段实现。
- L6 子系统插件层可通过这些端口传递内容引用、上下文、资源意图和环境观察，但不能绕过边界。

## 9. 禁止事项检查

已检查本阶段源码：

- 无 L2-L6 import。
- 无第三方库 import。
- 无旧版天工造物上层模块 import。
- 无真实文件 IO 调用。
- 无真实网络调用。
- 无真实数据库调用。
- 无后台任务、线程、进程启动。
- 无真实内容存储、内容读取、文件写入、产物生成。
- 无真实消息发送、通道连接、协议解析。
- 无真实预算计算、限流、资源锁定。
- 无真实沙箱启动、路径解析、环境探测。
- 无真实模型调用、工具调用、插件加载。

## 10. 测试命令

已运行：

```bash
python3 -m compileall -q tiangong_kernel tests
```

已运行：

```bash
python3 -m pytest -q tests
```

已单独运行必测项：

```bash
python3 -m pytest -q tests/test_l1_no_l2_imports.py
python3 -m pytest -q tests/test_l1_no_third_party_imports.py
python3 -m pytest -q tests/test_l1_no_real_io.py
python3 -m pytest -q tests/test_l1_ports_are_abstract.py
python3 -m pytest -q tests/test_l1_ports_return_core_result.py
python3 -m pytest -q tests/test_l1_uses_l0_primitives.py
python3 -m pytest -q tests/test_l1_no_execution_keywords.py
python3 -m pytest -q tests/test_l1_chinese_docstrings.py
```

已运行新增第三阶段专项测试：

```bash
python3 -m pytest -q tests/test_l1_phase3_content_ports.py
python3 -m pytest -q tests/test_l1_phase3_communication_ports.py
python3 -m pytest -q tests/test_l1_phase3_resource_ports.py
python3 -m pytest -q tests/test_l1_phase3_environment_ports.py
```

## 11. 测试结果

结果如下：

- `python3 -m compileall -q tiangong_kernel tests`：通过。
- `python3 -m pytest -q tests`：`162 passed in 2.84s`。
- `tests/test_l1_no_l2_imports.py`：`1 passed`。
- `tests/test_l1_no_third_party_imports.py`：`1 passed`。
- `tests/test_l1_no_real_io.py`：`1 passed`。
- `tests/test_l1_ports_are_abstract.py`：`1 passed`。
- `tests/test_l1_ports_return_core_result.py`：`2 passed`。
- `tests/test_l1_uses_l0_primitives.py`：`1 passed`。
- `tests/test_l1_no_execution_keywords.py`：`1 passed`。
- `tests/test_l1_chinese_docstrings.py`：`1 passed`。
- `tests/test_l1_phase3_content_ports.py`：`4 passed`。
- `tests/test_l1_phase3_communication_ports.py`：`4 passed`。
- `tests/test_l1_phase3_resource_ports.py`：`4 passed`。
- `tests/test_l1_phase3_environment_ports.py`：`4 passed`。

说明：由于 shell 顺序运行多条 pytest 命令时，容器工具曾在长串命令执行末尾出现超时截断；被截断的命令均已改为单独命令重新运行并通过。最终全量测试和单项测试均通过。

## 12. 未做事项

按阶段边界，本阶段明确未做：

- 未开发阶段 4-8。
- 未开发 `SkillPort`、`SkillRegistryPort`、`SkillExposurePort`。
- 未开发 `ToolPort`、`ToolGroupPort`、`ToolReleasePort`。
- 未开发 `ModelPort`、`ModelSessionPort`。
- 未开发 `MemoryPort`、`ContextPort`、`RetrievalPort`、`LearningPort`。
- 未开发 `PluginPort`、`RegistryPort`。
- 未开发 `SchedulePort`、`TriggerPort`、`TimerPort`。
- 未开发 `BoundaryCheckPort`、`PolicyPort`、`RiskPort`、`DecisionPort`。
- 未实现真实状态机。
- 未实现真实运行循环。
- 未实现真实工具释放。
- 未实现真实模型会话。
- 未实现真实记忆算法。
- 未实现真实插件宿主。
- 未实现真实安全裁决。
- 未生成 zip。

## 13. 是否允许进入 L1 第四阶段

允许进入 L1 第四阶段。

理由：第三阶段新增端口协议、请求响应对象、边界对象、专项测试和开发日志均已完成；第一、第二阶段测试未回退；全量测试通过；L0 未修改；未提前实现第四至第八阶段能力。
