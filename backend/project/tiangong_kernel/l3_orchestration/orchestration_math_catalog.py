"""L3 第八阶段数学模型总收口目录对象。

本模块只汇总 L3 数学输入、评分、排序、建议、原因码、权重入口与冻结说明。
它不实现复杂策略，不产生执行许可，不做边界放行。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class OrchestrationMathCatalogKind(str, Enum):
    """数学目录类别。"""

    MATH = "math"
    SCORE = "score"
    RANKING = "ranking"
    RECOMMENDATION = "recommendation"
    REASON_CODE = "reason_code"
    WEIGHT_INPUT = "weight_input"
    BOUNDARY_NOTE = "boundary_note"
    CONSISTENCY = "consistency"
    SNAPSHOT = "snapshot"
    FREEZE_NOTE = "freeze_note"


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
class OrchestrationMathCatalog:
    """L3 数学模型总目录。"""

    catalog_ref: TypedRef
    input_object_names: tuple[str, ...] = field(default_factory=tuple)
    result_object_names: tuple[str, ...] = field(default_factory=tuple)
    score_catalog_ref: TypedRef | None = None
    ranking_catalog_ref: TypedRef | None = None
    recommendation_catalog_ref: TypedRef | None = None
    catalog_kind: OrchestrationMathCatalogKind = OrchestrationMathCatalogKind.MATH
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.input_object_names + self.result_object_names:
            _ensure_short_text(item, "OrchestrationMathCatalog names", 128)
        if self.catalog_kind is not OrchestrationMathCatalogKind.MATH:
            raise ValueError("OrchestrationMathCatalog.catalog_kind must be math")
        _ensure_flag(self.advisory_only, "OrchestrationMathCatalog.advisory_only")
        if not self.schema_version:
            raise ValueError("OrchestrationMathCatalog.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationScoreCatalog:
    """L3 score 对象目录。"""

    catalog_ref: TypedRef
    score_object_names: tuple[str, ...] = field(default_factory=tuple)
    score_range_hint: str = "0.0_to_1.0"
    confidence_field_name: str = "confidence"
    catalog_kind: OrchestrationMathCatalogKind = OrchestrationMathCatalogKind.SCORE
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.score_object_names:
            _ensure_short_text(item, "OrchestrationScoreCatalog.score_object_names", 128)
        _ensure_short_text(self.score_range_hint, "OrchestrationScoreCatalog.score_range_hint", 128)
        _ensure_short_text(self.confidence_field_name, "OrchestrationScoreCatalog.confidence_field_name", 128)
        if self.catalog_kind is not OrchestrationMathCatalogKind.SCORE:
            raise ValueError("OrchestrationScoreCatalog.catalog_kind must be score")
        _ensure_flag(self.advisory_only, "OrchestrationScoreCatalog.advisory_only")
        if not self.schema_version:
            raise ValueError("OrchestrationScoreCatalog.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationRankingCatalog:
    """L3 ranking 对象目录。"""

    catalog_ref: TypedRef
    ranking_object_names: tuple[str, ...] = field(default_factory=tuple)
    stable_sort_key_hints: tuple[str, ...] = ("score_desc", "ref_id_asc")
    catalog_kind: OrchestrationMathCatalogKind = OrchestrationMathCatalogKind.RANKING
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.ranking_object_names + self.stable_sort_key_hints:
            _ensure_short_text(item, "OrchestrationRankingCatalog text", 128)
        if self.catalog_kind is not OrchestrationMathCatalogKind.RANKING:
            raise ValueError("OrchestrationRankingCatalog.catalog_kind must be ranking")
        _ensure_flag(self.advisory_only, "OrchestrationRankingCatalog.advisory_only")
        if not self.schema_version:
            raise ValueError("OrchestrationRankingCatalog.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationRecommendationCatalog:
    """L3 recommendation/advice/suggestion 对象目录。"""

    catalog_ref: TypedRef
    recommendation_object_names: tuple[str, ...] = field(default_factory=tuple)
    advice_object_names: tuple[str, ...] = field(default_factory=tuple)
    suggestion_object_names: tuple[str, ...] = field(default_factory=tuple)
    catalog_kind: OrchestrationMathCatalogKind = OrchestrationMathCatalogKind.RECOMMENDATION
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.recommendation_object_names + self.advice_object_names + self.suggestion_object_names:
            _ensure_short_text(item, "OrchestrationRecommendationCatalog names", 128)
        if self.catalog_kind is not OrchestrationMathCatalogKind.RECOMMENDATION:
            raise ValueError("OrchestrationRecommendationCatalog.catalog_kind must be recommendation")
        _ensure_flag(self.advisory_only, "OrchestrationRecommendationCatalog.advisory_only")
        if not self.schema_version:
            raise ValueError("OrchestrationRecommendationCatalog.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationReasonCodeCatalog:
    """L3 reason_codes 目录。"""

    catalog_ref: TypedRef
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    code_format_hint: str = "lower_snake_case"
    catalog_kind: OrchestrationMathCatalogKind = OrchestrationMathCatalogKind.REASON_CODE
    stable_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.reason_codes:
            _ensure_short_text(item, "OrchestrationReasonCodeCatalog.reason_codes", 128)
        _ensure_short_text(self.code_format_hint, "OrchestrationReasonCodeCatalog.code_format_hint", 128)
        if self.catalog_kind is not OrchestrationMathCatalogKind.REASON_CODE:
            raise ValueError("OrchestrationReasonCodeCatalog.catalog_kind must be reason_code")
        _ensure_flag(self.stable_only, "OrchestrationReasonCodeCatalog.stable_only")
        if not self.schema_version:
            raise ValueError("OrchestrationReasonCodeCatalog.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationWeightInputCatalog:
    """L3 情感权重与动态驱动入口目录。"""

    catalog_ref: TypedRef
    affective_weight_names: tuple[str, ...] = field(default_factory=tuple)
    dynamic_drive_weight_names: tuple[str, ...] = field(default_factory=tuple)
    allowed_effect_hints: tuple[str, ...] = ("tendency", "priority", "ranking")
    catalog_kind: OrchestrationMathCatalogKind = OrchestrationMathCatalogKind.WEIGHT_INPUT
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.affective_weight_names + self.dynamic_drive_weight_names + self.allowed_effect_hints:
            _ensure_short_text(item, "OrchestrationWeightInputCatalog text", 128)
        if self.catalog_kind is not OrchestrationMathCatalogKind.WEIGHT_INPUT:
            raise ValueError("OrchestrationWeightInputCatalog.catalog_kind must be weight_input")
        _ensure_flag(self.advisory_only, "OrchestrationWeightInputCatalog.advisory_only")
        if not self.schema_version:
            raise ValueError("OrchestrationWeightInputCatalog.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationMathBoundaryNote:
    """L3 数学边界说明。"""

    note_ref: TypedRef
    forbidden_output_hints: tuple[str, ...] = ("execute", "permission_grant", "tool_call", "model_call")
    allowed_output_hints: tuple[str, ...] = ("advice", "suggestion", "ranking", "projection")
    summary: str = "math outputs stay advisory"
    catalog_kind: OrchestrationMathCatalogKind = OrchestrationMathCatalogKind.BOUNDARY_NOTE
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.forbidden_output_hints + self.allowed_output_hints:
            _ensure_short_text(item, "OrchestrationMathBoundaryNote hints", 128)
        _ensure_short_text(self.summary, "OrchestrationMathBoundaryNote.summary")
        if self.catalog_kind is not OrchestrationMathCatalogKind.BOUNDARY_NOTE:
            raise ValueError("OrchestrationMathBoundaryNote.catalog_kind must be boundary_note")
        _ensure_flag(self.advisory_only, "OrchestrationMathBoundaryNote.advisory_only")
        if not self.schema_version:
            raise ValueError("OrchestrationMathBoundaryNote.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationMathConsistencyReport:
    """L3 数学一致性报告。"""

    report_ref: TypedRef
    checked_score_names: tuple[str, ...] = field(default_factory=tuple)
    missing_reason_code_names: tuple[str, ...] = field(default_factory=tuple)
    out_of_range_score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    consistency_score: float = 0.0
    report_only: bool = True
    catalog_kind: OrchestrationMathCatalogKind = OrchestrationMathCatalogKind.CONSISTENCY
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.checked_score_names + self.missing_reason_code_names:
            _ensure_short_text(item, "OrchestrationMathConsistencyReport names", 128)
        _ensure_unit_interval(self.consistency_score, "OrchestrationMathConsistencyReport.consistency_score")
        _ensure_flag(self.report_only, "OrchestrationMathConsistencyReport.report_only")
        if self.catalog_kind is not OrchestrationMathCatalogKind.CONSISTENCY:
            raise ValueError("OrchestrationMathConsistencyReport.catalog_kind must be consistency")
        if not self.schema_version:
            raise ValueError("OrchestrationMathConsistencyReport.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationMathSnapshotRef:
    """L3 数学快照引用。"""

    snapshot_ref: TypedRef
    source_catalog_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    stable_hash_hint: str = ""
    catalog_kind: OrchestrationMathCatalogKind = OrchestrationMathCatalogKind.SNAPSHOT
    ref_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.stable_hash_hint, "OrchestrationMathSnapshotRef.stable_hash_hint", 128)
        _ensure_flag(self.ref_only, "OrchestrationMathSnapshotRef.ref_only")
        if self.catalog_kind is not OrchestrationMathCatalogKind.SNAPSHOT:
            raise ValueError("OrchestrationMathSnapshotRef.catalog_kind must be snapshot")
        if not self.schema_version:
            raise ValueError("OrchestrationMathSnapshotRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationMathFreezeNote:
    """L3 数学冻结说明。"""

    note_ref: TypedRef
    frozen_catalog_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    freeze_scope_hint: str = "l3_math_advisory_contract"
    summary: str = "math model remains advisory and deterministic"
    catalog_kind: OrchestrationMathCatalogKind = OrchestrationMathCatalogKind.FREEZE_NOTE
    note_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.freeze_scope_hint, "OrchestrationMathFreezeNote.freeze_scope_hint", 128)
        _ensure_short_text(self.summary, "OrchestrationMathFreezeNote.summary")
        _ensure_flag(self.note_only, "OrchestrationMathFreezeNote.note_only")
        if self.catalog_kind is not OrchestrationMathCatalogKind.FREEZE_NOTE:
            raise ValueError("OrchestrationMathFreezeNote.catalog_kind must be freeze_note")
        if not self.schema_version:
            raise ValueError("OrchestrationMathFreezeNote.schema_version cannot be empty")
