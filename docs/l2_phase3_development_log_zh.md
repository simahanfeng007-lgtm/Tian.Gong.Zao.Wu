# 天工造物 L2 第 3 阶段开发日志

生成日期：2026-06-03

## 1. 阶段目标

本阶段只开发 L2 生命体状态层第三阶段：Skill / ToolGroup / Model / Action 状态。目标是在 L2 第一阶段基础状态骨架与第二阶段运行连续性状态之上，新增执行面主链状态对象，让后续 L3 可以稳定表达：

- Skill 对模型或任务的可见、选择、激活、失败状态；
- ToolGroup 的声明、可见、释放、租约状态；
- ToolIntent 的来源、参数摘要、边界状态和动作意图引用；
- Model 请求、响应、反馈、反思状态；
- ActionIntent 与 EffectObservation 的引用链。

本阶段不实现任何选择、释放、调用、执行、调度、恢复、学习、迭代或晋升逻辑。

## 2. 前置检查

已使用输入：

1. L1 最终冻结归档基线。
2. L2 第一阶段交付工程。
3. L2 第二阶段交付工程。
4. L2 第三阶段工程员提示词。

前置检查结果：

| 检查项 | 结果 |
|---|---|
| `tiangong_kernel/l0_primitives/` | 存在 |
| `tiangong_kernel/l1_ports/` | 存在 |
| `tiangong_kernel/l2_state/` | 存在 |
| L2 第一阶段源码与文档 | 存在 |
| L2 第二阶段源码与文档 | 存在 |
| L1 完整 pytest 日志 | 存在，显示 326 passed |
| L0 hash 比对 | 无新增、无删除、无变更 |
| L1 P0/P1 | P0/P1 为 0 |
| L2 第一阶段专项测试 | 8 passed |
| L2 第二阶段专项测试 | 13 passed |

结论：未触发停止条件，可以进入 L2 第 3 阶段开发。

## 3. 新增源码

新增第三阶段源码文件：

- `tiangong_kernel/l2_state/skill_state.py`
- `tiangong_kernel/l2_state/tool_group_state.py`
- `tiangong_kernel/l2_state/tool_intent_state.py`
- `tiangong_kernel/l2_state/model_state.py`
- `tiangong_kernel/l2_state/action_effect_state.py`

更新文件：

- `tiangong_kernel/l2_state/__init__.py`：新增第三阶段公开对象稳定导出。

## 4. 新增状态对象

Skill 状态：

- `SkillVisibilityStatus`
- `SkillSelectionStatus`
- `SkillActivationStatus`
- `SkillFailureKind`
- `SkillVisibilityState`
- `SkillSelectionState`
- `SkillActivationState`
- `SkillFailureState`

ToolGroup 状态：

- `ToolGroupDeclarationStatus`
- `ToolGroupVisibilityStatus`
- `ToolGroupReleaseStatus`
- `ToolGroupLeaseStatus`
- `ToolGroupDeclarationState`
- `ToolGroupVisibilityState`
- `ToolGroupReleaseState`
- `ToolGroupLeaseState`

ToolIntent 状态：

- `ToolIntentSource`
- `ToolIntentStatus`
- `ToolIntentBoundaryStatus`
- `ToolIntentState`
- `ToolIntentBoundaryState`

Model 状态：

- `ModelRequestStatus`
- `ModelResponseStatus`
- `ModelFeedbackKind`
- `ModelReflectionStatus`
- `ModelRequestState`
- `ModelResponseState`
- `ModelFeedbackState`
- `ModelReflectionState`

Action / Effect 状态：

- `ActionIntentSource`
- `ActionIntentStatus`
- `EffectObservationStatus`
- `ActionIntentState`
- `EffectObservationState`

## 5. 主链承接

第三阶段可以形成以下纯引用链：

`RunState -> TaskState -> SkillVisibilityState -> SkillSelectionState -> SkillActivationState -> ToolGroupDeclarationState -> ToolGroupVisibilityState -> ToolGroupReleaseState -> ToolGroupLeaseState -> ModelRequestState -> ModelResponseState -> ToolIntentState -> ToolIntentBoundaryState -> ActionIntentState -> EffectObservationState -> ModelFeedbackState -> ModelReflectionState`

该链只创建不可变状态对象，只保存引用、状态码、证据、审计和摘要字段，不执行任何业务动作。

## 6. 新增测试

新增第三阶段测试文件：

- `tests/test_l2_phase3_imports.py`
- `tests/test_l2_phase3_frozen_slots.py`
- `tests/test_l2_phase3_serialization.py`
- `tests/test_l2_phase3_skill_chain.py`
- `tests/test_l2_phase3_tool_group_chain.py`
- `tests/test_l2_phase3_tool_intent_boundary.py`
- `tests/test_l2_phase3_model_state_no_call.py`
- `tests/test_l2_phase3_action_effect_refs.py`
- `tests/test_l2_phase3_main_chain_refs.py`
- `tests/test_l2_phase3_no_execution_logic.py`
- `tests/test_l2_phase3_no_real_io.py`
- `tests/test_l2_phase3_no_upper_layer_imports.py`
- `tests/test_l2_phase3_chinese_docstrings.py`
- `tests/test_l2_phase3_phase1_phase2_compatibility.py`

覆盖内容：

- 第三阶段模块和包入口可导入；
- 第三阶段公开 dataclass 均 frozen + slots，字段不可修改；
- 第三阶段对象可稳定序列化和 stable hash；
- Skill、ToolGroup、ToolIntent、Model、Action/Effect 状态链可组合；
- 完整主链引用可组合；
- 第三阶段源码无执行方法、无真实 IO、无上层导入；
- 第三阶段模块和公开类具备中文 docstring 与边界说明；
- 第一阶段和第二阶段兼容。

## 7. 前置阶段兼容修复

无。

本阶段未修改 L0、L1、L2 第一阶段源码、L2 第二阶段源码，也未修改第一阶段或第二阶段测试。

## 8. 测试命令与结果

当前环境未提供独立 `pytest` 命令入口，实际使用 `python -m pytest`。

已运行：

```powershell
python -m compileall -q tiangong_kernel tests
```

结果：通过。

已运行第一阶段专项：

```powershell
$phase1 = Get-ChildItem -LiteralPath tests -Filter 'test_l2_phase1_*.py' | ForEach-Object { $_.FullName }
python -m pytest -q $phase1
```

结果：`8 passed in 1.03s`

已运行第二阶段专项：

```powershell
$phase2 = Get-ChildItem -LiteralPath tests -Filter 'test_l2_phase2_*.py' | ForEach-Object { $_.FullName }
python -m pytest -q $phase2
```

结果：`13 passed in 1.22s`

已运行第三阶段专项：

```powershell
$phase3 = Get-ChildItem -LiteralPath tests -Filter 'test_l2_phase3_*.py' | ForEach-Object { $_.FullName }
python -m pytest -q $phase3
```

结果：`18 passed in 1.42s`

已运行全部 L2 阶段专项：

```powershell
$l2 = Get-ChildItem -LiteralPath tests -Filter 'test_l2_phase*.py' | ForEach-Object { $_.FullName }
python -m pytest -q $l2
```

结果：`39 passed in 2.31s`

已运行完整回归：

```powershell
python -m pytest -q
```

结果：`365 passed in 3.70s`

## 9. 边界确认

- 未修改 L0 源码语义。
- 未修改 L1 源码语义。
- 未导入 L3-L6。
- 未恢复旧能力包体系、CapabilityPort、AbilityPackagePort、“神枢”新版核心概念或旧 Runtime 主链。
- 未新增 ModelPort、Skill 选择器、ToolGroup 释放器、Tool 调用器、模型调用器、调度器、运行循环或插件宿主。
- 未实现真实 IO、网络访问、subprocess、环境访问、数据库访问或用户文件读写。
- 未生产 Skill、Tool 或能力包。
- 未让状态对象持有函数、callable、模型客户端或工具实例。
- 未进入 L2 第 4 阶段及以后内容。

## 10. 未做事项

- 未开发 L2 第 4 阶段控制面、资源、环境、安全状态。
- 未开发 L2 第 5-8 阶段对象。
- 未实现真实 Skill 选择、工具组释放、工具调用、模型调用、动作执行、效果采集、调度、恢复、学习、候选晋升或插件加载。

## 11. 阶段结论

L2 第 3 阶段 Skill / ToolGroup / Model / Action 状态已完成。第一阶段、第二阶段、第三阶段专项、全部 L2 专项、compileall 和完整 pytest 均通过。

建议：可以基于本交付包进入 L2 第 4 阶段。
