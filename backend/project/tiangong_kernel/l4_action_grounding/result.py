"""L4 动作落地结果对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .failure import ActionGroundingFailure
from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


class ActionGroundingResultKind(str, Enum):
    SIMULATED = "simulated"
    DRY_RUN = "dry_run"
    NO_OP = "no_op"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class ActionGroundingResult:
    """标准结果 envelope；real_action_performed 在第一阶段必须为 False。"""

    result_ref: TypedRef
    result_kind: ActionGroundingResultKind
    source_request_ref: TypedRef | None = None
    gate_result_ref: TypedRef | None = None
    gate_status_hint: str = ""
    adapter_output_ref: TypedRef | None = None
    adapter_selection_result_ref: TypedRef | None = None
    adapter_mode_hint: str = ""
    output_summary: str = ""
    payload_items: tuple[tuple[str, str], ...] = field(default_factory=tuple)
    failure: ActionGroundingFailure | None = None
    simulated: bool = True
    real_action_performed: bool = False
    result_envelope_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_short_text(self.gate_status_hint, "ActionGroundingResult.gate_status_hint", 128)
        ensure_short_text(self.adapter_mode_hint, "ActionGroundingResult.adapter_mode_hint", 128)
        ensure_short_text(self.output_summary, "ActionGroundingResult.output_summary")
        for key, value in self.payload_items:
            ensure_short_text(key, "ActionGroundingResult.payload_items key", 128)
            ensure_short_text(value, "ActionGroundingResult.payload_items value")
        ensure_false(self.real_action_performed, "ActionGroundingResult.real_action_performed")
        ensure_true(self.result_envelope_only, "ActionGroundingResult.result_envelope_only")
        ensure_schema_version(self.schema_version, "ActionGroundingResult.schema_version")
