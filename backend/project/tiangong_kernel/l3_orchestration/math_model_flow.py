"""Formal L3 math model flow references.

The flow objects in this module describe the future mathematical engine path
without executing it.  They are advisory-only and never write L2 state or
produce action-grounding requests.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .math_formula_profile_ref import MathFormulaProfileRef, MathModelPortCallRef, MathModelResultRef
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class MathModelFlowInputBundle:
    """Input references for a formal math model flow."""

    input_bundle_ref: TypedRef | None = None
    model_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    input_snapshot_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    formula_profile_refs: tuple[MathFormulaProfileRef, ...] = field(default_factory=tuple)
    port_call_refs: tuple[MathModelPortCallRef, ...] = field(default_factory=tuple)
    source_orchestration_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    ref_only: bool = True
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.ref_only is not True:
            raise ValueError("MathModelFlowInputBundle.ref_only must remain true")
        if self.advisory_only is not True:
            raise ValueError("MathModelFlowInputBundle.advisory_only must remain true")
        if not self.schema_version:
            raise ValueError("MathModelFlowInputBundle.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathModelFlowRecommendation:
    """Advisory recommendation emitted by a formal math model flow."""

    recommendation_ref: TypedRef | None = None
    result_ref: TypedRef | None = None
    recommendation_kind: str = "math_model_advice"
    target_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    confidence_ref: TypedRef | None = None
    advisory_only: bool = True
    execution_command: bool = False
    grants_permission: bool = False
    issues_confirmation: bool = False
    grants_lease: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.recommendation_kind:
            raise ValueError("MathModelFlowRecommendation.recommendation_kind cannot be empty")
        if self.advisory_only is not True:
            raise ValueError("MathModelFlowRecommendation.advisory_only must remain true")
        if self.execution_command:
            raise ValueError("MathModelFlowRecommendation cannot be an execution command")
        if self.grants_permission:
            raise ValueError("MathModelFlowRecommendation cannot grant permission")
        if self.issues_confirmation:
            raise ValueError("MathModelFlowRecommendation cannot issue confirmation")
        if self.grants_lease:
            raise ValueError("MathModelFlowRecommendation cannot grant leases")
        if not self.schema_version:
            raise ValueError("MathModelFlowRecommendation.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathModelFlowOutputBundle:
    """Output references for a formal math model flow."""

    output_bundle_ref: TypedRef | None = None
    result_refs: tuple[MathModelResultRef, ...] = field(default_factory=tuple)
    recommendation_refs: tuple[MathModelFlowRecommendation, ...] = field(default_factory=tuple)
    state_update_suggestion_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    trace_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    writes_l2_state: bool = False
    bypasses_l5: bool = False
    produces_action_request: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("MathModelFlowOutputBundle.advisory_only must remain true")
        if self.writes_l2_state:
            raise ValueError("MathModelFlowOutputBundle cannot write L2 state")
        if self.bypasses_l5:
            raise ValueError("MathModelFlowOutputBundle cannot bypass L5")
        if self.produces_action_request:
            raise ValueError("MathModelFlowOutputBundle cannot produce action requests")
        if not self.schema_version:
            raise ValueError("MathModelFlowOutputBundle.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class MathModelOrchestrationFlow:
    """Formal L3 entry for future mathematical model engines."""

    flow_ref: TypedRef | None = None
    flow_name: str = "math_model_orchestration"
    input_bundle: MathModelFlowInputBundle = field(default_factory=MathModelFlowInputBundle)
    output_bundle: MathModelFlowOutputBundle = field(default_factory=MathModelFlowOutputBundle)
    advisory_only: bool = True
    ref_only: bool = True
    formal_engine_path: bool = True
    legacy_heuristic_path: bool = False
    writes_l2_state: bool = False
    bypasses_l5: bool = False
    produces_execution_command: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.flow_name:
            raise ValueError("MathModelOrchestrationFlow.flow_name cannot be empty")
        if self.advisory_only is not True:
            raise ValueError("MathModelOrchestrationFlow.advisory_only must remain true")
        if self.ref_only is not True:
            raise ValueError("MathModelOrchestrationFlow.ref_only must remain true")
        if self.formal_engine_path is not True:
            raise ValueError("MathModelOrchestrationFlow.formal_engine_path must remain true")
        if self.legacy_heuristic_path:
            raise ValueError("MathModelOrchestrationFlow cannot be the legacy heuristic path")
        if self.writes_l2_state:
            raise ValueError("MathModelOrchestrationFlow cannot write L2 state")
        if self.bypasses_l5:
            raise ValueError("MathModelOrchestrationFlow cannot bypass L5")
        if self.produces_execution_command:
            raise ValueError("MathModelOrchestrationFlow cannot produce execution commands")
        if not self.schema_version:
            raise ValueError("MathModelOrchestrationFlow.schema_version cannot be empty")

    def declare_output(self, output_bundle: MathModelFlowOutputBundle) -> "MathModelOrchestrationFlow":
        """Return a new flow value carrying declared output references only."""

        return MathModelOrchestrationFlow(
            flow_ref=self.flow_ref,
            flow_name=self.flow_name,
            input_bundle=self.input_bundle,
            output_bundle=output_bundle,
        )
