# 天工造物新版 L0 零依赖原语层第六阶段开发日志

生成日期：2026-06-03
阶段名称：第六阶段——治理与安全层
开发范围：仅新增 L0 治理与安全事实语言，不进入第七阶段，不实现任何上层执行逻辑。

## 一、本阶段目标

本阶段目标是在 L0 零依赖原语层中新增治理与安全层的最小事实语言，使后续 L1-L6 能引用信任、隐私、机密、合约、政策、指令、自治、价值等治理事实，同时保持 L0 的纯数据、可序列化、可哈希、不可变、无真实副作用边界。

本阶段遵守：

- L0 只允许 Python 标准库。
- 所有 dataclass 使用 `frozen=True, slots=True`。
- L0 不 import L1-L6。
- L0 不进行真实 IO、网络、模型调用、工具调用。
- L0 只定义事实语言，不实现策略引擎、安全引擎、隐私引擎、密钥管理、合约检查、指令仲裁、模式切换或价值优化。

## 二、新增模块清单

- `tiangong_kernel/l0_primitives/trust.py`
- `tiangong_kernel/l0_primitives/privacy.py`
- `tiangong_kernel/l0_primitives/secret.py`
- `tiangong_kernel/l0_primitives/contract.py`
- `tiangong_kernel/l0_primitives/policy.py`
- `tiangong_kernel/l0_primitives/instruction.py`
- `tiangong_kernel/l0_primitives/autonomy.py`
- `tiangong_kernel/l0_primitives/value.py`

同步更新：

- `tiangong_kernel/l0_primitives/__init__.py`

## 三、每个模块新增对象清单

### 1. trust.py

新增对象：

- `TrustBoundaryRef`
- `TrustBoundaryKind`
- `TrustLevel`
- `ProvenanceRef`
- `ProvenanceKind`
- `ResponsibilityChainRef`
- `AttestationRef`
- `IntegrityDigest`

边界说明：只表达信任边界、来源证明、责任链、可验证声明和完整性摘要引用事实。不实现身份认证、签名校验、加密握手或证书解析。

### 2. privacy.py

新增对象：

- `PrivacyRef`
- `ConsentRef`
- `DataClass`
- `DataSubjectRef`
- `ProcessingPurposeRef`
- `RetentionPolicyRef`
- `DataLifecycleState`
- `AccessSensitivity`
- `RedactionRef`
- `AnonymizationRef`

边界说明：只表达隐私属性、数据分类、主体、同意、处理目的、保留策略、生命周期和敏感度引用事实。不实现个人信息检测、法律规则判断、删除执行或脱敏算法。

### 3. secret.py

新增对象：

- `SecretRef`
- `SecretKind`
- `SecretState`
- `CredentialRef`
- `CredentialKind`
- `CredentialState`
- `CapabilityTokenRef`
- `TokenKind`
- `TokenState`
- `CredentialScopeRef`
- `CredentialBindingRef`
- `RevocationRef`

边界说明：只表达密钥、凭证、能力令牌、凭证范围、绑定与撤销的引用事实。不保存真实密钥值，不读取环境变量，不访问 vault，不实现加密、认证协议或令牌校验。

### 4. contract.py

新增对象：

- `ContractRef`
- `ContractKind`
- `ContractState`
- `ContractScopeRef`
- `ContractSatisfaction`
- `ContractViolationRef`
- `ContractVersionRef`
- `ContractOriginRef`

边界说明：只表达运行承诺、合约范围、满足状态、违反、版本和来源引用事实。不保存完整合约内容，不实现合约检查算法、策略执行、运行时 enforcement 或 DSL 解析。

### 5. policy.py

新增对象：

- `PolicyRef`
- `PolicyKind`
- `PolicyState`
- `NormRef`
- `NormKind`
- `GovernanceRef`
- `GovernanceDomain`
- `PolicyConflictRef`
- `EnforcementModeRef`

边界说明：只表达政策、规范、治理域、政策冲突和执行模式引用事实。不实现 Policy DSL、规则引擎、合规判断、治理流程执行或实际 allow / deny 算法。

### 6. instruction.py

新增对象：

- `InstructionRef`
- `InstructionKind`
- `InstructionAuthority`
- `InstructionSource`
- `InstructionPriority`
- `InstructionState`
- `InstructionConflictRef`
- `DirectiveRef`

边界说明：只表达观察到的指令事实、权威等级、来源、优先级、冲突和治理指令引用。不保存 system prompt 内容，不实现指令优先级仲裁、prompt injection 检测或上下文装配。

### 7. autonomy.py

新增对象：

- `AutonomyLevel`
- `AgencyLevel`
- `ControlModeRef`
- `OversightMode`
- `ControlModeState`
- `AutonomyBoundaryRef`
- `AgencyBoundaryRef`

边界说明：只表达自治等级、能动性等级、控制姿态、人类监督方式和边界引用事实。不实现模式切换、权限策略、UI 按钮、高权限模式、无双模式或自动降级算法。

### 8. value.py

新增对象：

- `ValueRef`
- `ValueKind`
- `PreferenceRef`
- `PreferenceKind`
- `PreferenceState`
- `ObjectiveRef`
- `ObjectiveKind`
- `ObjectivePriority`
- `UtilitySignalRef`
- `TradeoffRef`

边界说明：只表达价值取向、偏好、目标取向、效用信号和权衡引用事实。不实现价值观模型、偏好学习、奖励模型、伦理推理、效用优化或多目标优化。

## 四、关键设计取舍

1. 继续采用“Ref 优先”策略。治理与安全层多数对象为引用事实，不承载真实资源句柄、客户端、回调或可变对象。
2. `AutonomyLevel` 使用 `L0_MANUAL` 到 `L5_FULL_AUTONOMY`，刻意不使用 A0-A5，避免与 `RiskLevel.A5_CRITICAL` 混淆。
3. `SecretRef`、`CredentialRef`、`CapabilityTokenRef` 只保存引用、类别、状态和绑定引用，不保存任何真实秘密文本。
4. `PolicyRef`、`ContractRef`、`InstructionRef` 均只记录事实，不做解析、仲裁、执行或裁决。
5. `ValueRef`、`PreferenceRef`、`ObjectiveRef` 只记录价值和目标取向事实，不进行优化或道德判断。
6. 所有新增模块顶部均写入中文模块说明；核心 dataclass 和 Enum 均补充中文 docstring，说明职责边界与禁止事项。

## 五、明确未做事项

- 未做第七阶段或后续模块。
- 未新增 `resource.py`、`cost_budget.py`、`environment.py`、`location.py`、`tool_adapter.py`、`skill_capability.py`、`component_package.py` 等后续模块。
- 未实现安全策略引擎、隐私检测、密钥管理、合约检查器、Policy DSL、指令仲裁算法、模式切换器、价值判断算法。
- 未写 Runtime / ToolExecutor / PluginHost / ModelClient / MemorySystem / ForgettingSystem / SelfHealingSystem / HealthMonitor / PolicyEngine / SecurityEngine / PrivacyEngine 等上层系统逻辑。
- 未接触真实 IO、网络、模型、工具、密钥、证书或外部资源。

## 六、新增测试清单

- `tests/test_l0_trust.py`
- `tests/test_l0_privacy.py`
- `tests/test_l0_secret.py`
- `tests/test_l0_contract.py`
- `tests/test_l0_policy.py`
- `tests/test_l0_instruction.py`
- `tests/test_l0_autonomy.py`
- `tests/test_l0_value.py`
- `tests/test_l0_phase6_serialization.py`
- `tests/test_l0_phase6_stable_hash.py`
- `tests/test_l0_phase6_no_execution_logic.py`

## 七、测试命令

```bash
python -m compileall -q tiangong_kernel tests
python -m pytest -q tests
```

## 八、测试结果

```text
81 passed in 0.58s
```

## 九、失败测试说明与下一步建议

本阶段无失败测试。

下一步建议：开启第七阶段时再新增资源、成本预算、环境、位置、工具适配器、Skill/Capability、组件包等引用事实；继续保持 L0 只定义事实语言，不提前实现上层执行逻辑。
