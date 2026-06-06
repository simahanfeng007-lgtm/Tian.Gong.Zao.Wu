# 天工造物 L2 第七阶段开发日志

生成日期：2026-06-03

## 一、阶段目标

本阶段开发 L2 状态层第七阶段：候选、变更、迭代、进化、实验、验证、恢复状态。

本阶段仍然坚持 L2 定位：只记录状态事实，不执行真实学习、真实迭代、真实进化、真实实验、真实验证、真实回退、真实恢复、真实代码修改、真实 Skill 修改、真实工具生产、真实模型调用或真实工具调用。

## 二、前置检查

已使用上一阶段交付包作为输入基线：`天工造物_L2_第六阶段_记忆上下文检索学习状态_交付包_20260603.zip`。

确认第六阶段 handoff 与 todo 中明确第七阶段应开发：候选、变更、迭代、进化、实验、验证、恢复状态。

说明：本轮用户同时上传了一个 `L1第七阶段开发提示词` 文件，该文件属于 L1 端口协议层，不是 L2 状态层提示词。因此本阶段没有把 L1 提示词错用为 L2 指令，只把它作为错层风险提示处理。实际开发范围以当前 L2 第六阶段交付链路为准。

## 三、新增源码文件

- `tiangong_kernel/l2_state/candidate_state.py`
- `tiangong_kernel/l2_state/change_state.py`
- `tiangong_kernel/l2_state/iteration_state.py`
- `tiangong_kernel/l2_state/evolution_state.py`
- `tiangong_kernel/l2_state/experiment_state.py`
- `tiangong_kernel/l2_state/validation_state.py`
- `tiangong_kernel/l2_state/recovery_state.py`

## 四、修改源码文件

- `tiangong_kernel/l2_state/state_identity.py`
  - 新增 `L2StateKind.EXPERIMENT`，使实验状态不再挤占候选或验证类别。
- `tiangong_kernel/l2_state/__init__.py`
  - 导出第七阶段新增枚举与状态对象。
  - 保留第一至第六阶段既有导出。

## 五、新增测试文件

- `tests/test_l2_phase7_candidate_change_iteration_evolution_state.py`
- `tests/test_l2_phase7_experiment_validation_recovery_state.py`
- `tests/test_l2_phase7_boundary_no_execution.py`
- `tests/test_l2_phase7_state_serialization_and_integration.py`

## 六、新增状态对象清单

### candidate_state.py

- `CandidateKind`
- `CandidateSourceKind`
- `CandidateLifecycleStatus`
- `CandidateBoundaryStatus`
- `CandidateRefState`
- `CandidateSourceState`
- `CandidateEvidenceState`
- `CandidateBoundaryState`
- `CandidateLifecycleState`

职责：记录统一候选引用、候选来源、候选证据、候选边界和候选生命周期事实。

明确不做：不创建候选池，不执行候选晋升，不批准合入，不修改 Skill、工具、代码或架构。

### change_state.py

- `ChangeKind`
- `ChangeImpactStatus`
- `ChangeReversibilityStatus`
- `ChangeReviewStatus`
- `ChangeIntentState`
- `ChangeImpactState`
- `ChangeReversibilityState`
- `ChangePatchRefState`
- `ChangeReviewState`

职责：记录变更意图、影响、可逆性、补丁引用和复核事实。

明确不做：不生成补丁，不修改文件，不合入代码，不执行迁移，不执行回退。

### iteration_state.py

- `IterationTargetKind`
- `IterationCandidateStatus`
- `IterationReviewStatus`
- `IterationCandidateState`
- `IterationPatchIntentState`
- `IterationEvidenceState`
- `IterationReviewState`
- `IterationRollbackHintState`

职责：记录自我迭代候选、补丁意图、证据、复核和回退提示事实。

明确不做：不生成 patch，不写源码，不修改 Skill，不合入迭代，不执行回退。

### evolution_state.py

- `EvolutionIntentKind`
- `EvolutionCandidateStatus`
- `EvolutionBoundaryLabel`
- `EvolutionContinuityStatus`
- `EvolutionIntentState`
- `EvolutionCandidateState`
- `EvolutionBoundaryState`
- `EvolutionEvidenceState`
- `EvolutionDecisionHintState`
- `EvolutionRollbackHintState`
- `EvolutionContinuityState`

职责：记录进化意图、进化候选、边界、证据、决策提示、回退提示和连续性事实。

明确不做：不修改架构，不生成插件，不生产工具，不改代码，不合入进化，不执行回退。

### experiment_state.py

- `ExperimentKind`
- `ExperimentStatus`
- `ExperimentComparisonStatus`
- `ExperimentIntentState`
- `ExperimentDesignState`
- `ExperimentObservationState`
- `ExperimentResultState`
- `ExperimentComparisonState`
- `ExperimentRollbackHintState`

职责：记录实验意图、实验设计、实验观察、实验结果、实验对比和回退提示事实。

明确不做：不运行实验，不调用模型或工具，不计算结果，不执行回退或迁移。

### validation_state.py

- `ValidationIntentKind`
- `ValidationReadinessStatus`
- `ValidationOutcomeRefStatus`
- `ValidationIntentState`
- `ValidationRefState`
- `VerificationRefState`
- `TestPlanRefState`
- `CandidateValidationState`
- `RecoveryValidationState`

职责：记录验证意图、验证引用、规格验证引用、测试计划引用、候选验证和恢复验证事实。

明确不做：不运行测试，不计算验证结果，不晋升候选，不执行恢复。

### recovery_state.py

- `RecoveryAnchorKind`
- `RecoveryReadinessStatus`
- `RecoveryOutcomeStatus`
- `RecoveryAnchorState`
- `RollbackHintState`
- `RecoveryReadinessState`
- `RecoveryOutcomeRefState`
- `RecoveryLinkState`

职责：记录恢复锚点、回退提示、恢复准备、恢复结果引用和恢复链路事实。

明确不做：不执行回退，不恢复文件，不读取快照，不修改状态库，不启动恢复流程。

## 七、与 L0 的依赖关系

本阶段继续复用 L0 的 `TypedRef`、`RefId`、`StateSnapshotRef` 等引用事实。第七阶段新增对象不新建 L0 身份体系，不读取真实资源，不连接外部系统。

## 八、与 L1 / L2 前六阶段关系

- L1 提供候选、学习、迭代、进化、实验、验证、恢复等协议入口。
- L2 第七阶段只把这些协议在状态层表示为可序列化、可快照、可引用的状态事实。
- 第六阶段提供 `MemoryRefState`、`ContextWindowState`、`RetrievalResultRefState`、`LearningSignalState` 等状态，本阶段新增候选可引用这些状态。
- 第七阶段新增对象可被后续 L3-L6 编排、验证、执行或插件层解释，但本阶段不承担执行职责。

## 九、为什么本阶段只做状态事实

学习、迭代、进化、实验、验证和恢复都可能影响系统结构、代码、Skill、工具组、边界和用户资产。若在 L2 状态层直接执行，会污染层级边界，并绕过后续验证、复核、回退和审计链。因此本阶段所有对象都保持：

- 候选化
- 引用化
- 证据化
- 边界化
- 可恢复化
- 不执行化

## 十、禁止事项检查

已检查：

- 未引入 L3-L6 import。
- 未引入第三方库。
- 未引入真实 IO、网络、数据库、进程、线程或后台任务。
- 未实现真实候选池、真实变更、真实迭代、真实进化、真实实验、真实验证、真实恢复。
- 未调用模型。
- 未调用工具。
- 未恢复旧能力包体系。
- 未引入 CapabilityPort / AbilityPackagePort / AbilityRouter / PluginHost / ToolExecutor / ModelExecutor 等旧核心。
- 未修改 L0。
- 未修改 L1。

## 十一、测试命令与结果

实际运行：

```bash
python3 -m compileall -q tiangong_kernel tests
python3 -m pytest -q tests/test_l2_phase7_*.py
python3 -m pytest -q tests/test_l2_phase1_*.py tests/test_l2_phase2_*.py tests/test_l2_phase3_*.py tests/test_l2_phase4_*.py tests/test_l2_phase5_*.py tests/test_l2_phase6_*.py tests/test_l2_phase7_*.py
python3 -m pytest -q
```

实际结果：

- compileall：通过。
- 第七阶段专项测试：`13 passed`。
- L2 第 1-7 阶段回归：`133 passed`。
- 完整 pytest：`459 passed`。

## 十二、未做事项

- 未开发 L2 第八阶段组件、兼容迁移、状态投影、总收口。
- 未实现真实候选池。
- 未实现真实变更或 patch 生成。
- 未实现真实实验、测试、验证、回退或恢复。
- 未实现真实学习、迭代、进化。
- 未实现模型调用、工具调用、调度器、运行循环、插件宿主或存储层。

## 十三、是否建议进入第八阶段

建议进入 L2 第八阶段。

理由：第七阶段源码、测试、日志、报告和交接包已完成；第七阶段专项测试通过；L2 第 1-7 阶段回归通过；完整 pytest 通过；L0/L1 未修改；第八阶段内容未提前实现。
