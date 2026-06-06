# 天工造物新版 L1 端口协议层第四阶段开发日志

## 1. 本阶段目标

本阶段只开发 L1 第四阶段：控制面边界端口协议。

目标是新增控制面边界、策略、风险、决策四组协议端口，只定义界限、输入、输出、失败表达和替代路径表达，不实现真实裁决算法，不实现真实风险评分，不实现真实工具释放，不实现真实模型调用，不实现真实权限系统。

总原则：

1. 第一方向：工程生命体。
2. 第二方向：大模型执行力 + 绝对边界。
3. 控制面只表达边界，不替大模型思考，不替大模型选择 Skill，不替大模型选择工具。
4. 边界不是执行障碍，而是可解释、可追踪、可降级、可替代的界限协议。

## 2. 新增文件清单

源码文件：

1. `tiangong_kernel/l1_ports/control_boundary_ports.py`
2. `tiangong_kernel/l1_ports/policy_ports.py`
3. `tiangong_kernel/l1_ports/risk_ports.py`
4. `tiangong_kernel/l1_ports/decision_ports.py`

测试文件：

1. `tests/test_l1_phase4_control_boundary_ports.py`
2. `tests/test_l1_phase4_policy_ports.py`
3. `tests/test_l1_phase4_risk_ports.py`
4. `tests/test_l1_phase4_decision_ports.py`

文档文件：

1. `docs/l1_phase4_development_log_zh.md`
2. `docs/l1_phase4_handoff_report_zh.txt`

## 3. 新增端口清单

### 3.1 控制面边界端口

1. `BoundaryCheckPort`
2. `BoundaryExplainPort`
3. `BoundaryAlternativePort`
4. `BoundaryViolationRecordPort`
5. `ToolReleaseBoundaryPort`

### 3.2 策略端口

1. `PolicyReferencePort`
2. `PolicyLookupPort`
3. `PolicyBoundaryPort`
4. `PolicyExplainPort`

### 3.3 风险端口

1. `RiskViewPort`
2. `RiskBoundaryPort`
3. `RiskExplainPort`
4. `RiskEscalationHintPort`

### 3.4 决策端口

1. `DecisionReferencePort`
2. `DecisionRecordPort`
3. `DecisionBoundaryPort`
4. `DecisionFeedbackPort`

合计新增 17 个第四阶段端口。

## 4. 每个端口职责

### 4.1 `BoundaryCheckPort`

职责：声明某个行动意图是否可能触碰控制面边界的协议形式。

明确不做：不实现真实边界算法，不做真实裁决，不阻断大模型正常执行，不替大模型选择 Skill 或工具。

### 4.2 `BoundaryExplainPort`

职责：声明边界原因、触碰规则、替代路径、是否可降级等说明协议。

明确不做：不生成真实解释算法，不调用模型，不改变控制流。

### 4.3 `BoundaryAlternativePort`

职责：声明越界时的安全替代方向、降级方向、只读观察方向。

明确不做：不执行替代动作，不拆分真实任务，不生成真实计划。

### 4.4 `BoundaryViolationRecordPort`

职责：声明越界事实、来源事件、指标和证据引用的记录协议。

明确不做：不写日志，不落盘，不上报远程审计系统。

### 4.5 `ToolReleaseBoundaryPort`

职责：声明 Skill 被选择后、工具组可见前需要检查的边界协议。

明确不做：不释放工具，不调用工具，不生成租约，不执行工具组。

### 4.6 `PolicyReferencePort`

职责：声明 `PolicyRef` 的引用和返回协议。

明确不做：不加载策略，不裁决策略，不读取外部策略源。

### 4.7 `PolicyLookupPort`

职责：声明策略查询条件与策略引用集合返回协议。

明确不做：不读取文件、数据库或远程策略中心。

### 4.8 `PolicyBoundaryPort`

职责：声明策略适用范围和禁止范围的说明协议。

明确不做：不执行真实策略裁决，不改变请求状态。

### 4.9 `PolicyExplainPort`

职责：声明策略解释材料、规则和提示返回协议。

明确不做：不调用模型，不生成真实解释，不做裁决。

### 4.10 `RiskViewPort`

职责：声明 `RiskView` 的提交、读取和边界说明协议。

明确不做：不评分，不实现 A 等级算法，不做最终裁决。

### 4.11 `RiskBoundaryPort`

职责：声明请求可能触及的风险边界说明协议。

明确不做：不阻断，不执行，不生成审批。

### 4.12 `RiskExplainPort`

职责：声明风险说明材料、提示和规则返回协议。

明确不做：不调用模型，不生成真实解释，不改变风险事实。

### 4.13 `RiskEscalationHintPort`

职责：声明可能需要更高层处理的风险提示协议。

明确不做：不生成确认票据，不生成授权租约，不创建审批流，不要求每一步申请审批。

### 4.14 `DecisionReferencePort`

职责：声明 `DecisionRef` 与 `Decision` 事实的引用协议。

明确不做：不做真实决策，不改变决策事实，不触发执行。

### 4.15 `DecisionRecordPort`

职责：声明 `Decision` 事实记录协议。

明确不做：不落盘，不写审计库，不调用外部系统。

### 4.16 `DecisionBoundaryPort`

职责：声明 `Decision` 对象适用范围的边界说明协议。

明确不做：不执行裁决，不改变 `Decision`，不触发审批。

### 4.17 `DecisionFeedbackPort`

职责：声明边界结果、越界事实、继续建议和替代路径的反馈协议。

明确不做：不执行反馈算法，不创建审批，不调用工具。

## 5. 与 L0 的依赖关系

本阶段复用 L0 原语和引用对象，不重新定义同义对象。

主要复用对象包括：

- `CoreResult`
- `TraceContext`
- `Decision`
- `DecisionRef`
- `RiskView`
- `RiskRef`
- `PolicyRef`
- `ContractRef`
- `ActorRef`
- `ScopeRef`
- `GoalRef`
- `PlanRef`
- `ActionIntent`
- `EffectRef`
- `ResourceRef`
- `ToolRef`
- `SkillRef`
- `EventRef`
- `ObservationRef`
- `SignalRef`
- `MetricRef`
- `AuditRef`
- `EvidenceRef`
- `VersionRef`
- `SchemaRef`
- `NamespaceRef`
- `TestRef`
- `ValidationRef`
- `VerificationRef`

L0 未被修改。排除 `__pycache__` 后，L0 源码与原始基线无差异。

## 6. 与 L1 第一、第二、第三阶段骨架的关系

本阶段复用第一阶段的：

- `PortResult`
- `PortBoundary`
- `BoundaryHint`
- `BoundaryRule`
- `BoundaryViolation`
- `PortBoundaryContext`
- `CommandEnvelope`
- `QueryEnvelope`

本阶段没有修改第一阶段公共骨架。

本阶段没有修改第二阶段端口模块。

本阶段没有修改第三阶段端口模块。

本阶段没有修改 `tiangong_kernel/l1_ports/__init__.py`。

## 7. 面向 L2-L6 的前瞻引用说明

### L2

L2 生命体状态层可引用本阶段的边界、策略、风险和决策反馈对象，用于记录当前是否越界、越界原因、替代路径、风险提示和决策反馈状态。

### L3

L3 运行编排层可调用本阶段端口进行轻量边界检查，但不应把本阶段端口变成复杂审批链。本阶段只给出协议形态和结果包装。

### L4

L4 外部适配层可实现真实策略、真实风险、真实边界检查适配器。但真实算法和真实外部连接只能在 L4 或更高层按边界实现，不能回填到 L1。

### L5

L5 插件宿主层可引用本阶段端口限制插件越界，并记录插件生命周期中的边界反馈。

### L6

L6 子系统插件层可通过本阶段端口声明自身可用范围，提交边界反馈、风险视图和决策反馈，但不能绕过边界。

## 8. 为什么控制面边界不是大模型执行障碍

本阶段不把控制面设计为审批器、执行器或旧式中心调度器。

控制面边界端口只返回：

1. 当前请求触碰了什么边界。
2. 为什么触碰边界。
3. 是否存在替代路径。
4. 是否可以降级。
5. 是否可以拆分为更小动作。
6. 是否需要更高层处理。

这让后续 L3-L6 可以继续组织工作，而不是因为边界不可见而停在沉默阻断状态。

## 9. 为什么本阶段不实现真实裁决算法

L1 是端口协议层，不是算法层、适配层或执行层。

若在 L1 实现真实裁决算法，会导致：

1. L1 过早绑定策略实现。
2. L2-L6 无法按自身职责扩展。
3. 控制面变成复杂审批链，损害大模型执行力。
4. L1 与外部系统产生真实 IO 或真实权限耦合。

因此本阶段只定义协议，不实现算法。

## 10. 禁止事项检查

已检查：

- 未使用 `open()`。
- 未使用 `Path.read_text()`、`Path.write_text()`、`Path.exists()` 进行真实文件判断。
- 未使用 `os.listdir`、`os.walk`、`os.environ`。
- 未使用 `socket`、`subprocess`、`requests`、`httpx`、`urllib`。
- 未使用 `sqlite3.connect`。
- 未使用 `asyncio.create_task`、`threading.Thread`、`multiprocessing`、`time.sleep`。
- 未实现真实策略引擎。
- 未实现真实权限裁决。
- 未实现真实风险评分。
- 未实现真实 A 等级判定。
- 未实现真实确认票据。
- 未实现真实授权租约。
- 未实现真实审批流程。
- 未实现真实工具释放。
- 未实现真实工具调用。
- 未实现真实模型调用。
- 未实现真实插件加载。
- 未导入 L2-L6。
- 未导入旧版上层模块。
- 未导入第三方库。
- 未引入旧版核心对象作为新版核心。
- 未引入 CapabilityPort 或 AbilityPackagePort。
- `ToolReleaseBoundaryPort` 只做边界协议，不释放工具。

## 11. 测试命令

已运行：

```bash
python3 -m compileall -q tiangong_kernel tests
```

已运行：

```bash
python3 -m pytest -q tests
```

已单独运行或补跑：

```bash
python3 -m pytest -q tests/test_l1_no_l2_imports.py
python3 -m pytest -q tests/test_l1_no_third_party_imports.py
python3 -m pytest -q tests/test_l1_no_real_io.py
python3 -m pytest -q tests/test_l1_ports_are_abstract.py
python3 -m pytest -q tests/test_l1_ports_return_core_result.py
python3 -m pytest -q tests/test_l1_uses_l0_primitives.py
python3 -m pytest -q tests/test_l1_no_execution_keywords.py
python3 -m pytest -q tests/test_l1_chinese_docstrings.py
python3 -m pytest -q tests/test_l1_phase4_control_boundary_ports.py
python3 -m pytest -q tests/test_l1_phase4_policy_ports.py
python3 -m pytest -q tests/test_l1_phase4_risk_ports.py
python3 -m pytest -q tests/test_l1_phase4_decision_ports.py
```

## 12. 测试结果

结果：

- `python3 -m compileall -q tiangong_kernel tests`：通过。
- `python3 -m pytest -q tests`：`182 passed in 2.88s`。
- 第四阶段专项测试合计：20 passed。
- 第一、第二、第三阶段测试未回退。
- L1 静态边界测试未回退。

两次批量串行单测命令中途被容器超时截断；被截断的测试均已改为单条命令补跑并通过。因此本阶段测试已完整运行。

## 13. 未做事项

按阶段边界未做：

- 未开发第五至第八阶段。
- 未开发 Skill 端口、工具端口、模型端口、记忆端口、检索端口、学习端口、插件端口、注册端口、调度端口、触发端口、计时端口。
- 未实现真实状态机。
- 未实现真实运行循环。
- 未实现真实工具释放。
- 未实现真实模型会话。
- 未实现真实记忆算法。
- 未实现真实插件宿主。
- 未实现真实安全裁决。
- 未实现真实风险评分。
- 未实现真实审批流。

## 14. 是否允许进入 L1 第五阶段

建议允许进入 L1 第五阶段。

理由：第四阶段源码、专项测试、开发日志、交接报告和完整交接 zip 已完成；全量测试通过；L0 未修改；第一、第二、第三阶段未回退；第五至第八阶段内容未提前实现。
