# 天工造物新版 L1 端口协议层第二阶段开发日志

## 1. 本阶段目标

本阶段只开发 L1 第二阶段：基础设施、事件、观察、指标与审计端口协议。
本阶段目标是为后续 L2-L6 提供稳定的协议边界、请求对象、响应对象、边界对象与失败表达方式。

本阶段坚持两条方向：

1. 第一方向：工程生命体。
2. 第二方向：大模型执行力 + 绝对边界。

边界只定义界限、输入、输出和失败表达，不替大模型判断，不提前阻断后续阶段的工具使用能力。

## 2. 新增文件清单

新增源码文件：

1. `tiangong_kernel/l1_ports/infrastructure_ports.py`
2. `tiangong_kernel/l1_ports/event_ports.py`
3. `tiangong_kernel/l1_ports/observation_ports.py`
4. `tiangong_kernel/l1_ports/metric_ports.py`
5. `tiangong_kernel/l1_ports/audit_ports.py`

新增测试文件：

1. `tests/test_l1_phase2_infrastructure_ports.py`
2. `tests/test_l1_phase2_event_ports.py`
3. `tests/test_l1_phase2_observation_ports.py`
4. `tests/test_l1_phase2_metric_ports.py`
5. `tests/test_l1_phase2_audit_ports.py`

新增日志文件：

1. `docs/l1_phase2_development_log_zh.md`

## 3. 新增端口清单

基础设施端口：

1. `ClockPort`
2. `IdGeneratorPort`
3. `SerializationPort`
4. `HashPort`
5. `LoggerPort`

事件端口：

1. `EventAppendPort`
2. `EventReadPort`
3. `EventStreamPort`
4. `EventQueryPort`

观察端口：

1. `ObservationSubmitPort`
2. `ObservationReadPort`
3. `SignalPort`
4. `TelemetryPort`

指标端口：

1. `MetricRecordPort`
2. `MetricReadPort`
3. `MetricQueryPort`

审计端口：

1. `AuditAppendPort`
2. `AuditReadPort`
3. `EvidenceAttachPort`

## 4. 每个端口职责

### 4.1 ClockPort

职责：声明时间查询协议。
不做：不读取真实系统时间，不同步时钟，不启动定时器，不调度任务。

### 4.2 IdGeneratorPort

职责：声明 L0 `RefId` 生成协议。
不做：不实现标识生成算法，不访问注册表，不保证外部唯一性。

### 4.3 SerializationPort

职责：声明 `PayloadRef` 与 `ContentRef` 之间的序列化 / 反序列化协议边界。
不做：不实现真实序列化器，不读取或写入资源，不构造后续层对象。

### 4.4 HashPort

职责：声明内容、载荷或资源摘要事实协议。
不做：不读取真实内容，不执行摘要计算，不执行密码学流程。

### 4.5 LoggerPort

职责：声明日志事实提交协议。
不做：不写日志，不打印，不落盘，不发送远程日志。

### 4.6 EventAppendPort

职责：声明 `CoreEvent` 追加协议。
不做：不存储事件，不广播事件，不触发订阅者。

### 4.7 EventReadPort

职责：声明按 `EventRef` 读取事件事实协议。
不做：不读取文件、数据库或消息队列，不回放事件。

### 4.8 EventStreamPort

职责：声明事件流可见范围和返回引用协议。
不做：不启动后台任务，不连接网络，不创建消息队列，不推送事件。

### 4.9 EventQueryPort

职责：声明按 `QueryRef` 和 `QueryEnvelope` 查询事件引用协议。
不做：不实现查询引擎，不聚合，不访问真实索引。

### 4.10 ObservationSubmitPort

职责：声明观察事实提交协议。
不做：不采集真实环境，不解释观察含义，不修改状态。

### 4.11 ObservationReadPort

职责：声明按 `ObservationRef` 读取观察事实协议。
不做：不读取真实存储，不扫描环境，不生成观察。

### 4.12 SignalPort

职责：声明信号事实发送与接收协议。
不做：不触发真实行为，不创建消息队列，不启动监听。

### 4.13 TelemetryPort

职责：声明遥测事实提交协议。
不做：不采样，不远程上报，不连接外部遥测系统。

### 4.14 MetricRecordPort

职责：声明指标事实记录协议。
不做：不采样，不写入指标系统，不远程上报。

### 4.15 MetricReadPort

职责：声明按指标引用读取指标事实协议。
不做：不访问真实数据库，不计算指标，不生成报表。

### 4.16 MetricQueryPort

职责：声明按 `QueryRef` 查询指标引用协议。
不做：不实现聚合算法，不读取真实存储，不生成指标索引。

### 4.17 AuditAppendPort

职责：声明审计事实追加协议。
不做：不落盘，不生成报告，不执行合规判断。

### 4.18 AuditReadPort

职责：声明按审计引用读取审计事实协议。
不做：不访问真实审计库，不扫描日志，不生成审计报告。

### 4.19 EvidenceAttachPort

职责：声明证据引用与审计、事件、内容、载荷或资源引用之间的绑定协议。
不做：不复制文件，不上传文件，不读取文件，不执行外部取证。

## 5. 与 L0 的依赖关系

本阶段复用 L0 事实对象与引用对象，包括：

- `CoreResult`
- `TraceContext`
- `CoreEvent`
- `EventRef`
- `ObservationRef`
- `SignalRef`
- `MetricRef`
- `AuditRef`
- `EvidenceRef`
- `ContentRef`
- `PayloadRef`
- `ActorRef`
- `ScopeRef`
- `ResourceRef`
- `VersionRef`
- `SchemaRef`
- `NamespaceRef`

本阶段未重新发明与 L0 同义的 Ref。

## 6. 与 L1 第一阶段骨架的关系

本阶段复用第一阶段对象：

- `PortResult`
- `PortBoundary`
- `CommandEnvelope`
- `QueryEnvelope`

本阶段没有修改 L1 第一阶段公共骨架，没有修改 `__init__.py` 导出集合，没有降低第一阶段测试强度。

## 7. 面向 L2-L6 的前瞻引用说明

- L2：可引用事件、观察、指标、审计端口表达状态来源与生命体状态事实。
- L3：可通过端口协议提交运行事件、读取观察、记录指标、追加审计。
- L4：可实现本阶段端口，但 L1 不提供实现。
- L5：可通过事件、指标、审计端口记录插件生命周期与健康事实。
- L6：可通过观察、信号、指标和审计端口提交记忆、学习、检索、自愈等子系统事实。

## 8. 禁止事项检查

已检查并遵守：

- 未修改 L0。
- 未开发 L1 第三阶段到第八阶段内容。
- 未实现 Skill、Tool、Model、Memory、Context、Retrieval、Learning、Plugin、Registry、Schedule、Trigger、Timer 等端口。
- 未实现真实外部能力。
- 未引入第三方库。
- 未导入 L2-L6。
- 未访问文件、网络、数据库、后台任务、真实环境、模型或工具。
- 所有端口均为抽象协议。
- 所有端口方法返回 `CoreResult` 或 `PortResult`。
- 请求、响应、边界对象使用 `@dataclass(frozen=True, slots=True)`。
- 模块与公开类均有中文说明。

## 9. 测试命令

要求运行：

```bash
python3 -m compileall -q tiangong_kernel tests
python3 -m pytest -q tests
python3 -m pytest -q tests/test_l1_no_l2_imports.py
python3 -m pytest -q tests/test_l1_no_third_party_imports.py
python3 -m pytest -q tests/test_l1_no_real_io.py
python3 -m pytest -q tests/test_l1_ports_are_abstract.py
python3 -m pytest -q tests/test_l1_ports_return_core_result.py
python3 -m pytest -q tests/test_l1_uses_l0_primitives.py
python3 -m pytest -q tests/test_l1_no_execution_keywords.py
python3 -m pytest -q tests/test_l1_chinese_docstrings.py
python3 -m pytest -q tests/test_l1_phase2_infrastructure_ports.py
python3 -m pytest -q tests/test_l1_phase2_event_ports.py
python3 -m pytest -q tests/test_l1_phase2_observation_ports.py
python3 -m pytest -q tests/test_l1_phase2_metric_ports.py
python3 -m pytest -q tests/test_l1_phase2_audit_ports.py
```

## 10. 测试结果

已运行并通过：

```bash
python3 -m compileall -q tiangong_kernel tests
# 通过，无错误输出

python3 -m pytest -q tests
# 146 passed in 2.94s

python3 -m pytest -q tests/test_l1_no_l2_imports.py
# 1 passed

python3 -m pytest -q tests/test_l1_no_third_party_imports.py
# 1 passed

python3 -m pytest -q tests/test_l1_no_real_io.py
# 1 passed

python3 -m pytest -q tests/test_l1_ports_are_abstract.py
# 1 passed

python3 -m pytest -q tests/test_l1_ports_return_core_result.py
# 2 passed

python3 -m pytest -q tests/test_l1_uses_l0_primitives.py
# 1 passed

python3 -m pytest -q tests/test_l1_no_execution_keywords.py
# 1 passed

python3 -m pytest -q tests/test_l1_chinese_docstrings.py
# 1 passed

python3 -m pytest -q tests/test_l1_phase2_infrastructure_ports.py
# 4 passed

python3 -m pytest -q tests/test_l1_phase2_event_ports.py
# 4 passed

python3 -m pytest -q tests/test_l1_phase2_observation_ports.py
# 4 passed

python3 -m pytest -q tests/test_l1_phase2_metric_ports.py
# 4 passed

python3 -m pytest -q tests/test_l1_phase2_audit_ports.py
# 4 passed
```

补充检查：

```bash
diff -qr 原始主体包/project/tiangong_kernel/l0_primitives 当前工程/project/tiangong_kernel/l0_primitives
# 排除缓存后无差异，确认未修改 L0。
```

## 11. 未做事项

本阶段按边界未做：

- 未开发第三阶段到第八阶段。
- 未开发 SkillPort、ToolPort、ToolGroupPort、ModelPort。
- 未开发 MemoryPort、ContextPort、RetrievalPort、LearningPort。
- 未开发 PluginPort、RegistryPort、SchedulePort、TriggerPort、TimerPort。
- 未实现真实状态机、真实运行循环、真实工具释放、真实模型会话、真实记忆算法、真实插件宿主。
- 未生成 zip。

## 12. 是否允许进入 L1 第三阶段

若完整测试全部通过，建议进入 L1 第三阶段。
如果完整测试未通过，应先修复本阶段问题，不建议进入第三阶段。
