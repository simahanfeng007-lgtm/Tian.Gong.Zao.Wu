"""L2 观察投影状态对象。

作用：记录观察帧、事件流、指标、审计和质量状态压缩后的局部结构化投影事实。
边界：这是状态对象，不是观察器、采集器或监听器，不生成聊天文本、最终提示词或下一步行动。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ObservationProjectionKind(str, Enum):
    """观察投影类型。

    作用：表达运行、任务、Skill、工具、边界、安全、质量或审计观察的局部投影标签。
    边界：这是状态标签，不生成全局投影，不做编排或推理。
    """

    RUN_OBSERVATION_PROJECTION = "run_observation_projection"
    TASK_OBSERVATION_PROJECTION = "task_observation_projection"
    SKILL_OBSERVATION_PROJECTION = "skill_observation_projection"
    TOOL_OBSERVATION_PROJECTION = "tool_observation_projection"
    BOUNDARY_OBSERVATION_PROJECTION = "boundary_observation_projection"
    SECURITY_OBSERVATION_PROJECTION = "security_observation_projection"
    QUALITY_OBSERVATION_PROJECTION = "quality_observation_projection"
    AUDIT_OBSERVATION_PROJECTION = "audit_observation_projection"
    UNKNOWN = "unknown"


class ObservationProjectionStatus(str, Enum):
    """观察投影状态。

    作用：表达观察投影已构建、部分、过期、脱敏、冲突或未知状态。
    边界：这是状态对象的状态标签，不生成自然语言，不选择下一步行动。
    """

    BUILT = "built"
    PARTIAL = "partial"
    STALE = "stale"
    REDACTED = "redacted"
    CONFLICTED = "conflicted"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ObservationProjectionState:
    """观察投影状态。

    作用：记录投影引用、来源帧、事件流、指标、审计、质量、目标对象和结构化短摘要。
    边界：这是状态对象，不是观察器、采集器或监听器，不生成聊天文本、最终提示词或下一步行动。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    projection_ref: TypedRef | None = None
    projection_kind: ObservationProjectionKind = ObservationProjectionKind.UNKNOWN
    projection_status: ObservationProjectionStatus = ObservationProjectionStatus.UNKNOWN
    source_frame_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_stream_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_metric_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    source_audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    quality_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    projected_subject_ref: TypedRef | None = None
    projected_subject_kind: str | None = None
    projected_status_summary: str | None = None
    projected_observation_summary: str | None = None
    redaction_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    conflict_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("projected_subject_kind", self.projected_subject_kind),
            ("projected_status_summary", self.projected_status_summary),
            ("projected_observation_summary", self.projected_observation_summary),
        ):
            if value == "":
                raise ValueError(f"ObservationProjectionState.{name} cannot be empty when provided")
            if value is not None and len(value) > 512:
                raise ValueError(f"ObservationProjectionState.{name} must be a short summary")
        if not self.schema_version:
            raise ValueError("ObservationProjectionState.schema_version cannot be empty")
