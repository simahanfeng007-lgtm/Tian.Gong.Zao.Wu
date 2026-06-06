# 天工造物新版 L0 零依赖原语层 第八阶段开发日志

## 本阶段目标

本阶段只完成 L0 第八阶段：审计、演化、检索、验证层。目标是在不引入任何真实 IO、网络、模型、工具调用、执行器、调度器或上层系统逻辑的前提下，补齐以下事实语言：产物、证据、审计、版本、命名空间、关系、检索、验证、调度。

## 新增模块清单

- `tiangong_kernel/l0_primitives/artifact.py`
- `tiangong_kernel/l0_primitives/evidence.py`
- `tiangong_kernel/l0_primitives/audit.py`
- `tiangong_kernel/l0_primitives/versioning.py`
- `tiangong_kernel/l0_primitives/namespace.py`
- `tiangong_kernel/l0_primitives/relation.py`
- `tiangong_kernel/l0_primitives/retrieval.py`
- `tiangong_kernel/l0_primitives/validation.py`
- `tiangong_kernel/l0_primitives/schedule.py`

## 每个模块新增对象清单

### artifact.py

- `ArtifactRef`
- `ArtifactKind`
- `ArtifactState`
- `ArtifactDigest`
- `ArtifactVersionRef`
- `ArtifactLocationRef`
- `ArtifactProvenanceRef`
- `ArtifactIntegrityRef`

### evidence.py

- `EvidenceRef`
- `EvidenceKind`
- `EvidenceDigest`
- `EvidenceState`
- `EvidenceSourceRef`

### audit.py

- `AuditRef`
- `AuditTrailRef`
- `AuditEventRef`
- `AccountabilityRef`
- `ResponsibilityRef`
- `ResponsibilityKind`
- `TamperEvidenceRef`
- `IntegrityChainRef`
- `AuditCoverageRef`
- `AuditFindingRef`
- `AuditCoverageKind`
- `AuditFindingKind`

### versioning.py

- `SchemaRef`
- `SchemaVersion`
- `ObjectVersion`
- `VersionRef`
- `MigrationRef`
- `MigrationKind`
- `CompatibilityLevel`
- `DeprecationRef`
- `UpcastRef`
- `TransformRef`
- `VersionState`

### namespace.py

- `NamespaceRef`
- `NamespaceKind`
- `NameRef`
- `QualifiedName`
- `RegistryRef`
- `RegistryKind`
- `NameBindingRef`
- `NameState`
- `AliasRef`
- `DeprecationRef`

### relation.py

- `RelationRef`
- `RelationKind`
- `RelationDirection`
- `RelationStrength`
- `RelationState`
- `DependencyRef`
- `DependencyKind`
- `DependencyState`
- `GraphRef`
- `NodeRef`
- `EdgeRef`
- `PathRef`

### retrieval.py

- `IndexRef`
- `IndexKind`
- `IndexState`
- `QueryRef`
- `QueryKind`
- `QueryIntentRef`
- `QueryScopeRef`
- `RetrievalRef`
- `RetrievalKind`
- `RetrievalState`
- `RetrievalResultRef`
- `RetrievalEvidenceRef`
- `RankingRef`
- `FilterRef`

### validation.py

- `TestRef`
- `TestKind`
- `TestState`
- `TestResultRef`
- `ValidationRef`
- `ValidationKind`
- `ValidationState`
- `VerificationRef`
- `VerificationKind`
- `VerificationState`
- `AssertionRef`
- `AssertionKind`
- `AssertionResultRef`
- `EvaluationRef`
- `EvaluationResultRef`
- `CoverageRef`
- `RegressionRef`

### schedule.py

- `ScheduleRef`
- `ScheduleKind`
- `ScheduleState`
- `TriggerRef`
- `TriggerKind`
- `TriggerState`
- `TimerRef`
- `TimerKind`
- `WakeupRef`
- `WakeupReason`
- `RecurrenceRef`
- `TriggerConditionRef`

## 关键设计取舍

1. 继续坚持 L0 只定义事实语言，不定义执行流程。所有新增对象均为引用、枚举、值对象或轻量事实对象。
2. Artifact 与 Evidence 分离：Artifact 表达产物，Evidence 表达支撑判断的依据，二者可以互相引用但不互相吞并。
3. Audit 只保留审计轨迹、责任、覆盖、发现等引用事实，不生成报告、不连接外部审计系统。
4. Versioning 只表达版本和迁移事实，不实现迁移执行、代码生成、结构目录服务或格式转换。
5. Namespace 只表达命名域、名称、绑定、别名和登记边界，不执行名称解析或服务发现。
6. Relation 只表达语义关系、依赖和图引用，不做图遍历、依赖排序或关系推理。
7. Retrieval 只表达索引、查询、检索和结果引用，不做向量、全文、图、SQL 或外部搜索。
8. Validation 只表达测试、校验、验证、断言、评估、覆盖、回归事实，不执行测试或评估。
9. Schedule 只表达调度、触发、计时、唤醒和重复规则引用，不启动后台任务、不创建队列、不解析周期表达式。
10. `validation.py` 中以 `Test` 开头的 L0 类型显式设置 `__test__ = False`，避免测试框架误识别为测试类；这不改变 L0 事实对象语义。

## 明确未做事项

- 未新增第九阶段或额外 L0 概念。
- 未实现文件生成器、审计报告生成器、schema registry、migration runner、名称解析器、图数据库、图遍历、向量库、RAG、排序算法、测试执行器、runtime verifier、cron、队列或后台任务执行器。
- 未实现 Runtime / ToolExecutor / PluginHost / ModelClient / MemorySystem / PolicyEngine / AuditSystem / SchemaRegistry / GraphDatabase / RetrievalEngine / TestRunner / SchedulerEngine。
- 未引入真实 IO、网络、模型、工具调用、进程启动或插件加载。
- 未引入第三方依赖。

## 测试命令

```bash
python -m compileall -q tiangong_kernel tests
python -m pytest -q tests
```

## 测试结果

```text
106 passed in 0.63s
```

## 失败测试与下一步建议

本阶段无失败测试。

建议下一步进入 L0 全阶段质检，对第一至第八阶段做一次结构性审查：导入边界、第三方依赖、真实 IO 禁令、dataclass 不可变性、稳定序列化、stable_hash、模块边界、命名一致性、重复概念、Ref 纯度、上层逻辑泄漏和设计文档一致性。
