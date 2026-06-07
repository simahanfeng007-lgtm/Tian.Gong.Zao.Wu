"""L3 第八阶段总收口检查对象。

本模块只表达收口检查请求、检查结果、边界合规、导入稳定、序列化稳定、快照兼容与最终冻结准备度报告。
它不触发真实修复、执行、裁决、存储或子系统调用。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class L3ClosureCheckKind(str, Enum):
    """L3 收口检查类别。"""

    IMPORT = "import"
    SERIALIZATION = "serialization"
    SNAPSHOT = "snapshot"
    BOUNDARY = "boundary"
    HANDOFF = "handoff"
    FLOW_COMPLETENESS = "flow_completeness"
    FINAL_FREEZE = "final_freeze"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_flag(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


@dataclass(frozen=True, slots=True)
class L3ClosureCheckRequest:
    """L3 总收口检查请求；不触发检查执行。"""

    request_ref: TypedRef
    requested_check_kinds: tuple[L3ClosureCheckKind, ...] = field(default_factory=tuple)
    target_stage_names: tuple[str, ...] = field(default_factory=tuple)
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.target_stage_names:
            _ensure_short_text(item, "L3ClosureCheckRequest.target_stage_names", 128)
        for kind in self.requested_check_kinds:
            if not isinstance(kind, L3ClosureCheckKind):
                raise ValueError("L3ClosureCheckRequest.requested_check_kinds must use L3ClosureCheckKind")
        _ensure_flag(self.request_only, "L3ClosureCheckRequest.request_only")
        if not self.schema_version:
            raise ValueError("L3ClosureCheckRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ClosureCheckResult:
    """L3 总收口检查结果。"""

    result_ref: TypedRef
    request_ref: TypedRef | None = None
    passed_check_kinds: tuple[L3ClosureCheckKind, ...] = field(default_factory=tuple)
    failed_check_kinds: tuple[L3ClosureCheckKind, ...] = field(default_factory=tuple)
    warning_codes: tuple[str, ...] = field(default_factory=tuple)
    readiness_score: float = 0.0
    report_only: bool = True
    no_auto_fix: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for kind in self.passed_check_kinds + self.failed_check_kinds:
            if not isinstance(kind, L3ClosureCheckKind):
                raise ValueError("L3ClosureCheckResult check kinds must use L3ClosureCheckKind")
        for item in self.warning_codes:
            _ensure_short_text(item, "L3ClosureCheckResult.warning_codes", 128)
        _ensure_unit_interval(self.readiness_score, "L3ClosureCheckResult.readiness_score")
        _ensure_flag(self.report_only, "L3ClosureCheckResult.report_only")
        _ensure_flag(self.no_auto_fix, "L3ClosureCheckResult.no_auto_fix")
        if not self.schema_version:
            raise ValueError("L3ClosureCheckResult.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3BoundaryComplianceReport:
    """L3 边界合规报告。"""

    report_ref: TypedRef
    compliant: bool = True
    violation_codes: tuple[str, ...] = field(default_factory=tuple)
    guarantee_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    compliance_score: float = 0.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.violation_codes:
            _ensure_short_text(item, "L3BoundaryComplianceReport.violation_codes", 128)
        _ensure_unit_interval(self.compliance_score, "L3BoundaryComplianceReport.compliance_score")
        _ensure_flag(self.report_only, "L3BoundaryComplianceReport.report_only")
        if not self.schema_version:
            raise ValueError("L3BoundaryComplianceReport.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3ImportStabilityReport:
    """L3 导入稳定性报告。"""

    report_ref: TypedRef
    imported_object_names: tuple[str, ...] = field(default_factory=tuple)
    missing_object_names: tuple[str, ...] = field(default_factory=tuple)
    duplicate_export_names: tuple[str, ...] = field(default_factory=tuple)
    stability_score: float = 0.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.imported_object_names + self.missing_object_names + self.duplicate_export_names:
            _ensure_short_text(item, "L3ImportStabilityReport names", 128)
        _ensure_unit_interval(self.stability_score, "L3ImportStabilityReport.stability_score")
        _ensure_flag(self.report_only, "L3ImportStabilityReport.report_only")
        if not self.schema_version:
            raise ValueError("L3ImportStabilityReport.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3SerializationStabilityReport:
    """L3 序列化稳定性报告。"""

    report_ref: TypedRef
    serialized_object_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    unstable_object_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    stable_hash_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    stability_score: float = 0.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.stability_score, "L3SerializationStabilityReport.stability_score")
        _ensure_flag(self.report_only, "L3SerializationStabilityReport.report_only")
        if not self.schema_version:
            raise ValueError("L3SerializationStabilityReport.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3SnapshotCompatibilityReport:
    """L3 快照兼容报告。"""

    report_ref: TypedRef
    snapshot_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    incompatible_snapshot_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    compatibility_score: float = 0.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.compatibility_score, "L3SnapshotCompatibilityReport.compatibility_score")
        _ensure_flag(self.report_only, "L3SnapshotCompatibilityReport.report_only")
        if not self.schema_version:
            raise ValueError("L3SnapshotCompatibilityReport.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3NoExecutionGuaranteeReport:
    """L3 不执行保证报告。"""

    report_ref: TypedRef
    guarantee_items: tuple[str, ...] = ("no_model_call", "no_tool_call", "no_external_action")
    confidence: float = 1.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.guarantee_items:
            _ensure_short_text(item, "L3NoExecutionGuaranteeReport.guarantee_items", 128)
        _ensure_unit_interval(self.confidence, "L3NoExecutionGuaranteeReport.confidence")
        _ensure_flag(self.report_only, "L3NoExecutionGuaranteeReport.report_only")
        if not self.schema_version:
            raise ValueError("L3NoExecutionGuaranteeReport.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3NoDecisionGuaranteeReport:
    """L3 不裁决保证报告。"""

    report_ref: TypedRef
    guarantee_items: tuple[str, ...] = ("no_permission_result", "no_risk_result", "no_final_boundary_result")
    confidence: float = 1.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.guarantee_items:
            _ensure_short_text(item, "L3NoDecisionGuaranteeReport.guarantee_items", 128)
        _ensure_unit_interval(self.confidence, "L3NoDecisionGuaranteeReport.confidence")
        _ensure_flag(self.report_only, "L3NoDecisionGuaranteeReport.report_only")
        if not self.schema_version:
            raise ValueError("L3NoDecisionGuaranteeReport.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3NoSubsystemGuaranteeReport:
    """L3 不实现子系统保证报告。"""

    report_ref: TypedRef
    guarantee_items: tuple[str, ...] = ("no_memory_service", "no_retrieval_service", "no_learning_service", "no_affective_service")
    confidence: float = 1.0
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.guarantee_items:
            _ensure_short_text(item, "L3NoSubsystemGuaranteeReport.guarantee_items", 128)
        _ensure_unit_interval(self.confidence, "L3NoSubsystemGuaranteeReport.confidence")
        _ensure_flag(self.report_only, "L3NoSubsystemGuaranteeReport.report_only")
        if not self.schema_version:
            raise ValueError("L3NoSubsystemGuaranteeReport.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class L3FinalFreezeReadinessReport:
    """L3 最终冻结准备度报告。"""

    report_ref: TypedRef
    closure_result_ref: TypedRef | None = None
    boundary_report_ref: TypedRef | None = None
    import_report_ref: TypedRef | None = None
    serialization_report_ref: TypedRef | None = None
    snapshot_report_ref: TypedRef | None = None
    readiness_score: float = 0.0
    remaining_issue_codes: tuple[str, ...] = field(default_factory=tuple)
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.readiness_score, "L3FinalFreezeReadinessReport.readiness_score")
        for item in self.remaining_issue_codes:
            _ensure_short_text(item, "L3FinalFreezeReadinessReport.remaining_issue_codes", 128)
        _ensure_flag(self.report_only, "L3FinalFreezeReadinessReport.report_only")
        if not self.schema_version:
            raise ValueError("L3FinalFreezeReadinessReport.schema_version cannot be empty")
