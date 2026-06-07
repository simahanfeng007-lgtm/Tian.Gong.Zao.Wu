"""L1 数学模型发动机 100 分前置契约端口。

本模块只定义数学模型元信息、特征、评分证据、校准、漂移、遥测、治理、
回放、影子和冲突的协议数据结构。它不实现模型、不调用外部能力、不产出最终裁决。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l0_primitives.trace import TraceContext

from .port_result import PortResult


MATH_ENGINE_CONTRACT_SCHEMA_VERSION = "0.1"


def _unit(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _non_empty(value: str, field_name: str) -> None:
    if not value:
        raise ValueError(f"{field_name} cannot be empty")


@dataclass(frozen=True, slots=True)
class MathModelId:
    """数学模型 ID。"""

    value: str
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.value, "MathModelId.value")
        _non_empty(self.schema_version, "MathModelId.schema_version")


@dataclass(frozen=True, slots=True)
class MathModelVersion:
    """数学模型版本。"""

    value: str
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.value, "MathModelVersion.value")
        _non_empty(self.schema_version, "MathModelVersion.schema_version")


@dataclass(frozen=True, slots=True)
class ModelRunId:
    """模型运行 ID。"""

    value: str
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.value, "ModelRunId.value")
        _non_empty(self.schema_version, "ModelRunId.schema_version")


@dataclass(frozen=True, slots=True)
class FeatureKey:
    """特征键。"""

    value: str
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.value, "FeatureKey.value")
        _non_empty(self.schema_version, "FeatureKey.schema_version")


@dataclass(frozen=True, slots=True)
class FeatureValue:
    """特征值，使用显式类型与 schema 引用保护载荷。"""

    feature_key: FeatureKey
    value_kind: str = "numeric"
    numeric_value: float = 0.0
    text_value: str = ""
    schema_ref: TypedRef | None = None
    trace_context: TraceContext | None = None
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.value_kind, "FeatureValue.value_kind")
        _non_empty(self.schema_version, "FeatureValue.schema_version")


@dataclass(frozen=True, slots=True)
class FeatureSnapshot:
    """特征快照。"""

    snapshot_ref: TypedRef | None = None
    feature_values: tuple[FeatureValue, ...] = field(default_factory=tuple)
    feature_snapshot_hash: str = ""
    source_trace_ref: TypedRef | None = None
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.schema_version, "FeatureSnapshot.schema_version")


@dataclass(frozen=True, slots=True)
class ModelInputEnvelope:
    """模型输入信封，只保存输入与 schema 引用。"""

    input_ref: TypedRef | None = None
    model_id: MathModelId | None = None
    model_version: MathModelVersion | None = None
    feature_snapshot_ref: TypedRef | None = None
    input_snapshot_hash: str = ""
    input_schema_ref: TypedRef | None = None
    trace_context: TraceContext | None = None
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.schema_version, "ModelInputEnvelope.schema_version")


@dataclass(frozen=True, slots=True)
class ModelParameterSnapshot:
    """模型参数快照。"""

    parameter_snapshot_ref: TypedRef | None = None
    model_id: MathModelId | None = None
    model_version: MathModelVersion | None = None
    parameter_version: str = ""
    weight_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    threshold_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    parameter_snapshot_hash: str = ""
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.schema_version, "ModelParameterSnapshot.schema_version")


@dataclass(frozen=True, slots=True)
class ScoreValue:
    """评分值，范围 0 到 1。"""

    value: float = 0.0
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _unit(self.value, "ScoreValue.value")
        _non_empty(self.schema_version, "ScoreValue.schema_version")


@dataclass(frozen=True, slots=True)
class ConfidenceValue:
    """置信度，范围 0 到 1。"""

    value: float = 0.0
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _unit(self.value, "ConfidenceValue.value")
        _non_empty(self.schema_version, "ConfidenceValue.schema_version")


@dataclass(frozen=True, slots=True)
class UncertaintyValue:
    """不确定性，范围 0 到 1。"""

    value: float = 0.0
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _unit(self.value, "UncertaintyValue.value")
        _non_empty(self.schema_version, "UncertaintyValue.schema_version")


@dataclass(frozen=True, slots=True)
class ScoreEvidence:
    """评分证据链。"""

    evidence_ref: TypedRef | None = None
    input_snapshot_hash: str = ""
    feature_snapshot_hash: str = ""
    parameter_snapshot_hash: str = ""
    score_snapshot_hash: str = ""
    evidence_items: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_trace_ref: TypedRef | None = None
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.schema_version, "ScoreEvidence.schema_version")


@dataclass(frozen=True, slots=True)
class ScoreResult:
    """评分结果，只能作为证据或建议来源。"""

    result_ref: TypedRef | None = None
    score: ScoreValue = field(default_factory=ScoreValue)
    confidence: ConfidenceValue = field(default_factory=ConfidenceValue)
    uncertainty: UncertaintyValue = field(default_factory=UncertaintyValue)
    evidence_ref: TypedRef | None = None
    trace_context: TraceContext | None = None
    advisory_only: bool = True
    authority_result: bool = False
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("ScoreResult.advisory_only must remain true")
        if self.authority_result:
            raise ValueError("ScoreResult cannot be an authority result")
        _non_empty(self.schema_version, "ScoreResult.schema_version")


@dataclass(frozen=True, slots=True)
class CalibrationReport:
    """校准报告。"""

    report_ref: TypedRef | None = None
    calibration_error: float = 0.0
    accuracy: float = 0.0
    stability: float = 0.0
    report_only: bool = True
    changes_runtime_policy: bool = False
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _unit(self.calibration_error, "CalibrationReport.calibration_error")
        _unit(self.accuracy, "CalibrationReport.accuracy")
        _unit(self.stability, "CalibrationReport.stability")
        if self.report_only is not True:
            raise ValueError("CalibrationReport.report_only must remain true")
        if self.changes_runtime_policy:
            raise ValueError("CalibrationReport cannot change runtime policy")
        _non_empty(self.schema_version, "CalibrationReport.schema_version")


@dataclass(frozen=True, slots=True)
class DriftSignal:
    """漂移信号，只能作为风险证据。"""

    signal_ref: TypedRef | None = None
    drift_score: float = 0.0
    severity_hint: str = "unknown"
    evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    signal_only: bool = True
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _unit(self.drift_score, "DriftSignal.drift_score")
        if self.signal_only is not True:
            raise ValueError("DriftSignal.signal_only must remain true")
        _non_empty(self.schema_version, "DriftSignal.schema_version")


@dataclass(frozen=True, slots=True)
class ModelTelemetryRecord:
    """模型遥测记录。"""

    telemetry_ref: TypedRef | None = None
    latency_ms: float = 0.0
    timeout: bool = False
    fallback_used: bool = False
    adapter_used_ref: TypedRef | None = None
    disabled_reason: str = ""
    error_code: str = ""
    degrade_path: str = ""
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.latency_ms < 0.0:
            raise ValueError("ModelTelemetryRecord.latency_ms cannot be negative")
        _non_empty(self.schema_version, "ModelTelemetryRecord.schema_version")


@dataclass(frozen=True, slots=True)
class ModelReplayRequest:
    """模型回放请求。"""

    request_ref: TypedRef | None = None
    model_id: MathModelId | None = None
    model_version: MathModelVersion | None = None
    input_snapshot_ref: TypedRef | None = None
    parameter_snapshot_ref: TypedRef | None = None
    request_only: bool = True
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.request_only is not True:
            raise ValueError("ModelReplayRequest.request_only must remain true")
        _non_empty(self.schema_version, "ModelReplayRequest.schema_version")


@dataclass(frozen=True, slots=True)
class ModelReplayResult:
    """模型回放结果。"""

    result_ref: TypedRef | None = None
    replay_request_ref: TypedRef | None = None
    reproduced: bool = False
    difference_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    result_only: bool = True
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.result_only is not True:
            raise ValueError("ModelReplayResult.result_only must remain true")
        _non_empty(self.schema_version, "ModelReplayResult.schema_version")


@dataclass(frozen=True, slots=True)
class ModelFallbackReason:
    """模型降级原因。"""

    reason_ref: TypedRef | None = None
    reason_code: str = "model_disabled"
    summary: str = ""
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.reason_code, "ModelFallbackReason.reason_code")
        _non_empty(self.schema_version, "ModelFallbackReason.schema_version")


@dataclass(frozen=True, slots=True)
class ModelGovernanceStatus:
    """模型治理状态表达。"""

    status_ref: TypedRef | None = None
    disabled: bool = True
    can_use: bool = False
    must_fallback: bool = True
    status_only: bool = True
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.status_only is not True:
            raise ValueError("ModelGovernanceStatus.status_only must remain true")
        _non_empty(self.schema_version, "ModelGovernanceStatus.schema_version")


@dataclass(frozen=True, slots=True)
class MathModelDefinitionRequest:
    """数学模型定义请求。"""

    request_ref: TypedRef | None = None
    model_id: MathModelId | None = None
    request_only: bool = True
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.request_only is not True:
            raise ValueError("MathModelDefinitionRequest.request_only must remain true")
        _non_empty(self.schema_version, "MathModelDefinitionRequest.schema_version")


@dataclass(frozen=True, slots=True)
class MathModelDefinition:
    """数学模型定义响应。"""

    model_id: MathModelId
    model_name: str
    model_type: str = "unknown"
    version: MathModelVersion = field(default_factory=lambda: MathModelVersion("0.1"))
    owner_layer: str = "future_l4_or_l6"
    risk_level: str = "unknown"
    input_schema_ref: TypedRef | None = None
    output_schema_ref: TypedRef | None = None
    default_disabled: bool = True
    allowed_runtime_modes: tuple[str, ...] = ("disabled", "shadow", "replay", "fallback")
    definition_only: bool = True
    schema_version: str = MATH_ENGINE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _non_empty(self.model_name, "MathModelDefinition.model_name")
        _non_empty(self.model_type, "MathModelDefinition.model_type")
        if self.default_disabled is not True:
            raise ValueError("MathModelDefinition.default_disabled must remain true")
        if self.definition_only is not True:
            raise ValueError("MathModelDefinition.definition_only must remain true")
        _non_empty(self.schema_version, "MathModelDefinition.schema_version")


class MathModelDefinitionPort(ABC):
    """数学模型定义端口协议。"""

    @abstractmethod
    def describe_model(self, request: MathModelDefinitionRequest) -> PortResult[MathModelDefinition]:
        """返回模型定义引用。"""


class FeatureExtractionPort(ABC):
    """特征提取端口协议。"""

    @abstractmethod
    def describe_feature_snapshot(self, envelope: ModelInputEnvelope) -> PortResult[FeatureSnapshot]:
        """返回特征快照引用。"""


class ModelEvaluationPort(ABC):
    """模型效果评估端口协议。"""

    @abstractmethod
    def describe_evaluation(self, result: ScoreResult) -> PortResult[ScoreEvidence]:
        """返回评估证据引用。"""


class ModelCalibrationPort(ABC):
    """模型校准端口协议。"""

    @abstractmethod
    def describe_calibration(self, result: ScoreResult) -> PortResult[CalibrationReport]:
        """返回校准报告。"""


class DriftDetectionPort(ABC):
    """漂移检测端口协议。"""

    @abstractmethod
    def describe_drift(self, envelope: ModelInputEnvelope) -> PortResult[DriftSignal]:
        """返回漂移信号。"""


class ModelEvidencePort(ABC):
    """模型证据端口协议。"""

    @abstractmethod
    def describe_evidence(self, result: ScoreResult) -> PortResult[ScoreEvidence]:
        """返回证据链。"""


class ModelTelemetryPort(ABC):
    """模型遥测端口协议。"""

    @abstractmethod
    def describe_telemetry(self, result: ScoreResult) -> PortResult[ModelTelemetryRecord]:
        """返回遥测记录。"""


class ModelGovernancePort(ABC):
    """模型治理端口协议。"""

    @abstractmethod
    def describe_governance_status(self, model_id: MathModelId) -> PortResult[ModelGovernanceStatus]:
        """返回治理状态。"""


class ModelReplayPort(ABC):
    """模型回放端口协议。"""

    @abstractmethod
    def request_replay(self, request: ModelReplayRequest) -> PortResult[ModelReplayResult]:
        """返回回放结果引用。"""


class ModelShadowPort(ABC):
    """模型影子模式端口协议。"""

    @abstractmethod
    def describe_shadow_result(self, envelope: ModelInputEnvelope) -> PortResult[ScoreResult]:
        """返回影子结果引用。"""


class ModelConflictPort(ABC):
    """多模型冲突端口协议。"""

    @abstractmethod
    def describe_conflict(self, results: tuple[ScoreResult, ...]) -> PortResult[ScoreEvidence]:
        """返回冲突证据。"""
