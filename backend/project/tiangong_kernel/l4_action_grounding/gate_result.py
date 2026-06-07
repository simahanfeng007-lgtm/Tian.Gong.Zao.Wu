"""L4 第二阶段动作落地门控结果。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef

from .audit_requirement import AuditRequirementRef
from .failure import ActionGroundingFailure
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true
from .permit_ref import PermitConsumptionRef
from .permit_validation import PermitValidationResult, PermitValidationStatus


@dataclass(frozen=True, slots=True)
class ActionGroundingPermitRequirement:
    requirement_ref: TypedRef
    requested_l5_permit: bool = True
    requirement_only: bool = True
    l4_grants_permission: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.requested_l5_permit, "ActionGroundingPermitRequirement.requested_l5_permit")
        ensure_true(self.requirement_only, "ActionGroundingPermitRequirement.requirement_only")
        ensure_false(self.l4_grants_permission, "ActionGroundingPermitRequirement.l4_grants_permission")
        ensure_schema_version(self.schema_version, "ActionGroundingPermitRequirement.schema_version")


@dataclass(frozen=True, slots=True)
class ActionGroundingBoundaryRequirement:
    requirement_ref: TypedRef
    requested_boundary_ref: bool = True
    requirement_only: bool = True
    l4_boundary_decision_made: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.requested_boundary_ref, "ActionGroundingBoundaryRequirement.requested_boundary_ref")
        ensure_true(self.requirement_only, "ActionGroundingBoundaryRequirement.requirement_only")
        ensure_false(self.l4_boundary_decision_made, "ActionGroundingBoundaryRequirement.l4_boundary_decision_made")
        ensure_schema_version(self.schema_version, "ActionGroundingBoundaryRequirement.schema_version")


@dataclass(frozen=True, slots=True)
class ActionGroundingGateResult:
    """动作落地门控结果。

    allowed_for_grounding 只表示结构上可进入动作落地承载，不表示 L4 授权。
    """

    gate_result_ref: TypedRef
    status: PermitValidationStatus
    allowed_for_grounding: bool = False
    validation_result: PermitValidationResult | None = None
    normalized_failure: ActionGroundingFailure | None = None
    permit_consumption_summary: PermitConsumptionRef | None = None
    audit_requirement_ref: AuditRequirementRef | None = None
    boundary_feedback_ref: TypedRef | None = None
    boundary_feedback_summary: str = ""
    gate_result_only: bool = True
    l4_authorized_action: bool = False
    real_action_performed: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.boundary_feedback_summary, "ActionGroundingGateResult.boundary_feedback_summary")
        ensure_true(self.gate_result_only, "ActionGroundingGateResult.gate_result_only")
        ensure_false(self.l4_authorized_action, "ActionGroundingGateResult.l4_authorized_action")
        ensure_false(self.real_action_performed, "ActionGroundingGateResult.real_action_performed")
        ensure_schema_version(self.schema_version, "ActionGroundingGateResult.schema_version")


ExecutionGateResult = ActionGroundingGateResult
