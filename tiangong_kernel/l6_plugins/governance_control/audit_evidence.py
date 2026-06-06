"""Audit evidence declarations for L6 phase5 governance-control."""

from __future__ import annotations

from dataclasses import dataclass, field

from .common import GovernanceArtifactBase, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_score


@dataclass(frozen=True)
class AuditRequirement(GovernanceArtifactBase):
    object_ref: str = "audit:l6_phase5_requirement"
    requirement_only: bool = True
    audit_store_write: bool = False
    evidence_index_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        for field_name in ("requirement_only", "audit_store_write", "evidence_index_required"):
            ensure_bool(getattr(self, field_name), f"AuditRequirement.{field_name}")
        if not self.requirement_only or self.audit_store_write or not self.evidence_index_required:
            raise ValueError("AuditRequirement is not an audit write")


@dataclass(frozen=True)
class GovernanceEvidenceIndex(GovernanceArtifactBase):
    object_ref: str = "evidence:l6_phase5_governance_index"
    evidence_item_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase5_item",))
    complete_evidence_public: bool = False
    fabricated_evidence: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.evidence_item_refs, "GovernanceEvidenceIndex.evidence_item_refs", required=True)
        ensure_bool(self.complete_evidence_public, "GovernanceEvidenceIndex.complete_evidence_public")
        ensure_bool(self.fabricated_evidence, "GovernanceEvidenceIndex.fabricated_evidence")
        if self.complete_evidence_public or self.fabricated_evidence:
            raise ValueError("Evidence index must be ref-only and truthful")


@dataclass(frozen=True)
class GovernanceTraceRef(GovernanceArtifactBase):
    object_ref: str = "ref:l6_phase5_governance_trace"
    trace_ref_value: str = "ref:l6_phase5_trace_chain"
    trace_is_database_write: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.trace_ref_value, "GovernanceTraceRef.trace_ref_value")
        ensure_bool(self.trace_is_database_write, "GovernanceTraceRef.trace_is_database_write")
        if self.trace_is_database_write:
            raise ValueError("GovernanceTraceRef cannot write trace database")


@dataclass(frozen=True)
class ResponsibilityChainRef(GovernanceArtifactBase):
    object_ref: str = "responsibility:l6_phase5_chain"
    chain_refs: tuple[str, ...] = field(default_factory=lambda: ("responsibility:l6_phase5_source", "responsibility:l3_l5_review"))
    public_full_chain: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.chain_refs, "ResponsibilityChainRef.chain_refs", required=True)
        ensure_bool(self.public_full_chain, "ResponsibilityChainRef.public_full_chain")
        if self.public_full_chain:
            raise ValueError("Responsibility chain must be minimally disclosed")


@dataclass(frozen=True)
class TamperEvidenceHint(GovernanceArtifactBase):
    object_ref: str = "evidence:l6_phase5_tamper_hint"
    digest_ref: str = "digest:l6_phase5_tamper_digest"
    writes_tamper_log: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.digest_ref, "TamperEvidenceHint.digest_ref")
        ensure_bool(self.writes_tamper_log, "TamperEvidenceHint.writes_tamper_log")
        if self.writes_tamper_log:
            raise ValueError("TamperEvidenceHint cannot write tamper log")


@dataclass(frozen=True)
class AuditCoverageHint(GovernanceArtifactBase):
    object_ref: str = "hint:l6_phase5_audit_coverage"
    candidate_refs_covered: tuple[str, ...] = field(default_factory=lambda: ("ref:l6_phase5_candidate",))
    all_high_risk_has_evidence: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.candidate_refs_covered, "AuditCoverageHint.candidate_refs_covered", required=True)
        ensure_bool(self.all_high_risk_has_evidence, "AuditCoverageHint.all_high_risk_has_evidence")
        if not self.all_high_risk_has_evidence:
            raise ValueError("High-risk governance candidates must carry evidence refs")


@dataclass(frozen=True)
class EvidenceCompletenessScore(GovernanceArtifactBase):
    object_ref: str = "score:l6_phase5_evidence_completeness"
    completeness_score: float = 0.9
    evidence_index_ref: str = "evidence:l6_phase5_governance_index"
    responsibility_chain_ref: str = "responsibility:l6_phase5_chain"
    tamper_evidence_ref: str = "evidence:l6_phase5_tamper_hint"
    missing_evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    score_is_permit: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_score(self.completeness_score, "EvidenceCompletenessScore.completeness_score")
        for field_name in ("evidence_index_ref", "responsibility_chain_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"EvidenceCompletenessScore.{field_name}")
        ensure_ref_items(self.missing_evidence_refs, "EvidenceCompletenessScore.missing_evidence_refs")
        ensure_bool(self.score_is_permit, "EvidenceCompletenessScore.score_is_permit")
        if self.score_is_permit:
            raise ValueError("Evidence completeness score is not permit")
