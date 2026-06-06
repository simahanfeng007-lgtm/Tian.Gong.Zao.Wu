"""L3 第五阶段边界路径建议与排序。

Denial / Degrade / Confirm / Retry / Pending 等均为路径建议，不是真实裁决或真实动作。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l0_primitives.identity import TypedRef

from .orchestration_identity import L3_ORCHESTRATION_SCHEMA_VERSION


class BoundaryRouteKind(str, Enum):
    """边界路径建议类别。"""

    DENIAL_PATH = "denial_path"
    DEGRADE_PATH = "degrade_path"
    CONFIRMATION_PATH = "confirmation_path"
    RETRY_PATH = "retry_path"
    ESCALATION_PATH = "escalation_path"
    FALLBACK_PATH = "fallback_path"
    CLARIFICATION_PATH = "clarification_path"
    PENDING_PATH = "pending_path"
    RESUME_PATH = "resume_path"


def _ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def _ensure_unit_interval(value: float, field_name: str) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{field_name} must be between 0.0 and 1.0")


def _ensure_advisory(flag: bool, field_name: str) -> None:
    if flag is not True:
        raise ValueError(f"{field_name} must remain true")


@dataclass(frozen=True, slots=True)
class BoundaryPathAdviceBase:
    """边界路径建议基类。"""

    advice_ref: TypedRef
    boundary_request_ref: TypedRef
    route_kind: BoundaryRouteKind
    priority_score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    related_request_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    preserved_context_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    reason_summary: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_unit_interval(self.priority_score, f"{self.__class__.__name__}.priority_score")
        for item in self.reason_codes:
            _ensure_short_text(item, f"{self.__class__.__name__}.reason_codes", 128)
        _ensure_short_text(self.reason_summary, f"{self.__class__.__name__}.reason_summary")
        _ensure_advisory(self.advisory_only, f"{self.__class__.__name__}.advisory_only")
        if not self.schema_version:
            raise ValueError(f"{self.__class__.__name__}.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryDenialPathAdvice(BoundaryPathAdviceBase):
    route_kind: BoundaryRouteKind = BoundaryRouteKind.DENIAL_PATH


@dataclass(frozen=True, slots=True)
class BoundaryDegradePathAdvice(BoundaryPathAdviceBase):
    route_kind: BoundaryRouteKind = BoundaryRouteKind.DEGRADE_PATH


@dataclass(frozen=True, slots=True)
class BoundaryConfirmationPathAdvice(BoundaryPathAdviceBase):
    route_kind: BoundaryRouteKind = BoundaryRouteKind.CONFIRMATION_PATH


@dataclass(frozen=True, slots=True)
class BoundaryRetryPathAdvice(BoundaryPathAdviceBase):
    route_kind: BoundaryRouteKind = BoundaryRouteKind.RETRY_PATH


@dataclass(frozen=True, slots=True)
class BoundaryEscalationPathAdvice(BoundaryPathAdviceBase):
    route_kind: BoundaryRouteKind = BoundaryRouteKind.ESCALATION_PATH


@dataclass(frozen=True, slots=True)
class BoundaryFallbackPathAdvice(BoundaryPathAdviceBase):
    route_kind: BoundaryRouteKind = BoundaryRouteKind.FALLBACK_PATH


@dataclass(frozen=True, slots=True)
class BoundaryClarificationPathAdvice(BoundaryPathAdviceBase):
    route_kind: BoundaryRouteKind = BoundaryRouteKind.CLARIFICATION_PATH


@dataclass(frozen=True, slots=True)
class BoundaryPendingAdvice(BoundaryPathAdviceBase):
    route_kind: BoundaryRouteKind = BoundaryRouteKind.PENDING_PATH


@dataclass(frozen=True, slots=True)
class BoundaryResumeAdvice(BoundaryPathAdviceBase):
    route_kind: BoundaryRouteKind = BoundaryRouteKind.RESUME_PATH


@dataclass(frozen=True, slots=True)
class BoundaryRouteCandidate:
    """边界路径候选；只用于排序建议。"""

    route_ref: TypedRef
    route_kind: BoundaryRouteKind
    boundary_request_ref: TypedRef
    readiness_score: float = 0.0
    evidence_score: float = 0.0
    clarification_need_score: float = 0.0
    caution_score: float = 0.0
    continuity_score: float = 0.0
    reason_codes: tuple[str, ...] = field(default_factory=tuple)
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("readiness_score", self.readiness_score),
            ("evidence_score", self.evidence_score),
            ("clarification_need_score", self.clarification_need_score),
            ("caution_score", self.caution_score),
            ("continuity_score", self.continuity_score),
        ):
            _ensure_unit_interval(value, f"BoundaryRouteCandidate.{name}")
        for item in self.reason_codes:
            _ensure_short_text(item, "BoundaryRouteCandidate.reason_codes", 128)
        _ensure_advisory(self.advisory_only, "BoundaryRouteCandidate.advisory_only")
        if not self.schema_version:
            raise ValueError("BoundaryRouteCandidate.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class BoundaryRouteRanking:
    """边界路径排序结果；不是裁决结果。"""

    ranking_ref: TypedRef
    candidates: tuple[BoundaryRouteCandidate, ...] = field(default_factory=tuple)
    target_scores: tuple[tuple[TypedRef, float], ...] = field(default_factory=tuple)
    top_route_ref: TypedRef | None = None
    ranking_reason: str = ""
    advisory_only: bool = True
    schema_version: str = L3_ORCHESTRATION_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _ensure_short_text(self.ranking_reason, "BoundaryRouteRanking.ranking_reason")
        _ensure_advisory(self.advisory_only, "BoundaryRouteRanking.advisory_only")
        if self.candidates and self.top_route_ref is None:
            raise ValueError("BoundaryRouteRanking.top_route_ref is required when candidates exist")
        if not self.schema_version:
            raise ValueError("BoundaryRouteRanking.schema_version cannot be empty")


def _boundary_candidate_score(candidate: BoundaryRouteCandidate) -> float:
    value = (
        candidate.readiness_score * 0.34
        + candidate.evidence_score * 0.22
        + candidate.continuity_score * 0.18
        + (1.0 - candidate.clarification_need_score) * 0.18
        + candidate.caution_score * 0.08
    )
    return round(min(max(value, 0.0), 1.0), 6)


def build_boundary_route_ranking(ranking_ref: TypedRef, candidates: tuple[BoundaryRouteCandidate, ...]) -> BoundaryRouteRanking:
    """生成稳定边界路径排序；不提交审查。"""

    scored = tuple((candidate.route_ref, _boundary_candidate_score(candidate), candidate) for candidate in candidates)
    ordered = tuple(sorted(scored, key=lambda item: (-item[1], item[0].ref_id.value)))
    return BoundaryRouteRanking(
        ranking_ref=ranking_ref,
        candidates=tuple(item[2] for item in ordered),
        target_scores=tuple((item[0], item[1]) for item in ordered),
        top_route_ref=ordered[0][0] if ordered else None,
        ranking_reason="weighted boundary route readiness and evidence sufficiency",
    )
