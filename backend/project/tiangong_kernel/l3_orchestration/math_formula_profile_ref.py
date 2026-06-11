"""Formula profile references for L3 math model orchestration.

Formula bodies live outside L3.  This module only records references and
compatibility markers for legacy heuristic scoring.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class MathFormulaProfileRef:
    """Reference to an external formula or model profile."""

    formula_profile_ref: TypedRef | None = None
    profile_name: str = ""
    profile_version: str = L3_ORCHESTRATION_SCHEMA_VERSION
    owner_layer_hint: str = "future_l4_or_l6"
    descriptor_ref: TypedRef | None = None
    adapter_descriptor_ref: TypedRef | None = None
    input_schema_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    output_schema_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    profile_only: bool = True
    advisory_only: bool = True
    embedded_formula: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.profile_only is not True:
            raise ValueError("MathFormulaProfileRef.profile_only must remain true")
        if self.advisory_only is not True:
            raise ValueError("MathFormulaProfileRef.advisory_only must remain true")
        if self.embedded_formula:
            raise ValueError("MathFormulaProfileRef cannot embed formulas in L3")
        if not self.profile_version:
            raise ValueError("MathFormulaProfileRef.profile_version cannot be empty")
        if not self.schema_version:
            raise ValueError("MathFormulaProfileRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathModelPortCallRef:
    """Reference to a future L1 math model port call."""

    port_call_ref: TypedRef | None = None
    port_ref: TypedRef | None = None
    request_ref: TypedRef | None = None
    response_ref: TypedRef | None = None
    formula_profile_ref: TypedRef | None = None
    call_ref_only: bool = True
    advisory_only: bool = True
    real_call_performed: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.call_ref_only is not True:
            raise ValueError("MathModelPortCallRef.call_ref_only must remain true")
        if self.advisory_only is not True:
            raise ValueError("MathModelPortCallRef.advisory_only must remain true")
        if self.real_call_performed:
            raise ValueError("MathModelPortCallRef cannot record a real call in L3")
        if not self.schema_version:
            raise ValueError("MathModelPortCallRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathModelResultRef:
    """Reference to a future math model result."""

    result_ref: TypedRef | None = None
    port_call_ref: TypedRef | None = None
    score_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    assessment_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence_ref: TypedRef | None = None
    trace_ref: TypedRef | None = None
    result_ref_only: bool = True
    advisory_only: bool = True
    action_enabled: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.result_ref_only is not True:
            raise ValueError("MathModelResultRef.result_ref_only must remain true")
        if self.advisory_only is not True:
            raise ValueError("MathModelResultRef.advisory_only must remain true")
        if self.action_enabled:
            raise ValueError("MathModelResultRef cannot enable actions")
        if not self.schema_version:
            raise ValueError("MathModelResultRef.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class LegacyHeuristicCompatibility:
    """Marker for existing heuristic scoring retained for compatibility."""

    compatibility_ref: TypedRef | None = None
    source_module: str = ""
    source_object_names: tuple[str, ...] = field(default_factory=tuple)
    compatibility_only: bool = True
    formal_engine_path: bool = False
    advisory_only: bool = True
    migration_target: str = "MathModelOrchestrationFlow"
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.compatibility_only is not True:
            raise ValueError("LegacyHeuristicCompatibility.compatibility_only must remain true")
        if self.formal_engine_path:
            raise ValueError("Legacy heuristic scoring is not the formal engine path")
        if self.advisory_only is not True:
            raise ValueError("LegacyHeuristicCompatibility.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("LegacyHeuristicCompatibility.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class DefaultHeuristicScoringProfile:
    """Default marker for pre-patch L3 heuristic scoring profiles."""

    profile_ref: TypedRef | None = None
    profile_name: str = "default_l3_heuristic_scoring_compatibility"
    legacy_marker: LegacyHeuristicCompatibility = field(
        default_factory=lambda: LegacyHeuristicCompatibility(
            source_module="tiangong_kernel.l3_orchestration",
            source_object_names=("build_*_score", "build_*_ranking"),
        )
    )
    compatibility_only: bool = True
    formal_engine_path: bool = False
    embedded_formula_retained_for_tests: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.compatibility_only is not True:
            raise ValueError("DefaultHeuristicScoringProfile.compatibility_only must remain true")
        if self.formal_engine_path:
            raise ValueError("DefaultHeuristicScoringProfile is not the formal engine path")
        if self.embedded_formula_retained_for_tests is not True:
            raise ValueError("DefaultHeuristicScoringProfile must keep compatibility visibility")
        if not self.schema_version:
            raise ValueError("DefaultHeuristicScoringProfile.schema_version cannot be empty")
