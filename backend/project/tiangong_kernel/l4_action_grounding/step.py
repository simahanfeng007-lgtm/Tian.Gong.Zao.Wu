"""L4 动作落地步骤对象。"""

from __future__ import annotations

from dataclasses import dataclass

from tiangong_kernel.l0_primitives.identity import TypedRef
from tiangong_kernel.l3_orchestration.execution_request import ExecutionStepRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class ActionGroundingStep:
    """动作落地步骤；不启动任何真实动作。"""

    step_ref: TypedRef
    source_l3_step_ref: ExecutionStepRef | None = None
    action_label: str = "grounding_step"
    sequence_index: int = 0
    adapter_kind_hint: str = "none"
    adapter_descriptor_ref: TypedRef | None = None
    adapter_selection_result_ref: TypedRef | None = None
    l5_permit_ref: TypedRef | None = None
    live_action_enabled: bool = False
    step_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.action_label, "ActionGroundingStep.action_label", 128)
        ensure_short_text(self.adapter_kind_hint, "ActionGroundingStep.adapter_kind_hint", 128)
        if self.sequence_index < 0:
            raise ValueError("ActionGroundingStep.sequence_index cannot be negative")
        ensure_false(self.live_action_enabled, "ActionGroundingStep.live_action_enabled")
        ensure_true(self.step_only, "ActionGroundingStep.step_only")
        ensure_schema_version(self.schema_version, "ActionGroundingStep.schema_version")
