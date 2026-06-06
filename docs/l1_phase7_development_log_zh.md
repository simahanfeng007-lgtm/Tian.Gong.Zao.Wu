# 天工造物 L1 第七阶段开发日志

## 1. 本阶段目标

本阶段只开发 L1 第七阶段：记忆、上下文、检索、自我学习、自我迭代、自我进化端口协议。

本阶段目标是为工程生命体提供协议入口：

- 记忆：只表达记忆引用、写入意图、读取意图、轨迹、晋升提示、保留边界和遗忘意图。
- 上下文：只表达上下文引用、窗口、组装意图、边界、压缩提示和延续关系。
- 检索：只表达检索意图、查询、结果、证据、边界和反馈。
- 学习：只表达学习意图、学习任务候选、学习证据、学习结果引用、学习边界和学习反馈。
- 自我学习：只表达自学候选、知识摄入意图、Skill 学习提示、自学证据、自学复核和自学边界。
- 自我迭代：只表达迭代候选、补丁意图、迭代复核、回滚提示、迭代证据和迭代边界。
- 自我进化：只表达进化意图、进化候选、进化边界、进化证据、进化决策提示、进化回滚提示和连续性协议。

本阶段不实现真实记忆、真实上下文拼接、真实检索、真实学习、真实自我迭代、真实自我进化、真实代码修改、真实 Skill 修改、真实工具生产、真实合入、真实回滚、真实模型调用、真实工具调用或插件宿主。

## 2. 前置检查与 P1 命名补丁

进入第七阶段前已确认第一至第六阶段核心端口模块存在并可导入，尤其：

- `tiangong_kernel/l1_ports/skill_evolution_ports.py`
- `tiangong_kernel/l1_ports/tool_gap_ports.py`
- `tiangong_kernel/l1_ports/model_ports.py`
- `tiangong_kernel/l1_ports/model_envelope_ports.py`
- `tiangong_kernel/l1_ports/model_feedback_ports.py`
- `tiangong_kernel/l1_ports/model_reflection_ports.py`

第七阶段提示词要求存在 `docs/l1_phase5_hotfix1_report_zh.txt`。当前第 1-5 阶段补丁交接包已存在 `docs/l1_phase5_patch_handoff_report_zh.txt`，但缺少 hotfix1 命名文件。该问题属于 P1 前置命名缺口，因此本阶段先补充：

- `docs/l1_phase5_hotfix1_report_zh.txt`

该文件仅为文档命名补齐，不修改 L0，不引入真实能力。

同时，第七阶段提示词在第五阶段衔接口径中列出 ToolFunctionMismatchReport；当前补丁基线的 tool_gap_ports.py 未提供该对象。为避免第七阶段重复发明工具功能不匹配语义，本阶段将其作为 P1 前置兼容补丁补入 tool_gap_ports.py，仅作为冻结 dataclass 报告对象，不新增端口、不生产工具、不修改工具组、不触发真实学习或迭代。

## 3. 新增文件清单

新增源码文件：

- `tiangong_kernel/l1_ports/memory_ports.py`
- `tiangong_kernel/l1_ports/context_ports.py`
- `tiangong_kernel/l1_ports/retrieval_ports.py`
- `tiangong_kernel/l1_ports/learning_ports.py`
- `tiangong_kernel/l1_ports/self_learning_ports.py`
- `tiangong_kernel/l1_ports/self_iteration_ports.py`
- `tiangong_kernel/l1_ports/evolution_ports.py`

兼容补充：

- `tiangong_kernel/l1_ports/tool_gap_ports.py`：P1 兼容补充 `ToolFunctionMismatchReport`，只作为工具功能不匹配报告对象。

新增测试文件：

- `tests/test_l1_phase7_memory_ports.py`
- `tests/test_l1_phase7_context_ports.py`
- `tests/test_l1_phase7_retrieval_ports.py`
- `tests/test_l1_phase7_learning_ports.py`
- `tests/test_l1_phase7_self_learning_ports.py`
- `tests/test_l1_phase7_self_iteration_ports.py`
- `tests/test_l1_phase7_evolution_ports.py`

新增文档文件：

- `docs/l1_phase5_hotfix1_report_zh.txt`
- `docs/l1_phase7_development_log_zh.md`
- `docs/l1_phase7_handoff_report_zh.txt`

## 4. 新增端口清单

记忆端口：

- `MemoryReferencePort`
- `MemoryWriteIntentPort`
- `MemoryReadIntentPort`
- `MemoryTracePort`
- `MemoryPromotionHintPort`
- `MemoryRetentionBoundaryPort`
- `ForgettingIntentPort`

上下文端口：

- `ContextReferencePort`
- `ContextWindowPort`
- `ContextAssemblyIntentPort`
- `ContextBoundaryPort`
- `ContextCompressionHintPort`
- `ContextCarryoverPort`

检索端口：

- `RetrievalIntentPort`
- `RetrievalQueryPort`
- `RetrievalResultPort`
- `RetrievalEvidencePort`
- `RetrievalBoundaryPort`
- `RetrievalFeedbackPort`

学习端口：

- `LearningIntentPort`
- `LearningTaskPort`
- `LearningEvidencePort`
- `LearningResultPort`
- `LearningBoundaryPort`
- `LearningFeedbackPort`

自我学习端口：

- `SelfLearningCandidatePort`
- `KnowledgeIngestionIntentPort`
- `SkillLearningHintPort`
- `SelfLearningEvidencePort`
- `SelfLearningReviewPort`
- `SelfLearningBoundaryPort`

自我迭代端口：

- `IterationCandidatePort`
- `IterationPatchIntentPort`
- `IterationReviewPort`
- `IterationRollbackHintPort`
- `IterationEvidencePort`
- `IterationBoundaryPort`

自我进化端口：

- `EvolutionIntentPort`
- `EvolutionCandidatePort`
- `EvolutionBoundaryPort`
- `EvolutionEvidencePort`
- `EvolutionDecisionHintPort`
- `EvolutionRollbackHintPort`
- `EvolutionContinuityPort`

合计新增 44 个第七阶段抽象端口。

## 5. 每个端口职责与明确不做事项

### 5.1 记忆端口

- `MemoryReferencePort`：定义记忆事实引用协议；不保存记忆、不读取记忆、不建立记忆库。
- `MemoryWriteIntentPort`：定义写入记忆候选协议；不写入、不晋升、不修改长期记忆。
- `MemoryReadIntentPort`：定义读取记忆候选请求协议；不读取、不召回、不排序真实记忆。
- `MemoryTracePort`：定义记忆与事件、观察、信号、证据之间的轨迹绑定协议；不落盘、不索引、不折叠历史。
- `MemoryPromotionHintPort`：定义记忆晋升候选提示协议；不计算评分、不晋升、不改写记忆层级。
- `MemoryRetentionBoundaryPort`：定义记忆保留和忘却边界协议；不执行删除、不执行遗忘算法、不清理数据。
- `ForgettingIntentPort`：定义遗忘、抑制或剪枝候选协议；不删除真实数据、不清空记忆、不执行物理瘦身。

### 5.2 上下文端口

- `ContextReferencePort`：定义上下文引用协议；不读取上下文、不保存内容、不拼接模型输入。
- `ContextWindowPort`：定义上下文窗口和容量边界协议；不计算真实 token、不截断、不压缩。
- `ContextAssemblyIntentPort`：定义上下文组装候选协议；不拼接提示词、不调用模型、不读取记忆。
- `ContextBoundaryPort`：定义上下文可见、可引用、可使用边界协议；不做真实裁决、不过滤真实内容、不授予访问。
- `ContextCompressionHintPort`：定义上下文压缩或摘要候选提示协议；不压缩、不总结、不改写上下文。
- `ContextCarryoverPort`：定义跨轮、跨 Run、跨 Skill 的上下文延续协议；不持久化会话、不拼接历史、不保存消息内容。

### 5.3 检索端口

- `RetrievalIntentPort`：定义检索需求候选协议；不执行检索、不访问索引、不读取内容。
- `RetrievalQueryPort`：定义检索查询结构协议；不连接数据库、不联网、不搜索文件系统。
- `RetrievalResultPort`：定义检索结果引用协议；不生成真实结果、不排序、不聚合。
- `RetrievalEvidencePort`：定义检索结果与证据引用绑定协议；不复制证据、不上传证据、不读取证据内容。
- `RetrievalBoundaryPort`：定义检索边界、策略引用和风险视图说明协议；不做真实权限裁决、不过滤真实数据。
- `RetrievalFeedbackPort`：定义检索质量、缺口和证据不足反馈协议；不训练模型、不更新索引、不改写查询算法。

### 5.4 学习端口

- `LearningIntentPort`：定义学习意图提交协议；不执行学习、不读取资料、不写知识库。
- `LearningTaskPort`：定义学习任务候选协议；不读取资料、不生成知识、不生成 Skill。
- `LearningEvidencePort`：定义学习证据引用协议；不抓取资料、不生成证据、不写库。
- `LearningResultPort`：定义学习结果引用协议；不写知识库、不合入 Skill、不生产工具。
- `LearningBoundaryPort`：定义学习候选边界协议；不做真实裁决、不启动学习、不提升权限。
- `LearningFeedbackPort`：定义学习质量反馈协议；不更新模型、不更新 Skill、不重写学习结果。

### 5.5 自我学习端口

- `SelfLearningCandidatePort`：定义自学候选提交协议；不启动自学流程、不读资料、不写知识库。
- `KnowledgeIngestionIntentPort`：定义知识摄入候选意图协议；不摄入知识、不写数据库、不生成知识对象。
- `SkillLearningHintPort`：定义 Skill 学习补强提示协议；不修改 Skill、不生成版本、不合入知识。
- `SelfLearningEvidencePort`：定义自学候选证据引用协议；不生成证据、不复制证据、不写证据库。
- `SelfLearningReviewPort`：定义自学候选复核请求协议；不真实复核、不批准、不拒绝、不合入。
- `SelfLearningBoundaryPort`：定义自学候选边界协议；不绕过边界、不触发真实学习、不提升权限。

### 5.6 自我迭代端口

- `IterationCandidatePort`：定义自我迭代候选提交协议；不生成补丁、不修改文件、不合入代码。
- `IterationPatchIntentPort`：定义补丁或修订意图协议；不生成 patch、不改源码、不写文件。
- `IterationReviewPort`：定义迭代候选复核请求协议；不真实审核、不批准、不拒绝、不合入。
- `IterationRollbackHintPort`：定义迭代失败时可能需要回退的提示协议；不执行回滚、不恢复文件、不修改版本。
- `IterationEvidencePort`：定义迭代候选证据引用协议；不生成测试报告、不写审计库、不执行验证。
- `IterationBoundaryPort`：定义迭代候选边界说明协议；不绕过边界、不提升权限、不直接修改系统。

### 5.7 自我进化端口

- `EvolutionIntentPort`：定义长期结构调整意图提交协议；不执行进化、不修改架构、不生成候选变更。
- `EvolutionCandidatePort`：定义进化候选提交协议；不改架构、不生成插件、不生产工具、不改代码。
- `EvolutionBoundaryPort`：定义进化候选边界、策略和风险说明协议；不做真实裁决、不放行候选、不提升权限。
- `EvolutionEvidencePort`：定义进化候选证据引用协议；不生成证据、不写审计库、不执行测试。
- `EvolutionDecisionHintPort`：定义进化候选决策提示协议；不做真实决策、不合入候选、不触发执行。
- `EvolutionRollbackHintPort`：定义进化候选失败时的回退提示协议；不执行回滚、不恢复文件、不修改版本。
- `EvolutionContinuityPort`：定义进化前后主链连续性和边界不污染协议；不执行迁移、不验证真实连续性、不修改结构。

## 6. 与 L0 的依赖关系

本阶段继续复用 L0 引用和值对象，包括但不限于：

- `MemoryRef`、`MemoryTraceRef`、`MemoryRetentionRef`
- `ContextRef`、`ContextWindow`、`ContextBoundary`
- `RetrievalRef`、`QueryRef`、`RetrievalResultRef`、`RetrievalEvidenceRef`
- `LearningRef`、`ExperienceRef`、`LessonRef`、`ImprovementProposalRef`、`EvolutionRef`
- `EvidenceRef`、`AuditRef`、`ObservationRef`、`SignalRef`
- `SkillRef`、`ToolRef`、`ResourceRef`、`PolicyRef`、`RiskView`
- `ValidationRef`、`VerificationRef`、`TestRef`、`VersionRef`、`SchemaRef`

未修改 L0，未向 L0 添加新引用对象。

## 7. 与 L1 第一至第六阶段骨架的关系

本阶段保持第一至第六阶段既有端口边界，不重构既有公共骨架：

- 继续使用 `PortResult` 作为端口返回包装。
- 继续使用 `PortBoundary`、`BoundaryViolation`、`PortBoundaryContext` 表达边界信息。
- 继续使用 `CommandEnvelope`、`QueryEnvelope` 表达请求或查询信封。
- 继续承接第五阶段的 Skill / ToolGroup 缺口对象。
- 继续承接第六阶段的模型反馈和模型反思对象。

## 8. 与第五阶段 Skill / ToolGroup 缺口接口的衔接

第七阶段没有重新发明 Skill / ToolGroup 缺口语义，而是复用：

- `SkillGapReport`
- `ToolNeedReport`
- `ToolGroupGapReport`
- `SkillEvolutionHint`
- `SkillIterationHint`
- `SkillCorrectionHint`

这些对象在第七阶段进入学习候选、自学候选、迭代候选和进化候选，但不直接触发真实 Skill 修改或工具生产。

## 9. 与第六阶段模型反馈 / 模型反思接口的衔接

第七阶段复用第六阶段对象：

- `ModelLearningIntent`
- `ModelFailureFeedback`
- `ModelCorrectionHint`
- `ModelSkillGapFeedback`
- `ModelToolNeedFeedback`
- `ModelReflection`
- `ModelOutcomeAssessment`
- `ModelEvolutionHint`
- `ModelIterationHint`

这些对象是学习、迭代、进化候选的来源证据之一。第七阶段不执行模型反馈提出的动作，只把它们变为后续可验证候选。

## 10. 面向 L2-L6 的前瞻引用说明

- L2 可将记忆、上下文、检索、学习、迭代、进化候选作为生命体状态事实记录。
- L3 可编排候选进入验证、复核、边界检查和后续流程。
- L4 可实现真实外部适配器，但 L1 不持有任何真实资源。
- L5 可隔离插件对记忆、检索、学习、迭代、进化端口的访问范围。
- L6 子系统插件可提交候选与证据，但不能绕过主链和边界层。

## 11. 为什么本阶段只做候选 / 意图 / 证据，不做真实学习、迭代、进化

第七阶段是协议入口层，不是执行层。真实学习、真实迭代、真实进化会触及文件、知识库、Skill 版本、工具生产、系统结构和回滚能力，必须由后续层经过验证、复核、边界和回滚协议后处理。

本阶段只把事实变成：

- 意图
- 候选
- 证据
- 反馈
- 边界说明
- 回退提示
- 连续性声明

这些对象不会直接改变系统。

## 12. 为什么自我学习、自我迭代、自我进化不能绕过大模型主控、Skill 直显、工具组释放和边界层

新版主链要求大模型先看到 Skill，再选择 Skill，再在边界检查后释放工具组。自我学习、自我迭代和自我进化只是主链运行后的反馈入口，不能脱离大模型主控，也不能绕过边界层直接修改 Skill、工具、代码或架构。

因此第七阶段所有端口都只表达候选事实：

- 学习候选不能直接变成知识库写入。
- 迭代候选不能直接变成补丁或合入。
- 进化候选不能直接变成架构变更。
- 回滚提示不能直接执行回滚。

## 13. 禁止事项检查

已检查并通过：

- 无 L2-L6 import。
- 无第三方库 import。
- 无真实 IO、网络、进程、后台任务调用。
- 无真实记忆、真实上下文拼接、真实检索。
- 无真实学习、真实迭代、真实进化。
- 无真实代码修改、真实合入、真实回滚。
- 无真实模型调用、真实工具调用、真实插件加载。
- 第七阶段未实现第八阶段验证、晋升、回滚验证协议。
- 未出现旧链路核心对象作为 L1 第七阶段主链。

## 14. 测试命令

已运行：

```bash
python3 -m compileall -q tiangong_kernel tests
```

已运行：

```bash
python3 -m pytest -q tests
```

全量结果：

```text
272 passed in 4.48s
```

已单独运行或分组补跑：

```bash
python3 -m pytest -q tests/test_l1_no_l2_imports.py
python3 -m pytest -q tests/test_l1_no_third_party_imports.py
python3 -m pytest -q tests/test_l1_no_real_io.py
python3 -m pytest -q tests/test_l1_ports_are_abstract.py tests/test_l1_ports_return_core_result.py tests/test_l1_uses_l0_primitives.py tests/test_l1_no_execution_keywords.py tests/test_l1_chinese_docstrings.py
python3 -m pytest -q tests/test_l1_phase7_memory_ports.py tests/test_l1_phase7_context_ports.py tests/test_l1_phase7_retrieval_ports.py tests/test_l1_phase7_learning_ports.py tests/test_l1_phase7_self_learning_ports.py tests/test_l1_phase7_self_iteration_ports.py tests/test_l1_phase7_evolution_ports.py
```

补充说明：一次串行单项测试循环命令曾被容器超时截断；随后必测项已合并补跑为 `9 passed in 2.12s`，第七阶段专项测试已合并补跑为 `35 passed in 1.92s`。最终不存在未运行测试。

## 15. 测试结果

- `compileall`：通过。
- 全量 `pytest`：`272 passed in 4.48s`。
- 第七阶段专项测试：7 个文件均单独运行通过，每个 5 passed，合计 35 passed；合并专项重跑结果为 35 passed in 1.92s。
- 必测静态项补跑：全部通过。
- 第七阶段 38 个 L1 模块导入检查通过。
- L0 对比检查：与第六阶段输入包相比，排除缓存后无差异。

## 16. 未做事项

按阶段边界未做：

- 未开发第八阶段。
- 未实现 ValidationPort / VerificationPort / TestPort。
- 未实现 SchedulePort / TriggerPort / TimerPort。
- 未实现 CandidatePromotionPort。
- 未实现 EvolutionValidationPort / IterationVerificationPort / LearningTestPort / RollbackVerificationPort。
- 未实现真实状态机、真实运行循环、真实调度器。
- 未实现真实验证执行、真实测试执行、真实候选晋升、真实合入、真实回滚。
- 未实现真实记忆库、真实上下文拼接、真实检索、真实学习、真实自我迭代、真实自我进化。
- 未实现真实模型调用、真实工具调用、真实插件加载。

## 17. 是否允许进入 L1 第八阶段

建议允许进入 L1 第八阶段。

理由：第七阶段源码、专项测试、开发日志、交接报告和完整交接 zip 均已完成；全量测试通过；L0 未修改；第一至第六阶段测试未回退；第八阶段内容未提前实现。
