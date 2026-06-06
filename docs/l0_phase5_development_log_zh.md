# 天工造物新版 L0 零依赖原语层 第五阶段开发日志

## 本阶段目标

本阶段只落地 L0 第五阶段“生命系统底层”事实语言，新增 memory、forgetting、context、learning、health 五个模块。目标是定义可稳定序列化、可稳定哈希、可审计、可引用的生命系统底层事实对象，不实现任何上层系统流程、算法、执行器或真实副作用。

## 新增模块清单

- `tiangong_kernel/l0_primitives/memory.py`
- `tiangong_kernel/l0_primitives/forgetting.py`
- `tiangong_kernel/l0_primitives/context.py`
- `tiangong_kernel/l0_primitives/learning.py`
- `tiangong_kernel/l0_primitives/health.py`

## 每个模块新增对象清单

### memory.py

- `MemoryRef`
- `MemoryTraceRef`
- `MemoryKind`
- `MemoryState`
- `MemoryOriginRef`
- `MemoryConfidence`
- `MemoryRetentionRef`

### forgetting.py

- `ForgettingRef`
- `RetentionTrace`
- `DecayTrace`
- `InterferenceTrace`
- `SuppressionRef`
- `PruningRef`
- `RevisionRef`
- `ForgettingKind`
- `ForgettingState`
- `RetentionScore`
- `DecayRate`

### context.py

- `ContextRef`
- `ContextKind`
- `ContextWindow`
- `ContextBoundary`
- `ContextDigest`
- `ContextOriginRef`
- `BeliefStateRef`
- `WorldStateRef`

### learning.py

- `LearningRef`
- `LearningKind`
- `LearningState`
- `AdaptationRef`
- `AdaptationKind`
- `AdaptationState`
- `EvolutionRef`
- `EvolutionKind`
- `EvolutionState`
- `ImprovementProposalRef`
- `ImprovementAssessmentRef`
- `EvolutionCommitRef`
- `EvolutionRollbackRef`
- `ExperienceRef`
- `LessonRef`

### health.py

- `HealthRef`
- `HealthState`
- `HealthSignalRef`
- `VitalityRef`
- `VitalityKind`
- `VitalityState`
- `HomeostasisRef`
- `HomeostasisState`
- `StabilityRange`
- `StabilityDeviationRef`
- `StressRef`
- `DamageRef`
- `RecoveryHealthRef`

## 关键设计取舍

1. **只定义事实语言，不定义系统实现**：本阶段所有对象均保持为不可变值对象或引用对象，不保存完整记忆、完整上下文、完整健康指标流，也不执行任何流程。
2. **Ref 类只承载引用事实**：所有 `*Ref` 类仅包含 `RefId`、`TypedRef`、枚举、值对象、证据引用、schema_version 等字段，不承载执行器、客户端、回调函数、真实资源句柄或可变对象。
3. **生命底层对象保持可审计与可哈希**：所有新增对象均可通过 `stable_json_dumps` 生成 Canonical JSON，并可通过 `stable_hash` 生成稳定摘要。
4. **中文说明补强**：每个新增模块顶部写入中文模块说明；核心 dataclass 和 Enum 均补充中文 docstring，说明中文名称、作用、L0 边界和不能承担的上层职责。
5. **避免 L0 过早膨胀**：未实现召回、遗忘、上下文装配、学习、演化、健康评分、自愈触发等逻辑，只保留后续 L2/L3/L6 可使用的事实原语。

## 明确未做事项

- 未做第六阶段或后续模块。
- 未实现记忆召回、记忆存储、记忆索引、记忆巩固或遗忘算法。
- 未实现上下文装配、压缩、选择、污染检测或模型输入拼接。
- 未实现学习算法、偏好学习、工具生成、技能生成、代码修改或自动合并。
- 未实现健康评分、监控采集、自愈触发、降级触发、恢复触发或自治等级调整。
- 未写 Runtime、工具执行、插件宿主、模型客户端、记忆系统、遗忘系统、自愈系统、健康监控或策略引擎。

## 测试命令

```bash
python -m compileall -q tiangong_kernel tests
python -m pytest -q tests
```

## 测试结果

```text
69 passed in 0.50s
```

## 失败测试说明

无失败测试。

## 下一步建议

下一阶段仅在用户明确要求时继续做第六阶段：`trust.py`、`privacy.py`、`secret.py`、`contract.py`、`policy.py`、`instruction.py`、`autonomy.py`、`value.py`。继续保持 L0 只定义事实语言，不实现策略引擎、权限算法、真实密钥处理或自治控制流程。
