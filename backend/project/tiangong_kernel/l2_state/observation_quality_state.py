"""L2 观察质量状态对象。

作用：记录外部给出的观察完整性、新鲜度、一致性、可信度、脱敏安全和冲突状态。
边界：这是状态对象，不是观察器、采集器或监听器，不计算评分、不解决冲突、不决定可用性。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .base_state import L2_STATE_SCHEMA_VERSION, L2StateMetadata
from .state_identity import L2StateIdentity
from .state_status import L2StateStatus


class ObservationQualityDimension(str, Enum):
    """观察质量维度。

    作用：表达完整性、新鲜度、一致性、可信度、脱敏安全、顺序、延迟、覆盖或冲突等级维度。
    边界：这是状态标签，不计算质量分，不解决冲突。
    """

    COMPLETENESS = "completeness"
    FRESHNESS = "freshness"
    CONSISTENCY = "consistency"
    TRUSTWORTHINESS = "trustworthiness"
    REDACTION_SAFETY = "redaction_safety"
    ORDERING = "ordering"
    LATENCY = "latency"
    COVERAGE = "coverage"
    CONFLICT_LEVEL = "conflict_level"
    UNKNOWN = "unknown"


class ObservationQualityStatus(str, Enum):
    """观察质量状态。

    作用：表达外部报告的良好、可接受、部分、低、冲突、不安全或未知质量状态。
    边界：这是状态对象的状态标签，不自动决定观察是否可用。
    """

    GOOD = "good"
    ACCEPTABLE = "acceptable"
    PARTIAL = "partial"
    LOW = "low"
    CONFLICTED = "conflicted"
    UNSAFE = "unsafe"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ObservationQualityState:
    """观察质量状态。

    作用：记录质量引用、维度、状态、短标签、短摘要、帧、指标、审计、边界和安全引用。
    边界：这是状态对象，不是观察器、采集器或监听器，不计算评分、不解决冲突、不裁决可用性。
    """

    identity: L2StateIdentity
    status: L2StateStatus
    quality_ref: TypedRef | None = None
    quality_dimension: ObservationQualityDimension = ObservationQualityDimension.UNKNOWN
    quality_status: ObservationQualityStatus = ObservationQualityStatus.UNKNOWN
    quality_label: str | None = None
    quality_summary: str | None = None
    evidence_frame_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_metric_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    evidence_audit_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    security_state_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    metadata: L2StateMetadata | None = None
    schema_version: str = L2_STATE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (("quality_label", self.quality_label), ("quality_summary", self.quality_summary)):
            if value == "":
                raise ValueError(f"ObservationQualityState.{name} cannot be empty when provided")
        if self.quality_summary is not None and len(self.quality_summary) > 512:
            raise ValueError("ObservationQualityState.quality_summary must be a short summary")
        if not self.schema_version:
            raise ValueError("ObservationQualityState.schema_version cannot be empty")
