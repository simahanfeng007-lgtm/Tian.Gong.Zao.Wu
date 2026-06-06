"""L3 第八阶段组件目录与公共索引对象。

本模块只汇总组件、模块、公共导出、兼容性、阶段、对象族、边界、数学、投影和交接目录。
它不动态扫描文件系统，不加载外部插件，不实现任何真实服务。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class OrchestrationIndexKind(str, Enum):
    """L3 收口索引类别。"""

    COMPONENT = "component"
    MODULE = "module"
    PUBLIC_EXPORT = "public_export"
    COMPATIBILITY = "compatibility"
    STAGE = "stage"
    OBJECT_FAMILY = "object_family"
    BOUNDARY = "boundary"
    MATH = "math"
    FLOW = "flow"
    PROJECTION = "projection"
    HANDOFF = "handoff"


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
class OrchestrationComponentIndex:
    """L3 组件目录索引。"""

    index_ref: TypedRef
    component_names: tuple[str, ...] = field(default_factory=tuple)
    component_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    index_kind: OrchestrationIndexKind = OrchestrationIndexKind.COMPONENT
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.component_names:
            _ensure_short_text(item, "OrchestrationComponentIndex.component_names", 128)
        _ensure_short_text(self.summary, "OrchestrationComponentIndex.summary")
        if self.index_kind is not OrchestrationIndexKind.COMPONENT:
            raise ValueError("OrchestrationComponentIndex.index_kind must be component")
        if not self.schema_version:
            raise ValueError("OrchestrationComponentIndex.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationModuleIndex:
    """L3 模块索引。"""

    index_ref: TypedRef
    module_names: tuple[str, ...] = field(default_factory=tuple)
    module_family: str = "l3_orchestration"
    index_kind: OrchestrationIndexKind = OrchestrationIndexKind.MODULE
    stable_order: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.module_names:
            _ensure_short_text(item, "OrchestrationModuleIndex.module_names", 128)
        _ensure_short_text(self.module_family, "OrchestrationModuleIndex.module_family", 128)
        if self.index_kind is not OrchestrationIndexKind.MODULE:
            raise ValueError("OrchestrationModuleIndex.index_kind must be module")
        _ensure_flag(self.stable_order, "OrchestrationModuleIndex.stable_order")
        if not self.schema_version:
            raise ValueError("OrchestrationModuleIndex.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationPublicExportIndex:
    """L3 公共导出索引。"""

    index_ref: TypedRef
    exported_names: tuple[str, ...] = field(default_factory=tuple)
    duplicate_names: tuple[str, ...] = field(default_factory=tuple)
    missing_expected_names: tuple[str, ...] = field(default_factory=tuple)
    index_kind: OrchestrationIndexKind = OrchestrationIndexKind.PUBLIC_EXPORT
    stable_order: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.exported_names + self.duplicate_names + self.missing_expected_names:
            _ensure_short_text(item, "OrchestrationPublicExportIndex names", 128)
        if self.index_kind is not OrchestrationIndexKind.PUBLIC_EXPORT:
            raise ValueError("OrchestrationPublicExportIndex.index_kind must be public_export")
        _ensure_flag(self.stable_order, "OrchestrationPublicExportIndex.stable_order")
        if not self.schema_version:
            raise ValueError("OrchestrationPublicExportIndex.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationCompatibilityIndex:
    """L3 兼容性索引。"""

    index_ref: TypedRef
    compatible_stage_names: tuple[str, ...] = field(default_factory=tuple)
    baseline_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    compatibility_score: float = 0.0
    index_kind: OrchestrationIndexKind = OrchestrationIndexKind.COMPATIBILITY
    report_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.compatible_stage_names:
            _ensure_short_text(item, "OrchestrationCompatibilityIndex.compatible_stage_names", 128)
        _ensure_unit_interval(self.compatibility_score, "OrchestrationCompatibilityIndex.compatibility_score")
        if self.index_kind is not OrchestrationIndexKind.COMPATIBILITY:
            raise ValueError("OrchestrationCompatibilityIndex.index_kind must be compatibility")
        _ensure_flag(self.report_only, "OrchestrationCompatibilityIndex.report_only")
        if not self.schema_version:
            raise ValueError("OrchestrationCompatibilityIndex.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationStageIndex:
    """L3 阶段索引。"""

    index_ref: TypedRef
    stage_names: tuple[str, ...] = field(default_factory=tuple)
    completed_stage_names: tuple[str, ...] = field(default_factory=tuple)
    current_stage_name: str = "phase8_closure"
    index_kind: OrchestrationIndexKind = OrchestrationIndexKind.STAGE
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.stage_names + self.completed_stage_names:
            _ensure_short_text(item, "OrchestrationStageIndex.stage_names", 128)
        _ensure_short_text(self.current_stage_name, "OrchestrationStageIndex.current_stage_name", 128)
        if self.index_kind is not OrchestrationIndexKind.STAGE:
            raise ValueError("OrchestrationStageIndex.index_kind must be stage")
        if not self.schema_version:
            raise ValueError("OrchestrationStageIndex.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationObjectFamilyIndex:
    """L3 对象族索引。"""

    index_ref: TypedRef
    object_family_names: tuple[str, ...] = field(default_factory=tuple)
    representative_object_names: tuple[str, ...] = field(default_factory=tuple)
    index_kind: OrchestrationIndexKind = OrchestrationIndexKind.OBJECT_FAMILY
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.object_family_names + self.representative_object_names:
            _ensure_short_text(item, "OrchestrationObjectFamilyIndex names", 128)
        if self.index_kind is not OrchestrationIndexKind.OBJECT_FAMILY:
            raise ValueError("OrchestrationObjectFamilyIndex.index_kind must be object_family")
        if not self.schema_version:
            raise ValueError("OrchestrationObjectFamilyIndex.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationBoundaryIndex:
    """L3 边界索引。"""

    index_ref: TypedRef
    allowed_terms: tuple[str, ...] = field(default_factory=tuple)
    forbidden_capability_names: tuple[str, ...] = field(default_factory=tuple)
    non_execution_guarantees: tuple[str, ...] = field(default_factory=tuple)
    index_kind: OrchestrationIndexKind = OrchestrationIndexKind.BOUNDARY
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.allowed_terms + self.forbidden_capability_names + self.non_execution_guarantees:
            _ensure_short_text(item, "OrchestrationBoundaryIndex text", 128)
        if self.index_kind is not OrchestrationIndexKind.BOUNDARY:
            raise ValueError("OrchestrationBoundaryIndex.index_kind must be boundary")
        _ensure_flag(self.advisory_only, "OrchestrationBoundaryIndex.advisory_only")
        if not self.schema_version:
            raise ValueError("OrchestrationBoundaryIndex.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationMathIndex:
    """L3 数学对象索引。"""

    index_ref: TypedRef
    score_names: tuple[str, ...] = field(default_factory=tuple)
    ranking_names: tuple[str, ...] = field(default_factory=tuple)
    recommendation_names: tuple[str, ...] = field(default_factory=tuple)
    index_kind: OrchestrationIndexKind = OrchestrationIndexKind.MATH
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.score_names + self.ranking_names + self.recommendation_names:
            _ensure_short_text(item, "OrchestrationMathIndex names", 128)
        if self.index_kind is not OrchestrationIndexKind.MATH:
            raise ValueError("OrchestrationMathIndex.index_kind must be math")
        _ensure_flag(self.advisory_only, "OrchestrationMathIndex.advisory_only")
        if not self.schema_version:
            raise ValueError("OrchestrationMathIndex.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationProjectionIndex:
    """L3 投影对象索引。"""

    index_ref: TypedRef
    projection_object_names: tuple[str, ...] = field(default_factory=tuple)
    projection_target_hints: tuple[str, ...] = field(default_factory=tuple)
    index_kind: OrchestrationIndexKind = OrchestrationIndexKind.PROJECTION
    no_persistence: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.projection_object_names + self.projection_target_hints:
            _ensure_short_text(item, "OrchestrationProjectionIndex text", 128)
        if self.index_kind is not OrchestrationIndexKind.PROJECTION:
            raise ValueError("OrchestrationProjectionIndex.index_kind must be projection")
        _ensure_flag(self.no_persistence, "OrchestrationProjectionIndex.no_persistence")
        if not self.schema_version:
            raise ValueError("OrchestrationProjectionIndex.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class OrchestrationHandoffIndex:
    """L3 交接对象索引。"""

    index_ref: TypedRef
    handoff_names: tuple[str, ...] = field(default_factory=tuple)
    target_layer_hints: tuple[str, ...] = field(default_factory=tuple)
    index_kind: OrchestrationIndexKind = OrchestrationIndexKind.HANDOFF
    handoff_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.handoff_names + self.target_layer_hints:
            _ensure_short_text(item, "OrchestrationHandoffIndex text", 128)
        if self.index_kind is not OrchestrationIndexKind.HANDOFF:
            raise ValueError("OrchestrationHandoffIndex.index_kind must be handoff")
        _ensure_flag(self.handoff_only, "OrchestrationHandoffIndex.handoff_only")
        if not self.schema_version:
            raise ValueError("OrchestrationHandoffIndex.schema_version cannot be empty")
