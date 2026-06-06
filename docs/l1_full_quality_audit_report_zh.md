# 天工造物新版 L1 端口协议层第 1-8 阶段总质检报告

生成时间：2026-06-03  
审查身份：L1 全阶段质检员  
审查范围：L1 第 1-8 阶段完整交接包；只做质量审查，不做修复，不进入 L2。

---

## 1. 质检结论

**结论：不建议冻结 L1，应先进入修复阶段。**

交接包整体完整，`compileall` 与完整 `pytest` 均通过，L1 源码没有发现真实 IO、真实网络、真实模型调用、真实工具调用、真实插件宿主、L2-L6 import 或旧能力包主链恢复。L1 主体仍保持端口协议层属性。

但静态 AST 审查发现 1 个 P1：`tiangong_kernel/l1_ports/candidate_ports.py` 内部重复定义 `CandidatePromotionHint`，第二个定义覆盖第一个定义，导致统一候选晋升对象原设计中的 `iteration_candidate` 与 `evolution_candidate` 字段在运行时不可见。该问题不会导致当前测试失败，但会影响自我迭代 / 自我进化候选进入统一候选晋升链的协议完整性，属于冻结前必须修复的问题。

### 是否允许进入修复阶段

允许，且建议立即进入修复阶段。

### 是否允许冻结 L1

不建议冻结。必须先修复 P1，并处理关键 P2 后，再做冻结前复核。

---

## 2. 输入文件清单

| 类型 | 路径 | 审查说明 |
|---|---|---|
| L1 第 8 阶段交接包 | `/mnt/data/天工造物_L1_第8阶段_交接包_20260603.zip` | 本次审查主输入，已解压到独立审查目录。 |
| 第 8 阶段开发日志侧载文件 | `/mnt/data/l1_phase8_development_log_zh.md` | 与 zip 内同名文档存在内容差异；审查以 zip 内 project 为准，侧载文件作为对照。 |
| 第 8 阶段总收口报告侧载文件 | `/mnt/data/l1_phase8_closure_report_zh.txt` | 与 zip 内同名文档存在内容差异；审查以 zip 内 project 为准，侧载文件作为对照。 |
| L1 全阶段质检员提示词 | `/mnt/data/天工造物_L1全阶段质检员提示词_20260603.txt` | 本次审查规则来源。 |

原始 zip SHA256：

```text
bdcca1253c4b05106aac6cd18cfb8ed1a8923cffe2040ff5f48f9e489feaf9d0  /mnt/data/天工造物_L1_第8阶段_交接包_20260603.zip
```

审查目录：

```text
/mnt/data/audit_workspace/l1_phase8_package/project
```

---

## 3. zip 完整性检查

| 检查项 | 结果 |
|---|---|
| `zip -T` | 通过，`test of ... OK`。 |
| 能否正常解压 | 通过。 |
| 是否包含完整 `project/` | 通过。 |
| 是否包含 `tiangong_kernel/` | 通过。 |
| 是否包含 `tiangong_kernel/l0_primitives/` | 通过。 |
| 是否包含 `tiangong_kernel/l1_ports/` | 通过。 |
| 是否包含 `tests/` | 通过。 |
| 是否包含 `docs/` | 通过。 |
| 是否包含第 1-8 阶段开发日志 | 通过。 |
| 是否包含第 4-8 阶段交接报告与第 5 阶段 hotfix1 报告 | 通过。 |
| 是否包含第 8 阶段 closure report | 通过。 |
| 是否包含 `l1_stability_repair_pending_zh.md` | 通过。 |
| 文件总数 | 274 个文件。 |

未发现 zip 层 P0。

---

## 4. L0 完整性检查

| 检查项 | 结果 |
|---|---|
| `tiangong_kernel/l0_primitives/` 是否存在 | 通过。 |
| L0 `.py` 文件数量 | 58 个。 |
| L0 是否被本次质检修改 | 未修改。 |
| 是否能与独立 L0 最终归档包做 hash 比对 | 未能完成：本次用户未额外提供独立 L0 最终归档包或前阶段基线包。 |
| 包内 L0 测试状态 | 完整 `pytest tests` 中包含 L0 测试，整体通过。 |

说明：由于未提供独立 L0 归档基线，本次不能给出“跨包 hash 完全一致”的结论；只能给出包内清单、包内源码存在性、包内测试和静态边界结果。该项不判 P0，因为提示词要求是在用户提供 L0 基线包时必须进行 hash 比对。

---

## 5. L1 第 1-8 阶段文件完整性检查

### 5.1 L1 源码模块

预期 L1 源码模块全部存在：

- 第一阶段公共骨架：`__init__.py`、`base.py`、`port_result.py`、`port_error.py`、`port_boundary.py`、`port_health.py`、`port_lifecycle.py`、`envelope.py`
- 第二阶段：`infrastructure_ports.py`、`event_ports.py`、`observation_ports.py`、`metric_ports.py`、`audit_ports.py`
- 第三阶段：`content_ports.py`、`communication_ports.py`、`resource_ports.py`、`environment_ports.py`
- 第四阶段：`control_boundary_ports.py`、`policy_ports.py`、`risk_ports.py`、`decision_ports.py`
- 第五阶段：`skill_ports.py`、`tool_ports.py`、`tool_group_ports.py`、`tool_binding_ports.py`、`tool_release_ports.py`、`skill_evolution_ports.py`、`tool_gap_ports.py`
- 第六阶段：`model_ports.py`、`model_envelope_ports.py`、`model_feedback_ports.py`、`model_reflection_ports.py`
- 第七阶段：`memory_ports.py`、`context_ports.py`、`retrieval_ports.py`、`learning_ports.py`、`self_learning_ports.py`、`self_iteration_ports.py`、`evolution_ports.py`
- 第八阶段：`validation_ports.py`、`schedule_ports.py`、`state_continuity_ports.py`、`action_effect_ports.py`、`security_boundary_ports.py`、`component_registry_ports.py`、`compatibility_migration_ports.py`、`candidate_ports.py`、`change_ports.py`、`experiment_ports.py`

检查结果：全部存在。

### 5.2 L1 源码规模

| 项 | 数量 |
|---|---:|
| `tiangong_kernel/l1_ports/*.py` 模块数 | 49 |
| AST 顶层类总数 | 968 |
| 端口类数量 | 247 |
| dataclass 数量 | 709 |

---

## 6. docs 完整性检查

必需文档全部存在：

- `docs/l1_phase1_development_log_zh.md`
- `docs/l1_phase2_development_log_zh.md`
- `docs/l1_phase3_development_log_zh.md`
- `docs/l1_phase4_development_log_zh.md`
- `docs/l1_phase5_development_log_zh.md`
- `docs/l1_phase6_development_log_zh.md`
- `docs/l1_phase7_development_log_zh.md`
- `docs/l1_phase8_development_log_zh.md`
- `docs/l1_phase4_handoff_report_zh.txt`
- `docs/l1_phase5_handoff_report_zh.txt`
- `docs/l1_phase5_hotfix1_report_zh.txt`
- `docs/l1_phase6_handoff_report_zh.txt`
- `docs/l1_phase7_handoff_report_zh.txt`
- `docs/l1_phase8_handoff_report_zh.txt`
- `docs/l1_phase8_closure_report_zh.txt`
- `docs/l1_stability_repair_pending_zh.md`

检查结果：全部存在。

注意：上传的侧载 `l1_phase8_development_log_zh.md` 与 zip 内 `docs/l1_phase8_development_log_zh.md` 不完全一致；上传的侧载 `l1_phase8_closure_report_zh.txt` 与 zip 内 `docs/l1_phase8_closure_report_zh.txt` 也不完全一致。审查以 zip 内 project 为准，但归档前应统一同名文档版本。

---

## 7. tests 完整性检查

### 7.1 通用 L1 测试

全部存在并已运行：

- `tests/test_l1_no_l2_imports.py`
- `tests/test_l1_no_third_party_imports.py`
- `tests/test_l1_no_real_io.py`
- `tests/test_l1_ports_are_abstract.py`
- `tests/test_l1_ports_return_core_result.py`
- `tests/test_l1_uses_l0_primitives.py`
- `tests/test_l1_no_execution_keywords.py`
- `tests/test_l1_chinese_docstrings.py`

### 7.2 第八阶段专项测试

全部存在并已运行：

- `tests/test_l1_phase8_validation_ports.py`
- `tests/test_l1_phase8_schedule_ports.py`
- `tests/test_l1_phase8_state_continuity_ports.py`
- `tests/test_l1_phase8_action_effect_ports.py`
- `tests/test_l1_phase8_security_boundary_ports.py`
- `tests/test_l1_phase8_component_registry_ports.py`
- `tests/test_l1_phase8_compatibility_migration_ports.py`
- `tests/test_l1_phase8_candidate_ports.py`
- `tests/test_l1_phase8_change_ports.py`
- `tests/test_l1_phase8_experiment_ports.py`

检查结果：测试文件完整。

---

## 8. compileall 命令与结果

命令：

```bash
cd /mnt/data/audit_workspace/l1_phase8_package/project
python3 -m compileall -q tiangong_kernel tests
```

结果：通过，无错误输出。

环境：

```text
Python 3.13.5
```

---

## 9. pytest 命令与结果

### 9.1 完整测试

命令：

```bash
python3 -m pytest -q tests
```

结果：

```text
322 passed in 2.14s
```

### 9.2 通用 L1 必测项逐项结果

| 测试文件 | 结果 |
|---|---|
| `tests/test_l1_no_l2_imports.py` | `1 passed` |
| `tests/test_l1_no_third_party_imports.py` | `1 passed` |
| `tests/test_l1_no_real_io.py` | `1 passed` |
| `tests/test_l1_ports_are_abstract.py` | `1 passed` |
| `tests/test_l1_ports_return_core_result.py` | `2 passed` |
| `tests/test_l1_uses_l0_primitives.py` | `1 passed` |
| `tests/test_l1_no_execution_keywords.py` | `1 passed` |
| `tests/test_l1_chinese_docstrings.py` | `1 passed` |

### 9.3 第八阶段专项测试逐项结果

| 测试文件 | 结果 |
|---|---|
| `tests/test_l1_phase8_validation_ports.py` | `5 passed` |
| `tests/test_l1_phase8_schedule_ports.py` | `5 passed` |
| `tests/test_l1_phase8_state_continuity_ports.py` | `5 passed` |
| `tests/test_l1_phase8_action_effect_ports.py` | `5 passed` |
| `tests/test_l1_phase8_security_boundary_ports.py` | `5 passed` |
| `tests/test_l1_phase8_component_registry_ports.py` | `5 passed` |
| `tests/test_l1_phase8_compatibility_migration_ports.py` | `5 passed` |
| `tests/test_l1_phase8_candidate_ports.py` | `5 passed` |
| `tests/test_l1_phase8_change_ports.py` | `5 passed` |
| `tests/test_l1_phase8_experiment_ports.py` | `5 passed` |

说明：逐项运行过程中，一个批量 shell 命令曾被外层 timeout 截断；随后已对未完成的剩余第八阶段专项测试单独重跑并全部通过。因此本次测试视为完整运行。

---

## 10. 静态扫描结果

### 10.1 L2-L6 与旧上层 import

扫描范围：`tiangong_kernel/l1_ports/` 与 `tests/`。

结果：未发现 `tiangong_kernel.l2`、`tiangong_kernel.l3`、`tiangong_kernel.l4`、`tiangong_kernel.l5`、`tiangong_kernel.l6` import；未发现旧版天工造物上层实现 import。

### 10.2 第三方库 import

扫描范围：`tiangong_kernel/l1_ports/`。

结果：未发现第三方库 import。源码 import 限定在 `__future__`、`abc`、`dataclasses`、`enum`、`typing`、`tiangong_kernel.l0_primitives` 与 L1 包内相对导入。

### 10.3 真实 IO / 网络 / 进程 / 数据库 / 后台任务

扫描范围：`tiangong_kernel/l1_ports/`。

结果：未发现以下真实能力调用：`open(`、`Path.read_text`、`Path.write_text`、`os.listdir`、`os.walk`、`os.environ`、`socket`、`subprocess`、`requests`、`httpx`、`urllib`、`sqlite3.connect`、`asyncio.create_task`、`threading.Thread`、`multiprocessing`、`time.sleep`。

测试文件中存在 `Path.read_text` 等静态扫描用法，属于测试读取源码文本进行禁止项断言，不属于 L1 源码实现真实 IO，不判实现问题。

### 10.4 真实模型 / 工具 / 插件宿主

扫描范围：`tiangong_kernel/l1_ports/`。

结果：未发现 `openai`、`deepseek`、`qwen`、`claude`、`gemini`、`ollama`、`vllm`、`model.call`、`client.chat`、`tool.call`、`ToolExecutor`、`ModelExecutor`、`PluginHost`。

### 10.5 旧能力包 / 神枢 / Runtime 残留

- 未发现 `神枢` 作为新版核心对象。
- 未发现 `CapabilityPort`、`AbilityPackagePort`、`AbilityPackage`、`AbilityRouter`、`AbilityExecutor`、`能力包执行器`、`能力包路由器`、`能力包可见性桥接` 作为源码类名、端口名或执行链。
- `environment_ports.py` 中存在 `RuntimeContextPort` / `RuntimeContextDeclareRequest` / `RuntimeContextDeclareResponse`，`state_continuity_ports.py` 使用 L0 `RuntimeStateRef`。人工判断：这些是“运行上下文 / 运行状态引用”的协议命名，不是旧 Runtime 主循环，也没有真实执行循环；不判 P0/P1。但建议后续文档明确该命名不是旧核心概念。

---

## 11. 端口抽象性检查

AST 检查结果：

| 检查项 | 结果 |
|---|---|
| 端口类是否继承 `ABC` 或 `Protocol` | 通过。 |
| 端口方法是否带 `@abstractmethod` | 通过。 |
| 端口方法体是否仅 `raise NotImplementedError` / `pass` / `...` | 通过。 |
| 是否持有真实资源句柄字段 | 未发现。 |

补充：`BasePort.identity` 是抽象属性，返回 `PortIdentity`，不属于业务端口操作方法，不要求返回 `CoreResult` / `PortResult`。

---

## 12. CoreResult / PortResult 返回规范检查

AST 检查结果：

- 所有业务端口抽象方法返回 `PortResult[...]` 或 `CoreResult[...]`。
- 未发现端口方法以裸 `dict`、裸 `bool`、裸 `str`、裸 `list` 作为主返回值。
- `BasePort.identity -> PortIdentity` 是身份属性，属于基础描述属性，不判违规。

---

## 13. L0 Ref / L1 Envelope 使用检查

整体判断：通过，但存在一致性整修项。

已观察到 L1 第八阶段复用大量 L0 Ref / Value Object 与 L1 Envelope / Boundary：`ValidationRef`、`VerificationRef`、`TestRef`、`ScheduleRef`、`TriggerRef`、`TimerRef`、`StateSnapshotRef`、`CheckpointRef`、`RecoveryPointRef`、`ActionIntent`、`EffectRef`、`TransactionRef`、`CompensationRef`、`RollbackRef`、`DeletionRef`、`SecretRef`、`CredentialRef`、`PrivacyRef`、`TrustBoundaryRef`、`ComponentRef`、`PackageRef`、`SandboxRef`、`MigrationRef`、`DeprecationRef`、`SchemaRef`、`VersionRef`、`EvidenceRef`、`AuditRef`、`ResourceRef`、`TraceContext`、`PortBoundaryContext` 等。

需要后续整修的问题：候选相关对象普遍使用 `ResourceRef` 承载候选引用。由于当前 L0 没有独立 `CandidateRef`，本阶段不应临时新造 Ref；但冻结前应明确：继续使用 `ResourceRef`，还是在后续 L0/L1 稳定化时引入候选专用引用。

---

## 14. 中文 docstring 检查

通用测试 `tests/test_l1_chinese_docstrings.py` 已通过。抽样与静态扫描显示：模块级中文说明存在，公开端口类基本具备中文 docstring，并说明职责与“不做什么”。

仍需整修：部分第八阶段端口 docstring 为单行长句，格式可读性较弱；后续可统一为多行结构化说明，但不影响当前边界正确性。

---

## 15. Skill / ToolGroup / Model / Learning / Evolution 链路检查

### 15.1 Skill 直显链路

已具备协议链：

```text
SkillReference / SkillRegistry / SkillQuery / SkillExposure / SkillFlow / SkillBoundary
→ Tool / ToolGroup / ToolBinding / ToolRelease
→ ModelEnvelope / ModelToolCallEnvelope
→ Observation / Evidence / ModelFeedback / ModelReflection
```

未发现恢复旧能力包主链。

### 15.2 ToolGroup 链路

`tool_group_ports.py`、`tool_binding_ports.py`、`tool_release_ports.py` 存在，且只定义 ToolGroup / ToolBinding / ToolRelease 协议，不真实释放工具，不真实授予执行权。ToolGroup 没有被实现为旧 AbilityPackage。

### 15.3 ModelPort 链路

`model_ports.py`、`model_envelope_ports.py`、`model_feedback_ports.py`、`model_reflection_ports.py` 存在，且只定义模型输入输出、信封、反馈、反思协议；未发现模型客户端调用、prompt 构造器或 Skill 选择器实现。

### 15.4 自我学习 / 自我迭代 / 自我进化链路

`learning_ports.py`、`self_learning_ports.py`、`self_iteration_ports.py`、`evolution_ports.py` 与第八阶段 `validation_ports.py`、`candidate_ports.py`、`change_ports.py`、`experiment_ports.py` 已形成候选、证据、边界、验证、实验和回退提示协议。

但 `candidate_ports.py` 内 `CandidatePromotionHint` 被重复定义覆盖，导致统一候选晋升对象缺少 `iteration_candidate` 与 `evolution_candidate` 字段。该问题削弱“学习 / 迭代 / 进化 → 统一候选晋升提示”的协议完整性，判 P1。

---

## 16. 第八阶段横切模块检查

| 横切模块 | 文件存在 | 端口抽象性 | 真实能力下沉 | 备注 |
|---|---|---|---|---|
| Validation | 通过 | 通过 | 未发现 | 与 Candidate 存在晋升提示命名重复。 |
| Schedule | 通过 | 通过 | 未发现 | 只表达调度、触发、定时、节律、延后行动提示。 |
| StateContinuity | 通过 | 通过 | 未发现 | 使用 L0 `RuntimeStateRef`，人工判定不是旧 Runtime 主循环。 |
| ActionEffect | 通过 | 通过 | 未发现 | 只表达行动、副作用、事务、补偿、删除边界。 |
| SecurityBoundary | 通过 | 通过 | 未发现 | 只表达秘密、凭据、隐私、外露边界，不读取真实密钥。 |
| ComponentRegistry | 通过 | 通过 | 未发现 | 只表达组件、包、插件 manifest 与隔离边界，不加载插件。 |
| CompatibilityMigration | 通过 | 通过 | 未发现 | 只表达兼容与迁移协议，不执行迁移。 |
| Candidate | 通过 | 通过 | 未发现 | 存在 P1：`CandidatePromotionHint` 内部重复定义覆盖。 |
| Change | 通过 | 通过 | 未发现 | 与 Candidate / Validation / Experiment 存在证据、复核、回退提示层级重叠。 |
| Experiment | 通过 | 通过 | 未发现 | 只表达实验设计、观察、结果、比较、回退提示。 |

---

## 17. P0 问题清单

未发现 P0。

---

## 18. P1 问题清单

### P1-01：`candidate_ports.py` 内部 `CandidatePromotionHint` 重复定义并覆盖前定义

位置：

- `tiangong_kernel/l1_ports/candidate_ports.py:90`
- `tiangong_kernel/l1_ports/candidate_ports.py:150`

第一处定义包含：

```python
candidate_ref: ResourceRef
learning_candidate: LearningCandidate | None = None
iteration_candidate: IterationCandidate | None = None
evolution_candidate: EvolutionCandidate | None = None
validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
```

第二处定义同名覆盖第一处，实际导入后可见的 `CandidatePromotionHint` 只包含：

```python
learning_candidate: LearningCandidate | None = None
candidate_ref: ResourceRef | None = None
validation_refs: tuple[ValidationRef, ...] = field(default_factory=tuple)
verification_refs: tuple[VerificationRef, ...] = field(default_factory=tuple)
```

影响：

1. 当前测试通过，但这是测试覆盖盲区；`vars(ports)` 只看到后一个类，无法发现前一个类已被覆盖。
2. `iteration_candidate` 与 `evolution_candidate` 在统一候选晋升对象上丢失。
3. 自我迭代 / 自我进化候选进入统一候选晋升链的协议不完整。
4. 与 L1 最高口径中“自我学习 / 自我迭代 / 自我进化只以候选、意图、证据、边界、验证引用、回滚提示存在”的链路要求不完全一致。

建议修复方向：

- 合并两处定义，保留统一对象需要的 `learning_candidate`、`iteration_candidate`、`evolution_candidate`、`candidate_ref`、`validation_refs`、`verification_refs`。
- 明确 `candidate_ref` 是否必须存在；建议作为统一候选对象主引用时保持必填，除非设计上允许匿名候选草稿。
- 新增 AST 测试：同一模块不得出现重复顶层类名。
- 新增候选专项测试：`CandidatePromotionHint.__annotations__` 必须包含 `learning_candidate`、`iteration_candidate`、`evolution_candidate`。

---

## 19. P2 问题清单

### P2-01：`CandidatePromotionHint*` 在 `validation_ports.py` 与 `candidate_ports.py` 跨模块重复命名

位置：

- `tiangong_kernel/l1_ports/validation_ports.py:46`、`:275`、`:282`、`:385`
- `tiangong_kernel/l1_ports/candidate_ports.py:90/150`、`:161`、`:217`、`:272`

影响：命名上存在双入口：一个偏验证后的晋升提示，一个偏统一候选生命周期提示。模块命名空间可避免直接覆盖，但对后续 L2-L6 使用者不够清晰。冻结前建议命名消歧，例如：

- `ValidationPromotionHint` / `ValidationPromotionHintPort`
- `CandidatePromotionHint` / `CandidatePromotionHintPort`

或者保留同名但在总端口索引中明确两个入口的边界。

### P2-02：测试覆盖未覆盖重复顶层类名 / 覆盖式定义

现有测试能检查抽象性、返回类型、dataclass 参数、禁止项，但没有 AST 级“同一模块重复类名”检测，导致 P1 未被测试发现。

建议新增：

- `tests/test_l1_no_duplicate_public_class_names.py`
- `tests/test_l1_phase8_candidate_promotion_hint_shape.py`

### P2-03：`__init__.py` 导出策略仍停留在第一阶段

`tiangong_kernel/l1_ports/__init__.py` 仅导出第一阶段公共骨架。后续阶段模块需要通过子模块 import。该策略可以成立，但需要在冻结前明确：

- 继续只导出公共骨架；或
- 增加分阶段显式导出清单；或
- 提供 `ports_index` / `module_index` 文档，不通过 `__init__` 扩大公共 API。

### P2-04：端口方法动词命名不一致

存在 `request_...`、`submit_...`、`describe_...`、`declare_...` 等多套动词。当前不破坏测试，但会影响后续 L3 编排与 L6 子系统调用的一致性。

建议稳定口径：

- `describe_*`：只返回边界说明 / 描述。
- `request_*`：提交请求型意图。
- `submit_*`：提交观察 / 证据 / 反馈。
- `declare_*`：声明静态边界或上下文。

### P2-05：L0 Ref 使用策略未完全统一

候选对象主要使用 `ResourceRef` 表达候选引用；组件注册部分使用 `ComponentRef` / `PackageRef` 等专用 Ref。当前不构成错误，但冻结前应明确候选引用策略。

### P2-06：Validation / Candidate / Change / Experiment 中 Evidence / Review / Hint 层级有重叠

四个模块均有证据、复核、提示、回退类协议。当前是横切收口阶段自然结果，但后续应明确层级：

```text
CandidateSource → CandidateEvidence → ChangeEvidence / ExperimentObservation → Validation / Verification → Promotion / Rejection Hint
```

### P2-07：缺少 L1 总端口索引与 L2-L6 引用矩阵

`docs/l1_stability_repair_pending_zh.md` 已记录该缺口。建议冻结前补齐：

1. L1 总端口索引：按控制面 / 执行面 / 观察面 / 横切治理分组。
2. L1 到 L2-L6 引用矩阵：列出后续层可引用哪些端口，不允许反向污染 L1。
3. 旧架构迁移兼容说明：明确新版不恢复旧能力包体系。

### P2-08：侧载文档与 zip 内同名文档不完全一致

上传到 `/mnt/data` 的侧载 `l1_phase8_development_log_zh.md`、`l1_phase8_closure_report_zh.txt` 与 zip 内 `docs/` 同名文件内容不一致。虽然不影响源码测试，但会影响归档一致性。建议修复员在最终交付时统一文档来源。

---

## 20. P3 问题清单

### P3-01：zip 内 `design/` 下存在乱码长文件名

zip 可正常解压，但 `project/design/` 下存在乱码文件名，且包内有 `sanitized_long_filename_ee371242e542.txt`。建议稳定性整修阶段清理为正常中文或 ASCII 文件名。

### P3-02：`RuntimeContextPort` / `RuntimeStateRef` 需要文档说明

人工判断这些不是旧 Runtime 主循环，但由于新版口径强调不恢复旧核心概念，建议在总端口索引中注明：`RuntimeContext` 仅表示运行上下文协议，不是旧神经系统 Runtime 或调度循环。

### P3-03：部分第八阶段端口 docstring 为单行长句

不影响语义和测试，但可读性较弱，建议在稳定性整修中统一为多行结构：职责 / 输入输出 / 不做什么 / L2-L6 关系。

### P3-04：测试中的源码静态扫描逻辑分散

多个测试文件各自 `Path(ports.__file__).read_text(...)` 扫描禁止项。建议抽到测试 helper，减少重复，但不影响当前质量判断。

---

## 21. 给修复员的修复输入清单

修复员应读取并优先处理：

1. 本报告：`docs/l1_full_quality_audit_report_zh.md`
2. 摘要：`docs/l1_full_quality_audit_summary_zh.txt`
3. 当前源码：`tiangong_kernel/l1_ports/candidate_ports.py`
4. 相关源码：`tiangong_kernel/l1_ports/validation_ports.py`
5. 当前候选测试：`tests/test_l1_phase8_candidate_ports.py`
6. 当前验证测试：`tests/test_l1_phase8_validation_ports.py`
7. 稳定性待办：`docs/l1_stability_repair_pending_zh.md`

---

## 22. 建议修复顺序

1. 修复 P1：合并或消歧 `candidate_ports.py` 内重复 `CandidatePromotionHint`，恢复学习 / 迭代 / 进化三类候选字段。
2. 新增 AST 测试，禁止同一模块重复顶层类名。
3. 新增候选专项测试，断言 `CandidatePromotionHint` 必含 `learning_candidate`、`iteration_candidate`、`evolution_candidate`，并校验 `CandidatePromotionHintRequest.payload` 指向正确对象。
4. 决定 `validation_ports.py` 与 `candidate_ports.py` 跨模块同名 `CandidatePromotionHint*` 是否保留；若保留，补总端口索引解释；若不保留，改名消歧。
5. 整理 `__init__.py` 导出策略或补端口索引，不建议盲目把 200+ 端口全部平铺导出。
6. 统一动词命名口径，至少补文档说明。
7. 补 L1 总端口索引、L1→L2-L6 引用矩阵、旧架构迁移兼容说明。
8. 清理乱码设计文件名，统一侧载文档与 zip 内 docs。
9. 复跑：
   - `python3 -m compileall -q tiangong_kernel tests`
   - `python3 -m pytest -q tests`
   - 必测项逐项测试
   - zip 解压 / 重新打包 / 再解压闭环验证。

---

## 23. 未能完成的审查项及原因

1. **未做独立 L0 hash 对比**：用户本轮只提供 L1 第 8 阶段交接 zip，未额外提供独立 L0 最终归档包或 L1 第 1-7 阶段基线包。因此不能跨包证明 L0 与最终基线完全一致。
2. **未运行真实外部能力测试**：按 L1 定位，本层不得实现真实外部能力，因此不应运行模型、工具、网络、数据库、插件宿主等真实能力测试。
3. **未修改源码**：本次身份是质检员，只生成报告，不做修复。

---

## 24. 最终判定

| 项 | 判定 |
|---|---|
| P0 数量 | 0 |
| P1 数量 | 1 |
| P2 数量 | 8 |
| P3 数量 | 4 |
| 是否建议进入修复阶段 | 是 |
| 是否建议冻结 L1 | 否 |
| 是否修改源码 | 否 |

**最终结论：L1 第 1-8 阶段整体工程包完整、测试通过、协议层边界基本成立；但存在 1 个 P1，冻结前必须修复。**
