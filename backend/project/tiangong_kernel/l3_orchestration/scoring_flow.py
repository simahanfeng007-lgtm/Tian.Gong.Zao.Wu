"""Formal scoring flow references for L3."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .math_formula_profile_ref import MathFormulaProfileRef, MathModelPortCallRef, MathModelResultRef
from .math_model_flow import MathModelFlowInputBundle, MathModelFlowOutputBundle, MathModelOrchestrationFlow
from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


@dataclass(frozen=True, slots=True)
class ScoringFlow:
    """Formal advisory scoring flow; it does not contain a formula."""

    flow_ref: TypedRef | None = None
    flow_name: str = "scoring_flow"
    scoring_domain: str = "generic"
    candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    formula_profile_ref: MathFormulaProfileRef | None = None
    port_call_ref: MathModelPortCallRef | None = None
    result_ref: MathModelResultRef | None = None
    advisory_only: bool = True
    formal_engine_path: bool = True
    compatibility_only: bool = False
    contains_formula: bool = False
    writes_l2_state: bool = False
    bypasses_l5: bool = False
    produces_execution_command: bool = False
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not self.flow_name:
            raise ValueError("ScoringFlow.flow_name cannot be empty")
        if not self.scoring_domain:
            raise ValueError("ScoringFlow.scoring_domain cannot be empty")
        if self.advisory_only is not True:
            raise ValueError("ScoringFlow.advisory_only must remain true")
        if self.formal_engine_path is not True:
            raise ValueError("ScoringFlow.formal_engine_path must remain true")
        if self.compatibility_only:
            raise ValueError("ScoringFlow is the formal path, not a compatibility profile")
        if self.contains_formula:
            raise ValueError("ScoringFlow cannot contain formulas")
        if self.writes_l2_state:
            raise ValueError("ScoringFlow cannot write L2 state")
        if self.bypasses_l5:
            raise ValueError("ScoringFlow cannot bypass L5")
        if self.produces_execution_command:
            raise ValueError("ScoringFlow cannot produce execution commands")
        if not self.schema_version:
            raise ValueError("ScoringFlow.schema_version cannot be empty")

    def as_orchestration_flow(self) -> MathModelOrchestrationFlow:
        """Expose this scoring flow as a formal math model flow reference."""

        input_bundle = MathModelFlowInputBundle(
            formula_profile_refs=() if self.formula_profile_ref is None else (self.formula_profile_ref,),
            port_call_refs=() if self.port_call_ref is None else (self.port_call_ref,),
            source_orchestration_refs=() if self.flow_ref is None else (self.flow_ref,),
        )
        output_bundle = MathModelFlowOutputBundle(
            result_refs=() if self.result_ref is None else (self.result_ref,),
        )
        return MathModelOrchestrationFlow(
            flow_ref=self.flow_ref,
            flow_name=f"{self.scoring_domain}_math_model_orchestration",
            input_bundle=input_bundle,
            output_bundle=output_bundle,
        )
