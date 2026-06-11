"""L3 数学模型发动机 100 分前置 Flow。

本模块只组织数学模型相关流程的引用、证据、降级、影子、回放和审计投影。
它不调用真实模型，不调用工具，不做最终裁决。
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


def _true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def _false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false")


@dataclass(frozen=True, slots=True)
class MathModelEngineFlowBase:
    """数学模型 Flow 基础对象，只保存引用。"""

    flow_ref: TypedRef | None = None
    formula_profile_ref: TypedRef | None = None
    parameter_snapshot_ref: TypedRef | None = None
    threshold_policy_ref: TypedRef | None = None
    input_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    output_evidence_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    telemetry_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    fallback_reason_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    advisory_only: bool = True
    evidence_only: bool = True
    disabled_safe: bool = True
    no_final_decision: bool = True
    no_tool_action: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _true(self.request_only, "MathModelEngineFlowBase.request_only")
        _true(self.advisory_only, "MathModelEngineFlowBase.advisory_only")
        _true(self.evidence_only, "MathModelEngineFlowBase.evidence_only")
        _true(self.disabled_safe, "MathModelEngineFlowBase.disabled_safe")
        _true(self.no_final_decision, "MathModelEngineFlowBase.no_final_decision")
        _true(self.no_tool_action, "MathModelEngineFlowBase.no_tool_action")
        if not self.schema_version:
            raise ValueError("MathModelEngineFlowBase.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathFeatureExtractionFlow(MathModelEngineFlowBase):
    """特征提取 Flow，只产出特征快照引用。"""

    feature_snapshot_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class MathScoringFlow(MathModelEngineFlowBase):
    """评分 Flow，可表达禁用、影子、回放和降级态。"""

    score_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    shadow_mode: bool = False
    replay_mode: bool = False
    fallback_used: bool = False


@dataclass(frozen=True, slots=True)
class MathScoreAggregationFlow(MathModelEngineFlowBase):
    """评分聚合 Flow，聚合参数外置。"""

    score_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    aggregation_profile_ref: TypedRef | None = None
    aggregated_evidence_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ConfidenceSynthesisFlow(MathModelEngineFlowBase):
    """置信度合成 Flow，只产出置信证据。"""

    confidence_evidence_ref: TypedRef | None = None
    uncertainty_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ModelConflictFlow(MathModelEngineFlowBase):
    """模型冲突 Flow，只产出冲突证据。"""

    model_result_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    conflict_evidence_ref: TypedRef | None = None
    arbitrates_execution: bool = False

    def __post_init__(self) -> None:
        MathModelEngineFlowBase.__post_init__(self)
        _false(self.arbitrates_execution, "ModelConflictFlow.arbitrates_execution")


@dataclass(frozen=True, slots=True)
class ModelCalibrationFlow(MathModelEngineFlowBase):
    """模型校准 Flow，只生成报告引用。"""

    calibration_report_ref: TypedRef | None = None
    changes_parameters: bool = False

    def __post_init__(self) -> None:
        MathModelEngineFlowBase.__post_init__(self)
        _false(self.changes_parameters, "ModelCalibrationFlow.changes_parameters")


@dataclass(frozen=True, slots=True)
class DriftDetectionFlow(MathModelEngineFlowBase):
    """漂移检测 Flow，只产出漂移信号引用。"""

    drift_signal_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ModelReplayFlow(MathModelEngineFlowBase):
    """模型回放 Flow，可表达可复现或差异来源。"""

    replay_request_ref: TypedRef | None = None
    replay_result_ref: TypedRef | None = None
    difference_refs: tuple[TypedRef, ...] = field(default_factory=tuple)


@dataclass(frozen=True, slots=True)
class ModelShadowFlow(MathModelEngineFlowBase):
    """模型影子 Flow，影子结果不影响主路径。"""

    shadow_result_ref: TypedRef | None = None
    formal_result_ref: TypedRef | None = None
    affects_main_path: bool = False

    def __post_init__(self) -> None:
        MathModelEngineFlowBase.__post_init__(self)
        _false(self.affects_main_path, "ModelShadowFlow.affects_main_path")


@dataclass(frozen=True, slots=True)
class ModelFallbackFlow(MathModelEngineFlowBase):
    """模型降级 Flow，产出安全默认证据。"""

    fallback_reason_ref: TypedRef | None = None
    safe_default_result_ref: TypedRef | None = None


@dataclass(frozen=True, slots=True)
class ModelAuditProjectionFlow(MathModelEngineFlowBase):
    """模型审计投影 Flow，包含输入、参数、输出、证据、降级和 trace 引用。"""

    input_snapshot_ref: TypedRef | None = None
    parameter_snapshot_ref: TypedRef | None = None
    output_snapshot_ref: TypedRef | None = None
    audit_projection_ref: TypedRef | None = None
    trace_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    audit_write_performed: bool = False

    def __post_init__(self) -> None:
        MathModelEngineFlowBase.__post_init__(self)
        _false(self.audit_write_performed, "ModelAuditProjectionFlow.audit_write_performed")


@dataclass(frozen=True, slots=True)
class MathFormulaParameterizationRef:
    """公式、权重、阈值外置化引用。"""

    formula_id: str = ""
    formula_profile_ref: TypedRef | None = None
    parameter_snapshot_ref: TypedRef | None = None
    threshold_policy_ref: TypedRef | None = None
    defaults_ref: TypedRef | None = None
    externalized: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _true(self.externalized, "MathFormulaParameterizationRef.externalized")
        if not self.schema_version:
            raise ValueError("MathFormulaParameterizationRef.schema_version cannot be empty")
