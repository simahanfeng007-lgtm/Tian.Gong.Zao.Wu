# L0 第 3 阶段开发日志：边界与行动

- 日期：2026-06-03
- 范围：actor.py、scope.py、goal.py、plan.py、action.py、effect.py、decision.py、risk.py、grant_lease.py、self_identity.py
- 层级：L0 零依赖原语层

## 目标

建立行为主体、范围边界、目标、计划、行动意图、副作用、裁决事实、风险视图、授权租约以及自我身份对象族。

## 已完成模块与对象

- `actor.py`：主体引用与主体类别。
- `scope.py`：范围引用、范围边界与核心范围。
- `goal.py`：目标引用、状态、优先级、成功/失败条件引用。
- `plan.py`：计划引用、状态、优先级与来源引用。
- `action.py`：行动引用、状态与意图。
- `effect.py`：副作用引用、边界、影响、可逆性与结果引用。
- `decision.py`：裁决引用、裁决种类、原因与裁决事实。
- `risk.py`：风险引用、等级、信号与风险视图。
- `grant_lease.py`：授予、租约与权限窗口事实。
- `self_identity.py`：`SelfRef`、`IdentityRef`、`ContinuityRef`、`BoundaryRef`、`OwnershipRef`、`AffiliationRef`。

## 设计取舍

- `DecisionKind.ALLOW/DENY` 只记录外部裁决事实，不实现 allow/deny 策略。
- `RiskView` 只保存风险视图，不计算风险分数。
- `GrantRef` 与 `LeaseRef` 只表达授予/租约事实，不签发真实权限。
- `self_identity.py` 只表达自我、身份、连续性、边界、所有权、归属引用，不做认证、归属推理或关系图计算。

## 本轮修复记录

- 新增 `self_identity.py`，补齐设计文件要求的 Self/Identity/Continuity 对象族。
- 更新 `tiangong_kernel/l0_primitives/__init__.py` 导出。
- 新增 `tests/test_l0_self_identity.py`。
- 为阶段 3 模块补中文边界说明与核心类 docstring。

## 测试命令与结果

- `python -m pytest tests/test_l0_self_identity.py -q`：2 passed。
- `python -m pytest tests/test_l0_phase3* -q`：5 passed。

## 未做事项

- 未实现 ActorLoop、ToolExecutor、权限引擎、风险评分、计划执行或真实工具调用。
