"""L2 数学模型治理状态域。

本模块补齐数学模型发动机 100 分前置基础所需的注册、参数、特征、评分、
证据、校准、漂移、回放、影子、治理、冲突和遥测状态。所有对象只保存状态。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


def _unit(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


@dataclass(frozen=True, slots=True)
class MathModelGovernanceStateBase:
    """数学模型治理基础状态，只保存可审计引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    run_id: str = ""
    trace_id: str = ""
    model_id: str = ""
    model_version: str = ""
    parameter_version: str = ""
    input_snapshot_hash: str = ""
    feature_snapshot_hash: str = ""
    output_snapshot_hash: str = ""
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    adapter_ref: TypedRef | None = None
    disabled_state: str = "disabled_by_default"
    fallback_used: bool = False
    fallback_reason: str = ""
    drift_signal_ref: TypedRef | None = None
    calibration_ref: TypedRef | None = None
    created_at: str = ""
    layer_owner: str = "L2"
    summary: str = ""
    state_only: bool = True
    no_decision: bool = True
    no_execution: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _true(self.state_only, "MathModelGovernanceStateBase.state_only")
        _true(self.no_decision, "MathModelGovernanceStateBase.no_decision")
        _true(self.no_execution, "MathModelGovernanceStateBase.no_execution")
        if not self.schema_version:
            raise ValueError("MathModelGovernanceStateBase.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathModelRegistryState(MathModelGovernanceStateBase):
    """模型注册快照状态。"""

    model_type: str = "unknown"
    owner: str = "future_l4_or_l6"
    risk_level: str = "unknown"
    schema_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ModelParameterGovernanceState(MathModelGovernanceStateBase):
    """模型参数、权重、阈值和版本状态。"""

    parameter_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    weight_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    threshold_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    parameter_validation_hash: str = ""


@dataclass(frozen=True, slots=True)
class FeatureSnapshotState(MathModelGovernanceStateBase):
    """特征快照状态。"""

    feature_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    feature_extraction_version: str = ""


@dataclass(frozen=True, slots=True)
class ScoringSnapshotState(MathModelGovernanceStateBase):
    """评分快照状态。"""

    score: float = 0.0
    confidence: float = 0.0
    uncertainty: float = 0.0
    latency_ms: float = 0.0
    degrade_path: str = ""

    def __post_init__(self) -> None:
        MathModelGovernanceStateBase.__post_init__(self)
        _unit(self.score, "ScoringSnapshotState.score")
        _unit(self.confidence, "ScoringSnapshotState.confidence")
        _unit(self.uncertainty, "ScoringSnapshotState.uncertainty")
        if self.latency_ms < 0.0:
            raise ValueError("ScoringSnapshotState.latency_ms cannot be negative")


@dataclass(frozen=True, slots=True)
class ModelEvidenceState(MathModelGovernanceStateBase):
    """模型证据链状态。"""

    score_snapshot_hash: str = ""
    evidence_item_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_trace_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ModelCalibrationRecordState(MathModelGovernanceStateBase):
    """模型校准记录状态。"""

    calibration_error: float = 0.0
    calibration_version: str = ""
    calibrated_at: str = ""

    def __post_init__(self) -> None:
        MathModelGovernanceStateBase.__post_init__(self)
        _unit(self.calibration_error, "ModelCalibrationRecordState.calibration_error")


@dataclass(frozen=True, slots=True)
class DriftDetectionRecordState(MathModelGovernanceStateBase):
    """漂移检测记录状态。"""

    drift_window_ref: TypedRef | None = None
    drift_type: str = "unknown"
    severity: str = "unknown"
    treatment_hint: str = ""


@dataclass(frozen=True, slots=True)
class ModelReplayState(MathModelGovernanceStateBase):
    """模型回放状态。"""

    replay_request_ref: TypedRef | None = None
    replay_result_ref: TypedRef | None = None
    reproduced: bool = False
    difference_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ModelShadowState(MathModelGovernanceStateBase):
    """模型影子模式状态。"""

    shadow_result_ref: TypedRef | None = None
    formal_result_ref: TypedRef | None = None
    difference_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    affects_main_path: bool = False

    def __post_init__(self) -> None:
        MathModelGovernanceStateBase.__post_init__(self)
        _false(self.affects_main_path, "ModelShadowState.affects_main_path")


@dataclass(frozen=True, slots=True)
class ModelGovernanceState(MathModelGovernanceStateBase):
    """模型治理状态。"""

    authorization_ref: TypedRef | None = None
    human_confirmation_ref: TypedRef | None = None
    can_use: bool = False
    must_fallback: bool = True


@dataclass(frozen=True, slots=True)
class ModelConflictState(MathModelGovernanceStateBase):
    """模型冲突状态。"""

    conflicting_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    conflict_level: str = "unknown"
    conflict_evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ModelTelemetryState(MathModelGovernanceStateBase):
    """模型遥测状态。"""

    latency_ms: float = 0.0
    timeout: bool = False
    error_code: str = ""
    adapter_status: str = "disabled"
    failure_rate: float = 0.0
    fallback_count: int = 0

    def __post_init__(self) -> None:
        MathModelGovernanceStateBase.__post_init__(self)
        if self.latency_ms < 0.0:
            raise ValueError("ModelTelemetryState.latency_ms cannot be negative")
        _unit(self.failure_rate, "ModelTelemetryState.failure_rate")
        if self.fallback_count < 0:
            raise ValueError("ModelTelemetryState.fallback_count cannot be negative")
