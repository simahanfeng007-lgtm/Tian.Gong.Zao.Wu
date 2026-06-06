# 天工造物新版 L1 端口协议层第六阶段开发日志

## 1. 本阶段目标

本阶段目标是建立 L1 的模型抽象端口与模型信封协议，包括：

1. ModelPort 模型抽象端口。
2. 模型会话、模型消息、模型上下文、模型可见行动视图协议。
3. 模型请求、响应、工具调用意图、观察回传、错误回传信封协议。
4. 模型失败反馈、修正提示、学习意图、工具需求反馈、Skill 缺口反馈协议。
5. 模型任务反思、自评、结果评估、进化提示、迭代提示协议。

本阶段只定义协议，不实现真实模型调用、真实模型会话、真实工具调用、真实 Skill 执行、真实工具释放、真实学习、真实自我迭代、真实自我进化或插件宿主。

## 2. 新增文件清单

新增源码文件：

- `tiangong_kernel/l1_ports/model_ports.py`
- `tiangong_kernel/l1_ports/model_envelope_ports.py`
- `tiangong_kernel/l1_ports/model_feedback_ports.py`
- `tiangong_kernel/l1_ports/model_reflection_ports.py`

新增测试文件：

- `tests/test_l1_phase6_model_ports.py`
- `tests/test_l1_phase6_model_envelope_ports.py`
- `tests/test_l1_phase6_model_feedback_ports.py`
- `tests/test_l1_phase6_model_reflection_ports.py`

新增文档文件：

- `docs/l1_phase6_development_log_zh.md`
- `docs/l1_phase6_handoff_report_zh.txt`

## 3. 新增端口清单

### 3.1 模型抽象端口

- `ModelPort`
- `ModelSessionPort`
- `ModelMessagePort`
- `ModelContextPort`
- `ModelAvailableActionViewPort`

### 3.2 模型信封端口

- `ModelRequestEnvelopePort`
- `ModelResponseEnvelopePort`
- `ModelToolCallEnvelopePort`
- `ModelObservationEnvelopePort`
- `ModelErrorEnvelopePort`

### 3.3 模型反馈端口

- `ModelFailureFeedbackPort`
- `ModelCorrectionHintPort`
- `ModelLearningIntentPort`
- `ModelToolNeedFeedbackPort`
- `ModelSkillGapFeedbackPort`

### 3.4 模型反思端口

- `ModelReflectionPort`
- `ModelSelfReviewPort`
- `ModelOutcomeAssessmentPort`
- `ModelEvolutionHintPort`
- `ModelIterationHintPort`

合计新增 20 个 L1 第六阶段抽象端口。

## 4. 每个端口职责

### 4.1 ModelPort

职责：定义模型请求信封进入模型响应边界的协议形态。

不做：不调用真实模型，不做模型路由，不构造提示词，不选择 Skill，不调用工具。

### 4.2 ModelSessionPort

职责：定义模型会话引用、通道、会话链和作用域边界。

不做：不创建真实会话，不保存真实上下文，不维护连接。

### 4.3 ModelMessagePort

职责：定义模型输入消息、输出消息和观察消息的引用协议。

不做：不发送消息，不调用聊天接口，不拼接对话历史。

### 4.4 ModelContextPort

职责：定义模型可用上下文边界，包括内容、载荷、消息、Skill、工具组和观察引用。

不做：不压缩上下文，不读取文件或记忆，不构造提示词。

### 4.5 ModelAvailableActionViewPort

职责：定义模型当前可见 Skill、工具组、观察和边界说明的视图协议。

不做：不选择 Skill，不释放工具，不执行安全裁决，不恢复旧能力包体系。

### 4.6 ModelRequestEnvelopePort

职责：定义模型请求信封的声明协议。

不做：不发起真实模型请求，不拼接上下文，不构造提示词。

### 4.7 ModelResponseEnvelopePort

职责：定义模型响应信封的声明协议，承载文本输出、Skill 选择意图、工具调用意图和观察需求引用。

不做：不执行响应动作，不替模型选择 Skill，不调用工具。

### 4.8 ModelToolCallEnvelopePort

职责：定义大模型想调用工具时的结构化意图信封。

不做：不执行工具，不释放工具，不调用函数，不生成真实副作用。

### 4.9 ModelObservationEnvelopePort

职责：定义观察结果进入模型上下文的信封协议。

不做：不读取观察内容，不做摘要算法，不做清洗算法。

### 4.10 ModelErrorEnvelopePort

职责：定义错误事实进入模型上下文的信封协议。

不做：不执行恢复算法，不自动重试，不修改系统。

### 4.11 ModelFailureFeedbackPort

职责：定义失败原因、卡点和下一步建议的反馈协议。

不做：不自动重试，不修改系统，不生成补丁。

### 4.12 ModelCorrectionHintPort

职责：定义模型对 Skill、工具说明、边界说明或流程说明的修正提示协议。

不做：不修正 Skill，不写文件，不生成真实修改。

### 4.13 ModelLearningIntentPort

职责：定义模型提出系统需要学习什么的意图协议。

不做：不执行学习，不读取资料，不写知识库，不生成 Skill。

### 4.14 ModelToolNeedFeedbackPort

职责：定义模型对新工具需求、工具不足或工具说明不足的反馈协议。

不做：不生产工具，不修改工具组，不注册工具。

### 4.15 ModelSkillGapFeedbackPort

职责：定义模型对 Skill 缺失、说明不足或边界不清的反馈协议。

不做：不生成 Skill，不修复 Skill，不创建 Skill 版本。

### 4.16 ModelReflectionPort

职责：定义模型对任务、Skill 使用和工具组调用链的反思协议。

不做：不执行改进，不保存长期记忆，不修改系统。

### 4.17 ModelSelfReviewPort

职责：定义模型对自身输出质量、行动路径和错误原因的自评协议。

不做：不做自动评分算法，不触发真实改写。

### 4.18 ModelOutcomeAssessmentPort

职责：定义模型对任务结果和验证证据的评估协议。

不做：不做真实验收，不替代测试，不替代验证。

### 4.19 ModelEvolutionHintPort

职责：定义模型提出系统可能需要结构级演化的提示协议。

不做：不执行进化，不修改架构，不生成候选变更。

### 4.20 ModelIterationHintPort

职责：定义模型提出系统可能需要小步迭代的提示协议。

不做：不生成补丁，不合入代码，不回滚版本。

## 5. 与 L0 的依赖关系

本阶段继续复用 L0 原语和值对象，包括但不限于：

- `TraceContext`
- `CoreResult`
- `CoreError`
- `ContentRef`
- `PayloadRef`
- `MessageRef`
- `ChannelRef`
- `ConversationRef`
- `SkillRef`
- `ToolRef`
- `ActionIntent`
- `EffectRef`
- `ObservationRef`
- `SignalRef`
- `MetricRef`
- `AuditRef`
- `EvidenceRef`
- `ActorRef`
- `ScopeRef`
- `GoalRef`
- `PlanRef`
- `ResourceRef`
- `PolicyRef`
- `ContractRef`
- `Decision`
- `RiskView`
- `VersionRef`
- `SchemaRef`
- `NamespaceRef`
- `RelationRef`
- `TestRef`
- `ValidationRef`
- `VerificationRef`

未向 L0 添加任何新对象，未修改 L0 代码。已与第 1-5 阶段补丁交接包中的 L0 源码做哈希对比，排除缓存后无差异。

## 6. 与 L1 第一至第五阶段骨架的关系

本阶段仅新增第六阶段模块，没有重构第一至第五阶段既有公共骨架。

复用关系：

- 复用 `PortResult` 作为端口方法主返回值。
- 复用 `PortBoundaryContext`、`QueryEnvelope` 等 L1 第一阶段信封对象。
- 复用第五阶段 `SkillExposureView`、`SkillFlowView`、`ToolReleaseView`、`SkillEvolutionHint`、`SkillIterationHint`、`SkillGapReport`、`ToolNeedReport`、`ToolGroupGapReport` 等对象。
- 未恢复旧能力包体系，未引入旧路由器、旧执行器或旧主循环。

## 7. 面向 L2-L6 的前瞻引用说明

- L2 可记录模型会话、信封、反馈和反思状态。
- L3 可编排模型信封、Skill 直显、工具组释放和观察回传链路。
- L4 可在这些端口后方实现真实模型适配器，但 L1 不实现。
- L5 可通过模型上下文和可见行动视图限制插件污染模型输入。
- L6 可由子系统提交模型反馈、反思、学习意图、迭代提示和进化提示。

## 8. 为什么 ModelPort 可以存在但必须隔离

ModelPort 是模型输入输出的协议边界，不是模型执行器。它必须存在，因为新版主链需要稳定表达模型请求、响应、消息、上下文、观察和错误；但它必须隔离，因为一旦在 L1 绑定真实模型 SDK、真实连接、真实会话或提示词策略，就会污染 L1 的纯协议层职责，并破坏后续 L2-L6 的分层边界。

## 9. 为什么本阶段不实现真实模型调用

真实模型调用属于 L4 外部适配层或更高层的实现职责。L1 若提前实现真实模型调用，会引入网络、凭据、SDK、上下文拼接、重试、错误恢复等副作用，违背“端口协议层只定义边界”的原则。

## 10. 为什么本阶段不实现 prompt 构造器

提示词构造涉及策略、上下文选择、压缩、排序、风险边界和模型供应方差异，这些属于后续运行编排或模型适配层。L1 只声明模型请求信封和上下文引用，不构造具体提示词。

## 11. 为什么模型反馈可作为后续学习 / 迭代 / 进化证据来源

模型在执行过程中最容易发现 Skill 说明不足、工具不足、边界解释不清和任务失败卡点。本阶段把这些信息结构化为反馈、反思、学习意图、迭代提示和进化提示，使后续阶段可以进行验证、归因、候选生成和回滚治理。

这些反馈只是证据来源，不是执行命令。

## 12. 为什么本阶段不执行真实学习、迭代、进化

第六阶段只负责模型抽象、模型信封、模型反馈和模型反思。正式自我学习、自我迭代、自我进化端口放在第七阶段。本阶段若提前执行真实学习、迭代或进化，会越过阶段边界，并绕过验证、候选、回滚和治理协议。

## 13. 禁止事项检查

已检查：

- 无 L2-L6 import。
- 无第三方库 import。
- 无真实 IO、网络、进程、线程、后台任务、数据库调用。
- 无真实模型调用。
- 无真实模型 SDK。
- 无真实模型路由。
- 无真实上下文拼接算法。
- 无真实 prompt 构造器。
- 无真实 Skill 选择、真实工具释放、真实工具调用。
- 无真实学习、真实迭代、真实进化。
- 无旧能力包核心对象。
- 无新版禁用核心词作为对象。
- `ModelToolCallEnvelopePort` 只定义工具调用意图信封，不执行工具。
- `ModelLearningIntentPort` 只定义学习意图，不执行学习。
- `ModelReflectionPort` 只定义反思协议，不执行系统修改。

## 14. 测试命令

已运行：

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
python3 -m pytest -q tests/test_l1_phase6_model_ports.py
python3 -m pytest -q tests/test_l1_phase6_model_envelope_ports.py
python3 -m pytest -q tests/test_l1_phase6_model_feedback_ports.py
python3 -m pytest -q tests/test_l1_phase6_model_reflection_ports.py
```

## 15. 测试结果

- `python3 -m compileall -q tiangong_kernel tests`：通过。
- `python3 -m pytest -q tests`：`237 passed in 5.26s`。
- `test_l1_no_l2_imports.py`：`1 passed`。
- `test_l1_no_third_party_imports.py`：`1 passed`。
- `test_l1_no_real_io.py`：`1 passed`。
- `test_l1_ports_are_abstract.py`：`1 passed`。
- `test_l1_ports_return_core_result.py`：`2 passed`。
- `test_l1_uses_l0_primitives.py`：`1 passed`。
- `test_l1_no_execution_keywords.py`：`1 passed`。
- `test_l1_chinese_docstrings.py`：`1 passed`。
- `test_l1_phase6_model_ports.py`：`5 passed`。
- `test_l1_phase6_model_envelope_ports.py`：`5 passed`。
- `test_l1_phase6_model_feedback_ports.py`：`5 passed`。
- `test_l1_phase6_model_reflection_ports.py`：`5 passed`。

说明：一次批量串行单项测试命令被容器工具超时截断；相关测试均已改为单条命令逐项补跑，并全部通过。最终全量测试与单项测试均完整运行通过。

## 16. 未做事项

- 未开发第七阶段和第八阶段。
- 未实现真实模型调用。
- 未实现真实模型会话。
- 未实现真实模型路由。
- 未实现真实上下文拼接算法。
- 未实现真实 prompt 构造器。
- 未实现真实工具调用协议转换。
- 未实现真实 Skill 选择算法。
- 未实现真实 Skill 展示算法。
- 未实现真实 Skill 学习、迭代、进化。
- 未实现真实工具加载、释放、调用、执行、生产。
- 未实现插件宿主。
- 未实现真实安全裁决、风险评分或审批流。
- 未恢复旧能力包体系。

## 17. 是否允许进入 L1 第七阶段

建议允许进入 L1 第七阶段。

理由：第六阶段前置条件已满足；第六阶段源码、测试、开发日志、交接报告已完成；全量测试和专项测试均通过；L0 未修改；第一至第五阶段测试未回退；第七、第八阶段内容未提前实现。
