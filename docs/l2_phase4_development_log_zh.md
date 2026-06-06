# 天工造物 L2 第四阶段开发日志

生成日期：2026-06-03

## 阶段目标

第四阶段新增 L2 控制面、边界、风险/策略/裁决引用、资源、环境、安全状态对象。所有对象均为纯状态对象，只记录外部边界层或控制面已经给出的事实，不执行真实风险评分、权限裁决、资源计量、环境探测、安全扫描、模型调用或工具调用。

## 前置检查

- L2 第一阶段测试：8 passed。
- L2 第二阶段测试：13 passed。
- L2 第三阶段测试：18 passed。
- 第一至第三阶段回归：39 passed。
- L1 最终归档记录：326 passed。
- L0 hash 归档记录：58 个文件，无新增、无删除、无变更。

## 新增源码

- `tiangong_kernel/l2_state/control_state.py`
- `tiangong_kernel/l2_state/boundary_state.py`
- `tiangong_kernel/l2_state/risk_decision_state.py`
- `tiangong_kernel/l2_state/resource_state.py`
- `tiangong_kernel/l2_state/environment_state.py`
- `tiangong_kernel/l2_state/security_state.py`

## 修改源码

- `tiangong_kernel/l2_state/__init__.py`
  - 仅新增第四阶段对象导入和 `__all__` 导出。
  - 未删除或改名第一、第二、第三阶段公开导出。

## 新增测试

- `tests/test_l2_phase4_imports.py`
- `tests/test_l2_phase4_frozen_slots.py`
- `tests/test_l2_phase4_serialization.py`
- `tests/test_l2_phase4_control_state.py`
- `tests/test_l2_phase4_boundary_state.py`
- `tests/test_l2_phase4_boundary_block_degrade_alternative.py`
- `tests/test_l2_phase4_risk_decision_state_no_scoring.py`
- `tests/test_l2_phase4_a5_status_only.py`
- `tests/test_l2_phase4_policy_reference_state.py`
- `tests/test_l2_phase4_resource_budget_quota_rate_limit.py`
- `tests/test_l2_phase4_environment_sandbox_no_probe.py`
- `tests/test_l2_phase4_security_privacy_credential_redaction.py`
- `tests/test_l2_phase4_phase3_integration_refs.py`
- `tests/test_l2_phase4_no_execution_logic.py`
- `tests/test_l2_phase4_no_real_io.py`
- `tests/test_l2_phase4_no_upper_layer_imports.py`
- `tests/test_l2_phase4_chinese_docstrings.py`
- `tests/test_l2_phase4_phase1_phase2_phase3_compatibility.py`

## 状态对象摘要

### ControlState

新增 `ControlPlaneStatus`、`ControlPlaneMode`、`ControlSignalStatus`、`ControlPlaneState`、`ControlSignalState`、`ControlConstraintState`。

作用：记录运行、任务、Skill、ToolIntent、ActionIntent、ModelFeedback 关联的控制面模式、控制信号和控制约束引用。

边界：不应用控制模式，不路由任务，不执行控制信号，不实现约束拦截器。

### BoundaryState

新增 `BoundaryCheckStatus`、`BoundaryBlockKind`、`BoundaryDegradeKind`、`BoundaryAlternativeKind`、`BoundaryCheckState`、`BoundaryBlockedState`、`BoundaryDegradedState`、`BoundaryAlternativeState`。

作用：记录边界检查、阻断、降级和替代路径事实。

边界：`PASSED`、`BLOCKED`、`DEGRADED` 等均表示外部边界层记录结果，不代表 L2 自行裁决；替代路径仅记录，不自动选择。

### RiskDecisionState

新增 `RiskDecisionStatus`、`RiskSeverityLabel`、`PolicyReferenceStatus`、`RiskDecisionState`、`PolicyReferenceState`、`DecisionRecordState`。

作用：记录 RiskView、Decision、Policy、score snapshot 等外部引用。

边界：不计算风险分数，不根据 A5 推导拦截，不执行策略匹配，不实现 Decision 引擎。

### ResourceState

新增 `ResourceStatus`、`ResourceKind`、`ResourceBudgetState`、`QuotaState`、`RateLimitState`、`ResourceLeaseState`、`ResourcePressureState`。

作用：记录外部给出的预算、配额、限速、租约和资源压力事实。

边界：不读取真实 CPU / 内存 / 磁盘 / 网络状态，不扣减预算，不 sleep，不重试，不续租或撤销真实租约。

### EnvironmentState

新增 `EnvironmentStatus`、`EnvironmentKind`、`SandboxStatus`、`EnvironmentState`、`SandboxState`、`ExternalWorldReferenceState`。

作用：记录环境、沙箱、外部世界对象引用及其状态标签。

边界：不读取环境变量，不探测系统路径，不访问沙箱，不访问外部世界。

### SecurityState

新增 `SecurityStatus`、`PrivacyStatus`、`CredentialStatus`、`TrustBoundaryStatus`、`SecurityBoundaryState`、`PrivacyCredentialState`、`TrustBoundaryState`、`SecretReferenceState`。

作用：记录安全边界、隐私、凭据、密钥引用和信任边界状态。

边界：不执行安全扫描，不读取密钥，不验证身份；`PrivacyCredentialState` 和 `SecretReferenceState` 默认并强制 `redacted=True`、`value_absent=True`。

## 前置阶段兼容修复

无。

## 明确未做

- 未开发 L2 第五阶段及以后对象。
- 未新增 ModelPort、Skill 选择器、ToolGroup 释放器、Tool 调用器、模型调用器、调度器、运行循环或插件宿主。
- 未恢复旧能力包、CapabilityPort、AbilityPackagePort、“神枢”或旧 Runtime 主链。
- 未实现真实 IO、网络访问、subprocess、风险评分、权限裁决、确认票据、资源计量、环境探测、安全扫描或凭据读取。
