"""L0 失败事实原语，只表达故障、失败、根因、诊断与证据引用；不自愈、不重试、不回滚。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef


class FailureKind(str, Enum):
    """FailureKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    GOAL_FAILURE = "goal_failure"
    PLAN_FAILURE = "plan_failure"
    EFFECT_FAILURE = "effect_failure"
    TOOL_FAILURE = "tool_failure"
    ADAPTER_FAILURE = "adapter_failure"
    POLICY_FAILURE = "policy_failure"
    MEMORY_FAILURE = "memory_failure"
    CONTEXT_FAILURE = "context_failure"
    RESOURCE_FAILURE = "resource_failure"
    CONTRACT_FAILURE = "contract_failure"
    RECOVERY_FAILURE = "recovery_failure"
    UNKNOWN = "unknown"


class FaultKind(str, Enum):
    """FaultKind 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    MODEL_REASONING_FAULT = "model_reasoning_fault"
    CONTEXT_BOUNDARY_FAULT = "context_boundary_fault"
    AUTHORIZATION_FAULT = "authorization_fault"
    TOOL_INVOCATION_FAULT = "tool_invocation_fault"
    ADAPTER_COMPATIBILITY_FAULT = "adapter_compatibility_fault"
    DEPENDENCY_FAULT = "dependency_fault"
    ENVIRONMENT_FAULT = "environment_fault"
    STATE_TRANSITION_FAULT = "state_transition_fault"
    SCHEMA_VERSION_FAULT = "schema_version_fault"
    RESOURCE_EXHAUSTION_FAULT = "resource_exhaustion_fault"
    EXTERNAL_SERVICE_FAULT = "external_service_fault"
    UNKNOWN = "unknown"


class FailureState(str, Enum):
    """FailureState 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    DETECTED = "detected"
    DIAGNOSING = "diagnosing"
    DIAGNOSED = "diagnosed"
    RECOVERY_PLANNED = "recovery_planned"
    RECOVERING = "recovering"
    RECOVERED = "recovered"
    UNRECOVERABLE = "unrecoverable"
    ESCALATED = "escalated"
    ARCHIVED = "archived"
    UNKNOWN = "unknown"


class FailureSeverity(str, Enum):
    """FailureSeverity 的 L0 枚举，只表达稳定事实，不实现上层算法或真实执行。"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class FailureRef:
    """FailureRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: FailureKind = FailureKind.UNKNOWN
    state: FailureState = FailureState.UNKNOWN
    severity: FailureSeverity = FailureSeverity.UNKNOWN
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("FailureRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class FaultScope:
    """FaultScope 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    scope_ref: TypedRef
    label: str = "unknown"

    def __post_init__(self) -> None:
        if not self.label:
            raise ValueError("FaultScope.label cannot be empty")


@dataclass(frozen=True, slots=True)
class FaultRef:
    """FaultRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    kind: FaultKind = FaultKind.UNKNOWN
    scope: FaultScope | None = None
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("FaultRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DiagnosisConfidence:
    """DiagnosisConfidence 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: float

    def __post_init__(self) -> None:
        if self.value < 0.0 or self.value > 1.0:
            raise ValueError("DiagnosisConfidence.value must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class CriticalStepRef:
    """CriticalStepRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    step_type: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.step_type:
            raise ValueError("CriticalStepRef.step_type cannot be empty")
        if not self.schema_version:
            raise ValueError("CriticalStepRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RootCauseRef:
    """RootCauseRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    cause_type: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.cause_type:
            raise ValueError("RootCauseRef.cause_type cannot be empty")
        if not self.schema_version:
            raise ValueError("RootCauseRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class FailureEvidenceRef:
    """FailureEvidenceRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    evidence_type: str = "unknown"
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.evidence_type:
            raise ValueError("FailureEvidenceRef.evidence_type cannot be empty")
        if not self.schema_version:
            raise ValueError("FailureEvidenceRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryDiagnosisRef:
    """RecoveryDiagnosisRef 的 L0 不可变事实对象，只表达稳定事实，不实现上层算法或真实执行。"""
    value: RefId
    failure_ref: FailureRef | None = None
    fault_refs: tuple[FaultRef, ...] = field(default_factory=tuple)
    confidence: DiagnosisConfidence = field(default_factory=lambda: DiagnosisConfidence(0.0))
    critical_step_ref: CriticalStepRef | None = None
    root_cause_ref: RootCauseRef | None = None
    evidence_refs: tuple[FailureEvidenceRef, ...] = field(default_factory=tuple)
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        if not self.schema_version:
            raise ValueError("RecoveryDiagnosisRef.schema_version cannot be empty")
