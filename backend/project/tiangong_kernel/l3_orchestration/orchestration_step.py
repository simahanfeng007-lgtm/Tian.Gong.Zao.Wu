"""L3 编排步骤对象，只表达计划步骤与引用关系。"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION, OrchestrationIdentity
from .orchestration_status import OrchestrationStatus


class OrchestrationStepKind(str, Enum):
    """第一阶段允许出现的通用步骤类别。"""

    UNKNOWN = "unknown"
    COLLECT_STATE_REFS = "collect_state_refs"
    PREPARE_MATH_INPUT = "prepare_math_input"
    RECORD_EVALUATION = "record_evaluation"
    RANK_ROUTE = "rank_route"
    ADVISE_TRANSITION = "advise_transition"
    PREPARE_UPPER_LAYER_REQUEST = "prepare_upper_layer_request"


@dataclass(frozen=True, slots=True)
class OrchestrationStep:
    """编排步骤事实。

    作用：记录一个步骤的输入引用、输出引用、依赖步骤和建议后续步骤。
    边界：步骤仅为计划片段，不承载真实动作或外部系统句柄。
    """

    identity: OrchestrationIdentity
    status: OrchestrationStatus
    step_ref: TypedRef | None = None
    step_kind: OrchestrationStepKind = OrchestrationStepKind.UNKNOWN
    input_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    output_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    depends_on_step_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    suggested_next_step_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    summary: str = ""
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.advisory_only is not True:
            raise ValueError("OrchestrationStep.advisory_only must remain true in L3 phase 1")
        if len(self.summary) > 512:
            raise ValueError("OrchestrationStep.summary must be a short summary")
        if not self.schema_version:
            raise ValueError("OrchestrationStep.schema_version cannot be empty")
