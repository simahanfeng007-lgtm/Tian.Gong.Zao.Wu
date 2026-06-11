"""Resume references for L4 phase 6."""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ExecutionResumeRef:
    """Resume reference only; L3 and the LLM decide continuation."""

    resume_ref: TypedRef
    action_ref: TypedRef
    step_ref: TypedRef | None = None
    resume_hint: str = "resume_ref_only"
    ref_only: bool = True
    executes_resume: bool = False
    modifies_l3_plan: bool = False
    writes_l2_state: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.resume_hint, "ExecutionResumeRef.resume_hint")
        ensure_true(self.ref_only, "ExecutionResumeRef.ref_only")
        ensure_false(self.executes_resume, "ExecutionResumeRef.executes_resume")
        ensure_false(self.modifies_l3_plan, "ExecutionResumeRef.modifies_l3_plan")
        ensure_false(self.writes_l2_state, "ExecutionResumeRef.writes_l2_state")
        ensure_schema_version(self.schema_version, "ExecutionResumeRef.schema_version")
