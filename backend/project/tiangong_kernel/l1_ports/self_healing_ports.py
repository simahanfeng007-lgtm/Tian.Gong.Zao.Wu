"""L1 自愈系统主链端口协议。

本模块只定义失败诊断、恢复计划意图、自愈生命周期、恢复后验证和复盘记录协议；
不执行诊断、不恢复状态、不运行测试、不写审计。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class FailureDiagnosisRequest:
    """失败诊断请求。"""

    request_ref: TypedRef
    failure_ref: TypedRef | None = None
    trace_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.request_only, "FailureDiagnosisRequest.request_only")
        if not self.schema_version:
            raise ValueError("FailureDiagnosisRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class FailureDiagnosisResponse:
    """失败诊断响应。"""

    response_ref: TypedRef
    diagnosis_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    root_cause_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    performs_diagnosis: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.response_only, "FailureDiagnosisResponse.response_only")
        _false(self.performs_diagnosis, "FailureDiagnosisResponse.performs_diagnosis")
        if not self.schema_version:
            raise ValueError("FailureDiagnosisResponse.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryPlanIntentRequest:
    """恢复计划意图请求。"""

    request_ref: TypedRef
    diagnosis_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    checkpoint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    transaction_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    regression_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.request_only, "RecoveryPlanIntentRequest.request_only")
        if not self.schema_version:
            raise ValueError("RecoveryPlanIntentRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class RecoveryPlanIntentResponse:
    """恢复计划意图响应。"""

    response_ref: TypedRef
    recovery_plan_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    executes_recovery: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.response_only, "RecoveryPlanIntentResponse.response_only")
        _false(self.executes_recovery, "RecoveryPlanIntentResponse.executes_recovery")
        if not self.schema_version:
            raise ValueError("RecoveryPlanIntentResponse.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfHealingLifecycleRequest:
    """自愈生命周期请求。"""

    request_ref: TypedRef
    failure_ref: TypedRef | None = None
    diagnosis_ref: TypedRef | None = None
    recovery_plan_ref: TypedRef | None = None
    boundary_review_ref: TypedRef | None = None
    request_only: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.request_only, "SelfHealingLifecycleRequest.request_only")
        if not self.schema_version:
            raise ValueError("SelfHealingLifecycleRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class SelfHealingLifecycleResponse:
    """自愈生命周期响应。"""

    response_ref: TypedRef
    lifecycle_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    executes_lifecycle: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.response_only, "SelfHealingLifecycleResponse.response_only")
        _false(self.executes_lifecycle, "SelfHealingLifecycleResponse.executes_lifecycle")
        if not self.schema_version:
            raise ValueError("SelfHealingLifecycleResponse.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PostRecoveryValidationRequest:
    """恢复后验证请求。"""

    request_ref: TypedRef
    recovery_result_ref: TypedRef | None = None
    validation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    regression_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.request_only, "PostRecoveryValidationRequest.request_only")
        if not self.schema_version:
            raise ValueError("PostRecoveryValidationRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PostRecoveryValidationResponse:
    """恢复后验证响应。"""

    response_ref: TypedRef
    validation_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    regression_outcome_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    runs_validation: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.response_only, "PostRecoveryValidationResponse.response_only")
        _false(self.runs_validation, "PostRecoveryValidationResponse.runs_validation")
        if not self.schema_version:
            raise ValueError("PostRecoveryValidationResponse.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PostmortemRecordRequest:
    """复盘记录请求。"""

    request_ref: TypedRef
    failure_ref: TypedRef | None = None
    diagnosis_ref: TypedRef | None = None
    recovery_plan_ref: TypedRef | None = None
    validation_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    learning_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.request_only, "PostmortemRecordRequest.request_only")
        if not self.schema_version:
            raise ValueError("PostmortemRecordRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class PostmortemRecordResponse:
    """复盘记录响应。"""

    response_ref: TypedRef
    postmortem_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    writes_postmortem_store: bool = False
    schema_version: str = "0.1"

    def __post_init__(self) -> None:
        _true(self.response_only, "PostmortemRecordResponse.response_only")
        _false(self.writes_postmortem_store, "PostmortemRecordResponse.writes_postmortem_store")
        if not self.schema_version:
            raise ValueError("PostmortemRecordResponse.schema_version cannot be empty")


class FailureDiagnosisPort(ABC):
    """失败诊断端口协议。"""

    @abstractmethod
    def describe_failure_diagnosis(self, request: FailureDiagnosisRequest, trace: TraceContext) -> PortResult[FailureDiagnosisResponse]:
        """描述失败诊断引用。"""


class RecoveryPlanIntentPort(ABC):
    """恢复计划意图端口协议。"""

    @abstractmethod
    def describe_recovery_plan_intent(self, request: RecoveryPlanIntentRequest, trace: TraceContext) -> PortResult[RecoveryPlanIntentResponse]:
        """描述恢复计划意图引用。"""


class SelfHealingLifecyclePort(ABC):
    """自愈生命周期端口协议。"""

    @abstractmethod
    def describe_self_healing_lifecycle(self, request: SelfHealingLifecycleRequest, trace: TraceContext) -> PortResult[SelfHealingLifecycleResponse]:
        """描述自愈生命周期引用。"""


class PostRecoveryValidationPort(ABC):
    """恢复后验证端口协议。"""

    @abstractmethod
    def describe_post_recovery_validation(self, request: PostRecoveryValidationRequest, trace: TraceContext) -> PortResult[PostRecoveryValidationResponse]:
        """描述恢复后验证引用。"""


class PostmortemPort(ABC):
    """复盘记录端口协议。"""

    @abstractmethod
    def describe_postmortem_record(self, request: PostmortemRecordRequest, trace: TraceContext) -> PortResult[PostmortemRecordResponse]:
        """描述复盘记录引用。"""
