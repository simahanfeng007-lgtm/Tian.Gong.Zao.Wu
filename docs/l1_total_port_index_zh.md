# 天工造物新版 L1 总端口索引（稳定性整修版）

生成时间：2026-06-03

## 1. 索引结论

L1 继续保持端口协议层定位，只定义 Port / Request / Response / Envelope / Boundary / View / Hint / Report 等协议对象；不实现真实 IO、真实网络、真实模型调用、真实工具调用、真实调度、真实插件宿主或真实权限裁决。

`tiangong_kernel/l1_ports/__init__.py` 采用稳定骨架导出策略：只导出第一阶段公共骨架与通用信封。第 2-8 阶段端口通过子模块显式导入，不在包入口平铺导出，避免公共命名空间污染。

## 2. 分组索引

### 2.1 公共骨架

| 模块 | 顶层类数 | dataclass 数 | 端口类 |
|---|---:|---:|---|
| `base.py` | 7 | 2 | BasePort |
| `envelope.py` | 7 | 6 | 无端口类，仅公共对象/结果对象 |
| `port_boundary.py` | 5 | 4 | 无端口类，仅公共对象/结果对象 |
| `port_error.py` | 4 | 2 | 无端口类，仅公共对象/结果对象 |
| `port_health.py` | 4 | 3 | 无端口类，仅公共对象/结果对象 |
| `port_lifecycle.py` | 4 | 3 | 无端口类，仅公共对象/结果对象 |
| `port_result.py` | 4 | 3 | 无端口类，仅公共对象/结果对象 |

### 2.2 基础设施与资源面

| 模块 | 顶层类数 | dataclass 数 | 端口类 |
|---|---:|---:|---|
| `communication_ports.py` | 18 | 13 | MessagePort、ChannelPort、ProtocolPort、HandoffPort、ConversationPort |
| `content_ports.py` | 19 | 13 | ContentStorePort、ContentReadPort、ContentWriteIntentPort、PayloadPort、ArtifactPort、EvidencePort |
| `environment_ports.py` | 16 | 11 | EnvironmentPort、SandboxPort、LocationResolverPort、RuntimeContextPort、EnvironmentObservationPort |
| `infrastructure_ports.py` | 18 | 13 | ClockPort、IdGeneratorPort、SerializationPort、HashPort、LoggerPort |
| `resource_ports.py` | 16 | 11 | ResourcePort、BudgetPort、QuotaPort、RateLimitPort、ResourceReservationPort |

### 2.3 控制面

| 模块 | 顶层类数 | dataclass 数 | 端口类 |
|---|---:|---:|---|
| `control_boundary_ports.py` | 17 | 12 | BoundaryCheckPort、BoundaryExplainPort、BoundaryAlternativePort、BoundaryViolationRecordPort、ToolReleaseBoundaryPort |
| `decision_ports.py` | 13 | 9 | DecisionReferencePort、DecisionRecordPort、DecisionBoundaryPort、DecisionFeedbackPort |
| `policy_ports.py` | 13 | 9 | PolicyReferencePort、PolicyLookupPort、PolicyBoundaryPort、PolicyExplainPort |
| `risk_ports.py` | 15 | 11 | RiskViewPort、RiskBoundaryPort、RiskExplainPort、RiskEscalationHintPort |
| `schedule_ports.py` | 32 | 24 | ScheduleIntentPort、ScheduleBoundaryPort、TriggerIntentPort、TriggerBoundaryPort、TimerReferencePort、TimerBoundaryPort、CadenceHintPort、DeferredActionHintPort |
| `security_boundary_ports.py` | 36 | 27 | SecretReferencePort、SecretBoundaryPort、CredentialReferencePort、CredentialBoundaryPort、TrustBoundaryPort、PrivacyBoundaryPort、SensitiveContentBoundaryPort、DataExposureBoundaryPort、ExternalDisclosureBoundaryPort |

### 2.4 执行面协议

| 模块 | 顶层类数 | dataclass 数 | 端口类 |
|---|---:|---:|---|
| `action_effect_ports.py` | 40 | 30 | ActionIntentPort、ActionBoundaryPort、EffectReportPort、SideEffectBoundaryPort、TransactionBoundaryPort、TransactionIntentPort、CompensationIntentPort、ChangeRevertHintPort、DeletionIntentPort、DeletionBoundaryPort |
| `model_envelope_ports.py` | 20 | 15 | ModelRequestEnvelopePort、ModelResponseEnvelopePort、ModelToolCallEnvelopePort、ModelObservationEnvelopePort、ModelErrorEnvelopePort |
| `model_ports.py` | 21 | 16 | ModelPort、ModelSessionPort、ModelMessagePort、ModelContextPort、ModelAvailableActionViewPort |
| `skill_ports.py` | 21 | 15 | SkillReferencePort、SkillRegistryPort、SkillQueryPort、SkillExposurePort、SkillFlowPort、SkillBoundaryPort |
| `tool_binding_ports.py` | 15 | 11 | SkillToolBindingPort、ToolGroupBindingPort、ToolDependencyPort、ToolUsageFlowPort |
| `tool_group_ports.py` | 18 | 12 | ToolGroupReferencePort、ToolGroupDescriptionPort、ToolGroupQueryPort、ToolGroupBoundaryPort、ToolGroupLifecyclePort |
| `tool_ports.py` | 20 | 14 | ToolReferencePort、ToolDescriptionPort、ToolInvocationIntentPort、ToolInputBoundaryPort、ToolOutputBoundaryPort、ToolObservationPort |
| `tool_release_ports.py` | 16 | 11 | ToolReleaseIntentPort、ToolReleaseRequestPort、ToolReleaseResultPort、ToolReleaseViewPort、ToolReleaseRevocationPort |

### 2.5 观察面协议

| 模块 | 顶层类数 | dataclass 数 | 端口类 |
|---|---:|---:|---|
| `audit_ports.py` | 10 | 7 | AuditAppendPort、AuditReadPort、EvidenceAttachPort |
| `context_ports.py` | 27 | 21 | ContextReferencePort、ContextWindowPort、ContextAssemblyIntentPort、ContextBoundaryPort、ContextCompressionHintPort、ContextCarryoverPort |
| `event_ports.py` | 13 | 9 | EventAppendPort、EventReadPort、EventStreamPort、EventQueryPort |
| `memory_ports.py` | 29 | 22 | MemoryReferencePort、MemoryWriteIntentPort、MemoryReadIntentPort、MemoryTracePort、MemoryPromotionHintPort、MemoryRetentionBoundaryPort、ForgettingIntentPort |
| `metric_ports.py` | 10 | 7 | MetricRecordPort、MetricReadPort、MetricQueryPort |
| `model_feedback_ports.py` | 20 | 15 | ModelFailureFeedbackPort、ModelCorrectionHintPort、ModelLearningIntentPort、ModelToolNeedFeedbackPort、ModelSkillGapFeedbackPort |
| `model_reflection_ports.py` | 20 | 15 | ModelReflectionPort、ModelSelfReviewPort、ModelOutcomeAssessmentPort、ModelEvolutionHintPort、ModelIterationHintPort |
| `observation_ports.py` | 15 | 11 | ObservationSubmitPort、ObservationReadPort、SignalPort、TelemetryPort |
| `retrieval_ports.py` | 24 | 18 | RetrievalIntentPort、RetrievalQueryPort、RetrievalResultPort、RetrievalEvidencePort、RetrievalBoundaryPort、RetrievalFeedbackPort |

### 2.6 横切治理与演化面

| 模块 | 顶层类数 | dataclass 数 | 端口类 |
|---|---:|---:|---|
| `candidate_ports.py` | 32 | 24 | CandidateReferencePort、CandidateSourcePort、CandidateEvidencePort、CandidateBoundaryPort、CandidateReviewIntentPort、CandidateLifecycleHintPort、CandidatePromotionHintPort、CandidateRejectionHintPort |
| `change_ports.py` | 32 | 24 | ChangeSetIntentPort、ChangeSetBoundaryPort、ChangeImpactHintPort、ChangeReversibilityHintPort、ChangeEvidencePort、ChangeReviewIntentPort、PatchIntentBoundaryPort、ChangeRollbackHintPort |
| `compatibility_migration_ports.py` | 36 | 27 | CompatibilityCheckPort、VersionCompatibilityPort、PortCompatibilityMapPort、MigrationHintPort、MigrationBoundaryPort、DeprecationNoticePort、SchemaMigrationBoundaryPort、BackwardCompatibilityHintPort、ForwardCompatibilityHintPort |
| `component_registry_ports.py` | 40 | 30 | ComponentReferencePort、ComponentBoundaryPort、ComponentLifecycleBoundaryPort、PackageReferencePort、PackageBoundaryPort、RegistryIntentPort、RegistryQueryPort、PluginManifestPort、PluginLifecycleBoundaryPort、PluginIsolationBoundaryPort |
| `evolution_ports.py` | 28 | 21 | EvolutionIntentPort、EvolutionCandidatePort、EvolutionBoundaryPort、EvolutionEvidencePort、EvolutionDecisionHintPort、EvolutionRollbackHintPort、EvolutionContinuityPort |
| `experiment_ports.py` | 28 | 21 | ExperimentIntentPort、ExperimentBoundaryPort、ExperimentDesignHintPort、ExperimentObservationPort、ExperimentResultPort、ExperimentComparisonHintPort、ExperimentRollbackHintPort |
| `learning_ports.py` | 24 | 18 | LearningIntentPort、LearningTaskPort、LearningEvidencePort、LearningResultPort、LearningBoundaryPort、LearningFeedbackPort |
| `self_iteration_ports.py` | 24 | 18 | IterationCandidatePort、IterationPatchIntentPort、IterationReviewPort、IterationRollbackHintPort、IterationEvidencePort、IterationBoundaryPort |
| `self_learning_ports.py` | 24 | 18 | SelfLearningCandidatePort、KnowledgeIngestionIntentPort、SkillLearningHintPort、SelfLearningEvidencePort、SelfLearningReviewPort、SelfLearningBoundaryPort |
| `skill_evolution_ports.py` | 16 | 12 | SkillEvolutionHintPort、SkillIterationHintPort、SkillVersionHintPort、SkillCorrectionHintPort |
| `state_continuity_ports.py` | 36 | 27 | SnapshotReferencePort、SnapshotIntentPort、CheckpointReferencePort、CheckpointIntentPort、RestorePointReferencePort、RecoveryPointPort、StateContinuityBoundaryPort、StateRecoveryHintPort、ContinuityEvidencePort |
| `tool_gap_ports.py` | 17 | 13 | SkillGapReportPort、ToolNeedReportPort、ToolGroupGapReportPort、ToolGapBoundaryPort |
| `validation_ports.py` | 43 | 30 | ValidationReferencePort、ValidationRequestPort、VerificationPort、TestReferencePort、TestPlanIntentPort、QualityBoundaryPort、CandidateValidationPort、LearningTestPort、IterationVerificationPort、EvolutionValidationPort、RollbackVerificationPort、RestoreVerificationPort、CandidatePromotionHintPort |

## 3. 命名与动词口径

- `describe_*`：只返回边界说明、声明性描述或静态上下文，不启动真实能力。
- `request_*`：提交请求型意图，后续层可选择是否编排，但 L1 不处理执行。
- `submit_*`：提交观察、证据、反馈、提示或候选意图，L1 仅定义传递形状。
- `declare_*`：声明静态边界、上下文、健康、生命周期或约束，不产生真实副作用。
- `reference_*`：表达引用对象，不创建真实资源或候选池。

## 4. 候选、验证、变更、实验的层级关系

```text
CandidateSource / CandidateReference
  → CandidateEvidence / ChangeEvidence / ExperimentObservation
  → Validation / Verification / LearningTest / IterationVerification / EvolutionValidation
  → CandidatePromotionHint / CandidateRejectionHint / RollbackHint
```

其中 `validation_ports.py` 的 `CandidatePromotionHint*` 偏验证链输出提示；`candidate_ports.py` 的 `CandidatePromotionHint*` 偏统一候选生命周期提示。两者保留跨模块同名，但不得在同一模块重复定义。

## 5. L0 Ref 使用策略

候选相关对象继续使用 L0 `ResourceRef` 作为候选主引用；当前 L0 不新增 `CandidateRef`。后续若 L0/L1 冻结后仍需候选专用引用，应作为独立演化候选处理，不能在 L1 稳定性整修中临时造新 Ref。

组件注册继续使用 `ComponentRef`、`PackageRef`、`SandboxRef` 等 L0 专用引用；状态连续性继续使用 `RuntimeStateRef` 表达运行状态引用。`RuntimeContext` 与 `RuntimeStateRef` 只表示运行上下文和状态引用，不是旧 Runtime 主循环，也不是新版核心对象。

## 6. 旧体系边界

本索引不恢复 CapabilityPort、AbilityPackagePort、AbilityPackage、AbilityRouter、AbilityExecutor 或旧 Runtime 主循环。Skill 是大模型行动入口；Skill 选中后经后续层边界释放 ToolGroup 视图，ToolGroup 不是旧能力包。
