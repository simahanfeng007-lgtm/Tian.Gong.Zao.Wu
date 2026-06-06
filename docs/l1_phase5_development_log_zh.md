# 天工造物新版 L1 端口协议层第五阶段开发日志

## 1. 本阶段目标

本阶段只开发 L1 第五阶段：Skill 直显与工具组端口协议。目标是为新版主链建立协议骨架：大模型先看到 Skill，选择 Skill 后，由边界层检查，再让后续层按协议释放该 Skill 所需工具组。L1 只定义协议，不执行 Skill，不调用工具，不释放工具，不调用模型，不实现插件宿主，不恢复旧能力包体系。

## 2. 新增文件清单

新增源码文件：

1. `tiangong_kernel/l1_ports/skill_ports.py`
2. `tiangong_kernel/l1_ports/tool_ports.py`
3. `tiangong_kernel/l1_ports/tool_group_ports.py`
4. `tiangong_kernel/l1_ports/tool_binding_ports.py`
5. `tiangong_kernel/l1_ports/tool_release_ports.py`

新增测试文件：

1. `tests/test_l1_phase5_skill_ports.py`
2. `tests/test_l1_phase5_tool_ports.py`
3. `tests/test_l1_phase5_tool_group_ports.py`
4. `tests/test_l1_phase5_tool_binding_ports.py`
5. `tests/test_l1_phase5_tool_release_ports.py`

新增文档文件：

1. `docs/l1_phase5_development_log_zh.md`
2. `docs/l1_phase5_handoff_report_zh.txt`

## 3. 新增端口清单

### 3.1 Skill 端口

1. `SkillReferencePort`
2. `SkillRegistryPort`
3. `SkillQueryPort`
4. `SkillExposurePort`
5. `SkillFlowPort`
6. `SkillBoundaryPort`

### 3.2 Tool 端口

1. `ToolReferencePort`
2. `ToolDescriptionPort`
3. `ToolInvocationIntentPort`
4. `ToolInputBoundaryPort`
5. `ToolOutputBoundaryPort`
6. `ToolObservationPort`

### 3.3 ToolGroup 端口

1. `ToolGroupReferencePort`
2. `ToolGroupDescriptionPort`
3. `ToolGroupQueryPort`
4. `ToolGroupBoundaryPort`
5. `ToolGroupLifecyclePort`

### 3.4 ToolBinding 端口

1. `SkillToolBindingPort`
2. `ToolGroupBindingPort`
3. `ToolDependencyPort`
4. `ToolUsageFlowPort`

### 3.5 ToolRelease 端口

1. `ToolReleaseIntentPort`
2. `ToolReleaseRequestPort`
3. `ToolReleaseResultPort`
4. `ToolReleaseViewPort`
5. `ToolReleaseRevocationPort`

本阶段合计新增 26 个抽象端口。

## 4. 每个端口职责

### 4.1 Skill 端口职责

- `SkillReferencePort`：定义 Skill 引用、版本和证据返回协议。
- `SkillRegistryPort`：定义 Skill 注册请求和注册结果引用协议。
- `SkillQueryPort`：定义 Skill 查询条件与候选引用返回协议。
- `SkillExposurePort`：定义大模型可见 Skill 说明视图的输出边界。
- `SkillFlowPort`：定义 Skill 工作流程、输入要求、输出结果和失败反馈格式。
- `SkillBoundaryPort`：定义 Skill 可用范围、禁用范围和风险边界说明协议。

### 4.2 Tool 端口职责

- `ToolReferencePort`：定义工具引用协议。
- `ToolDescriptionPort`：定义工具名称、用途、输入输出边界的说明协议。
- `ToolInvocationIntentPort`：定义大模型想调用工具时的意图表达协议。
- `ToolInputBoundaryPort`：定义工具输入边界说明协议。
- `ToolOutputBoundaryPort`：定义工具输出边界说明协议。
- `ToolObservationPort`：定义工具观察结果返回给大模型的协议。

### 4.3 ToolGroup 端口职责

- `ToolGroupReferencePort`：定义工具组资源引用协议。
- `ToolGroupDescriptionPort`：定义工具组包含哪些工具、适用哪个 Skill、输入输出边界的说明协议。
- `ToolGroupQueryPort`：定义按 Skill 或范围查询工具组引用的协议。
- `ToolGroupBoundaryPort`：定义工具组适用范围和风险边界说明协议。
- `ToolGroupLifecyclePort`：定义 declared、visible、released、revoked、expired 等状态事实协议。

### 4.4 ToolBinding 端口职责

- `SkillToolBindingPort`：定义 Skill 与工具引用之间的绑定协议。
- `ToolGroupBindingPort`：定义 Skill 与工具组之间的绑定协议。
- `ToolDependencyPort`：定义工具间依赖、前置观察和关系引用协议。
- `ToolUsageFlowPort`：定义工具调用顺序、可并行性和失败反馈协议。

### 4.5 ToolRelease 端口职责

- `ToolReleaseIntentPort`：定义 Skill 被选择后可能需要释放某个工具组的意图协议。
- `ToolReleaseRequestPort`：定义工具组释放请求结构和协议返回。
- `ToolReleaseResultPort`：定义释放结果的观察、指标、审计和视图返回协议。
- `ToolReleaseViewPort`：定义释放后大模型可见的工具组视图协议。
- `ToolReleaseRevocationPort`：定义工具组撤销请求与撤销结果引用协议。

## 5. 每个端口明确不做什么

本阶段所有端口均不做真实外部能力：

- 不实现真实 Skill 注册表。
- 不实现真实 Skill 查询引擎。
- 不实现真实 Skill 展示算法。
- 不执行 Skill 流程。
- 不加载工具。
- 不释放工具。
- 不调用工具。
- 不撤销真实工具。
- 不实现工具依赖检查算法。
- 不调用模型。
- 不实现插件宿主。
- 不写文件、数据库、注册表或外部系统。
- 不生成确认票据、授权租约或审批流。

## 6. 与 L0 的依赖关系

本阶段复用 L0 事实对象和引用对象，包括：

- `CoreResult`
- `TraceContext`
- `SkillRef`
- `ToolRef`
- `ActionIntent`
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
- `RiskView`
- `RelationRef`
- `DependencyRef`
- `VersionRef`
- `SchemaRef`
- `NamespaceRef`
- `ValidationRef`
- `VerificationRef`

L0 中没有独立 `ToolGroupRef`，本阶段按要求优先使用 `ResourceRef` 表达工具组引用，使用 `RelationRef` / `DependencyRef` 表达工具组关系和工具依赖，未污染 L0 身份体系。

## 7. 与 L1 第一至第四阶段骨架的关系

- 复用第一阶段 `PortResult`、`PortBoundary`、`CommandEnvelope`、`QueryEnvelope`、`PortBoundaryContext`。
- 复用第四阶段 `ToolReleaseBoundary`，不重新发明另一套工具释放边界对象。
- 未修改 L1 第一至第四阶段既有端口模块。
- 未修改 `tiangong_kernel/l1_ports/__init__.py`。

## 8. 面向 L2-L6 的前瞻引用说明

- L2 可记录 Skill、Tool、ToolGroup、ToolBinding、ToolRelease 的状态与引用事实。
- L3 可将大模型选择 Skill 后的流程编排为：Skill 说明 → 边界检查 → 工具组视图 → 工具意图 → 观察返回。
- L4 可实现真实文件、网络、工具、模型、外部协议适配器，但本阶段不实现。
- L5 可借助工具组、绑定和释放视图限制插件可见范围。
- L6 可通过这些端口提交子系统 Skill、工具组需求、工具观察和撤销事实。

## 9. 为什么 Skill 是大模型行动入口

Skill 是大模型能理解的知识动作单元，包含目标、步骤、输入、输出、失败反馈和所需工具组。相比直接暴露工具，Skill 能把“为什么做、怎么做、边界在哪里”放在模型可理解的层面，使大模型先选择做事方法，再按方法获得工具组。

## 10. 为什么工具组释放不等于旧能力包

工具组释放只是 Skill 被选择后，把该 Skill 所需工具引用以可见视图形式提供给大模型的协议。它不是封装执行计划，不接管大模型判断，不路由任务，不执行工具，不成为中间执行器。新版主链仍是 Skill 直显、大模型主控、边界层约束、工具组按需可见。

## 11. 为什么本阶段不实现真实工具调用

L1 是端口协议层，只定义输入、输出、失败和边界表达。如果在 L1 实现真实工具调用，会破坏分层，让协议层承担 L4/L3 的适配和编排职责，也会让边界层之前出现真实副作用。因此本阶段只保留 `ToolInvocationIntentPort` 表达工具调用意图。

## 12. 为什么本阶段不实现真实工具释放

工具释放涉及边界检查、可见范围、资源状态、工具适配器、撤销与审计，属于后续 L3/L4/L5 的实现职责。L1 只能定义 `ToolReleaseIntentPort`、`ToolReleaseRequestPort`、`ToolReleaseResultPort`、`ToolReleaseViewPort`、`ToolReleaseRevocationPort` 的协议形状，不改变真实系统。

## 13. 禁止事项检查

已检查：

- 无 L2-L6 import。
- 无第三方库 import。
- 无真实 IO、网络、进程、后台任务调用。
- 无真实 Skill 注册表、真实工具释放、真实工具调用。
- 无旧能力包主链对象作为核心对象。
- 无新版核心对象中使用“神枢”。
- `ToolReleasePort` 系列只定义协议，不释放工具。
- `SkillExposurePort` 只定义 Skill 暴露协议，不暴露内部 Port。

## 14. 测试命令

实际运行：

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
python3 -m pytest -q tests/test_l1_phase5_skill_ports.py
python3 -m pytest -q tests/test_l1_phase5_tool_ports.py
python3 -m pytest -q tests/test_l1_phase5_tool_group_ports.py
python3 -m pytest -q tests/test_l1_phase5_tool_binding_ports.py
python3 -m pytest -q tests/test_l1_phase5_tool_release_ports.py
```

## 15. 测试结果

- `python3 -m compileall -q tiangong_kernel tests`：通过。
- `python3 -m pytest -q tests`：`207 passed in 3.71s`。
- 必测项：全部通过。
- 第五阶段专项测试：全部通过。

批量串行单项测试命令曾被容器超时截断；被截断项已改成单条命令补跑并通过。最终测试完整运行并通过。

## 16. 未做事项

按阶段边界未做：

- 未开发第六至第八阶段。
- 未开发 ModelPort、ModelSessionPort、ModelRequestEnvelope、ModelResponseEnvelope。
- 未开发 MemoryPort、ContextPort、RetrievalPort、LearningPort、PluginPort、SchedulePort、TriggerPort、TimerPort。
- 未实现真实状态机、真实运行循环、真实工具释放、真实模型会话、真实记忆算法、真实插件宿主。
- 未实现真实安全裁决、真实风险评分、真实审批流。
- 未恢复旧能力包体系。

## 17. 是否允许进入 L1 第六阶段

建议进入 L1 第六阶段。

理由：第五阶段新增端口、测试、开发日志和交接报告已完成；完整测试通过；L0 未修改；L1 第一至第四阶段测试未回退；第六至第八阶段内容未提前实现。

---

# 第五阶段补丁记录：第六阶段前置接口补齐

## 补丁原因

第六阶段前置检查要求第五阶段已存在并可导入：

- `tiangong_kernel/l1_ports/skill_evolution_ports.py`
- `tiangong_kernel/l1_ports/tool_gap_ports.py`

原第五阶段交接包缺少这两个扩展协议模块，因此进行第 1-5 阶段补丁，不进入第六阶段。

## 补丁新增源码

- `tiangong_kernel/l1_ports/skill_evolution_ports.py`
- `tiangong_kernel/l1_ports/tool_gap_ports.py`

## 补丁新增测试

- `tests/test_l1_phase5_skill_evolution_ports.py`
- `tests/test_l1_phase5_tool_gap_ports.py`

## 补丁新增端口

- `SkillEvolutionHintPort`
- `SkillIterationHintPort`
- `SkillVersionHintPort`
- `SkillCorrectionHintPort`
- `SkillGapReportPort`
- `ToolNeedReportPort`
- `ToolGroupGapReportPort`
- `ToolGapBoundaryPort`

## 补丁边界

补丁只定义协议，不实现真实学习、真实自我迭代、真实自我进化、真实工具生产、真实工具释放、真实工具调用、真实模型调用或插件宿主。

## 补丁测试结果

- `python3 -m compileall -q tiangong_kernel tests`：通过。
- `python3 -m pytest -q tests`：`217 passed in 4.04s`。
- 补丁专项测试：`10 passed`。
- L1 必测项：全部单独补跑通过。

## 补丁后结论

第六阶段前置缺失项已补齐，建议重新进入 L1 第六阶段。
