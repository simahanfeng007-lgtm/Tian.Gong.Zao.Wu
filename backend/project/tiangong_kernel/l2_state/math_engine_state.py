"""L2 数学发动机状态记录。

These objects reserve the state vocabulary for future mathematical model
engines.  They only record immutable facts and references.  They do not score,
rank, train, tune, refresh, infer, persist, or detect anything.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.serialization import stable_hash, stable_json_dumps

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_state_only(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _ensure_false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class MathematicalModelState:
    """数学模型引用状态，不持有模型实例。"""

    identity: L2StateIdentity
    status: L2StateStatus
    model_ref: TypedRef | None = None
    model_name: str = ""
    model_kind: str = "unknown"
    version_ref: TypedRef | None = None
    parameter_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    weight_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    threshold_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    calibration_ref: TypedRef | None = None
    owner_layer_hint: str = "future_l4_or_l6"
    advisory_only: bool = True
    state_only: bool = True
    has_runtime_model: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_state_only(self.state_only, "MathematicalModelState.state_only")
        _ensure_state_only(self.advisory_only, "MathematicalModelState.advisory_only")
        _ensure_false(self.has_runtime_model, "MathematicalModelState.has_runtime_model")
        if not self.schema_version:
            raise ValueError("MathematicalModelState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelParameterState:
    """模型参数状态，只记录未来模型配置引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    parameter_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    parameter_name: str = ""
    value_ref: TypedRef | None = None
    value_label: str = ""
    source_ref: TypedRef | None = None
    state_only: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_state_only(self.state_only, "ModelParameterState.state_only")
        if not self.schema_version:
            raise ValueError("ModelParameterState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelWeightState:
    """模型权重状态，只记录已归一化权重事实。"""

    identity: L2StateIdentity
    status: L2StateStatus
    weight_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    weight_name: str = ""
    normalized_weight: float = 0.0
    source_ref: TypedRef | None = None
    state_only: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.normalized_weight, "ModelWeightState.normalized_weight")
        _ensure_state_only(self.state_only, "ModelWeightState.state_only")
        if not self.schema_version:
            raise ValueError("ModelWeightState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelThresholdState:
    """模型阈值状态，只记录阈值事实。"""

    identity: L2StateIdentity
    status: L2StateStatus
    threshold_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    threshold_name: str = ""
    normalized_threshold: float = 0.0
    source_ref: TypedRef | None = None
    hard_boundary_hint: bool = False
    state_only: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.normalized_threshold, "ModelThresholdState.normalized_threshold")
        _ensure_state_only(self.state_only, "ModelThresholdState.state_only")
        if not self.schema_version:
            raise ValueError("ModelThresholdState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelCalibrationState:
    """模型校准状态，只记录校准引用事实。"""

    identity: L2StateIdentity
    status: L2StateStatus
    calibration_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    profile_ref: TypedRef | None = None
    source_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    state_only: bool = True
    does_not_adjust_model: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_state_only(self.state_only, "ModelCalibrationState.state_only")
        _ensure_state_only(self.does_not_adjust_model, "ModelCalibrationState.does_not_adjust_model")
        if len(self.summary) > 512:
            raise ValueError("ModelCalibrationState.summary must be short")
        if not self.schema_version:
            raise ValueError("ModelCalibrationState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelVersionState:
    """模型版本状态，只记录版本与兼容引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    version_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    version_label: str = L2_STATE_SCHEMA_VERSION
    compatibility_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    supersedes_ref: TypedRef | None = None
    state_only: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_state_only(self.state_only, "ModelVersionState.state_only")
        if not self.version_label:
            raise ValueError("ModelVersionState.version_label cannot be empty")
        if not self.schema_version:
            raise ValueError("ModelVersionState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ScoreState:
    """评分状态，只记录未来模型路径输出的评分事实。"""

    identity: L2StateIdentity
    status: L2StateStatus
    score_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    input_snapshot_ref: TypedRef | None = None
    output_snapshot_ref: TypedRef | None = None
    normalized_score: float = 0.0
    confidence_ref: TypedRef | None = None
    score_label: str = ""
    advisory_only: bool = True
    state_only: bool = True
    grants_permission: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.normalized_score, "ScoreState.normalized_score")
        _ensure_state_only(self.advisory_only, "ScoreState.advisory_only")
        _ensure_state_only(self.state_only, "ScoreState.state_only")
        _ensure_false(self.grants_permission, "ScoreState.grants_permission")
        if not self.schema_version:
            raise ValueError("ScoreState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class AssessmentState:
    """评估状态，只记录未来模型路径输出的评估事实。"""

    identity: L2StateIdentity
    status: L2StateStatus
    assessment_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    recommendation_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    summary: str = ""
    advisory_only: bool = True
    state_only: bool = True
    writes_l2_state: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_state_only(self.advisory_only, "AssessmentState.advisory_only")
        _ensure_state_only(self.state_only, "AssessmentState.state_only")
        _ensure_false(self.writes_l2_state, "AssessmentState.writes_l2_state")
        if len(self.summary) > 512:
            raise ValueError("AssessmentState.summary must be short")
        if not self.schema_version:
            raise ValueError("AssessmentState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelInputSnapshot:
    """模型输入快照，只保存输入引用集合。"""

    identity: L2StateIdentity
    status: L2StateStatus
    snapshot_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    source_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    feature_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    objective_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    constraint_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    snapshot_only: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_state_only(self.snapshot_only, "ModelInputSnapshot.snapshot_only")
        if not self.schema_version:
            raise ValueError("ModelInputSnapshot.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelOutputSnapshot:
    """模型输出快照，只保存输出引用集合。"""

    identity: L2StateIdentity
    status: L2StateStatus
    snapshot_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    assessment_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trace_ref: TypedRef | None = None
    snapshot_only: bool = True
    executes_action: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_state_only(self.snapshot_only, "ModelOutputSnapshot.snapshot_only")
        _ensure_false(self.executes_action, "ModelOutputSnapshot.executes_action")
        if not self.schema_version:
            raise ValueError("ModelOutputSnapshot.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelTraceState:
    """模型追踪状态，只保存追踪引用。"""

    identity: L2StateIdentity
    status: L2StateStatus
    trace_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    input_snapshot_ref: TypedRef | None = None
    output_snapshot_ref: TypedRef | None = None
    step_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trace_only: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_state_only(self.trace_only, "ModelTraceState.trace_only")
        if not self.schema_version:
            raise ValueError("ModelTraceState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelConfidenceState:
    """模型置信状态，只记录置信事实。"""

    identity: L2StateIdentity
    status: L2StateStatus
    confidence_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    target_ref: TypedRef | None = None
    normalized_confidence: float = 0.0
    confidence_label: str = "unknown"
    state_only: bool = True
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.normalized_confidence, "ModelConfidenceState.normalized_confidence")
        _ensure_state_only(self.state_only, "ModelConfidenceState.state_only")
        if not self.schema_version:
            raise ValueError("ModelConfidenceState.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class ModelDriftState:
    """模型漂移状态，只记录漂移观察引用，不做检测。"""

    identity: L2StateIdentity
    status: L2StateStatus
    drift_ref: TypedRef | None = None
    model_ref: TypedRef | None = None
    baseline_ref: TypedRef | None = None
    observation_ref: TypedRef | None = None
    drift_label: str = "unknown"
    drift_indicator: float = 0.0
    state_only: bool = True
    detector_enabled: bool = False
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.drift_indicator, "ModelDriftState.drift_indicator")
        _ensure_state_only(self.state_only, "ModelDriftState.state_only")
        _ensure_false(self.detector_enabled, "ModelDriftState.detector_enabled")
        if not self.schema_version:
            raise ValueError("ModelDriftState.schema_version cannot be empty")


def math_engine_state_stable_json(value: object) -> str:
    """Return canonical JSON for L2 math engine state records."""

    return stable_json_dumps(value)


def math_engine_state_stable_hash(value: object) -> str:
    """Return a stable hash for L2 math engine state records."""

    return stable_hash(value)
