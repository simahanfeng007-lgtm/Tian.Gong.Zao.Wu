"""L6 phase4 audit evidence and responsibility-chain contracts.

These are not audit database records.  They are inert references carried by
phase4 candidates so downstream L5 audit governance can make the real decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l6_plugins.common._common import L6_COMMON_SCHEMA_VERSION, ensure_bool, ensure_no_live_or_sensitive_text, ensure_ref_items, ensure_ref_text, ensure_schema_version, stable_digest
from .common import L6_PHASE4
from .projection import CognitiveOutputBase


@dataclass(frozen=True)
class CognitiveAuditEnvelope:
    audit_envelope_ref: str = "audit:l6_phase4_cognitive_audit_envelope"
    phase: str = L6_PHASE4
    actor_ref: str = "l6:l6_phase4_cognitive_plugin"
    scope_ref: str = "l6:l6_phase4_cognitive_scope"
    trace_ref: str = "ref:l6_phase4_cognitive_trace"
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_cognitive_evidence",))
    responsibility_chain_ref: str = "responsibility:l6_phase4_cognitive_chain"
    accountability_ref: str = "responsibility:l6_phase4_accountability"
    tamper_evidence_ref: str = "evidence:l6_phase4_tamper_evidence"
    redacted_evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_redacted_evidence",))
    digest_summary: str = "summary:l6_phase4_audit_envelope"
    writes_audit_store: bool = False
    grants_authorization: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.audit_envelope_ref, "CognitiveAuditEnvelope.audit_envelope_ref")
        if self.phase != L6_PHASE4:
            raise ValueError("CognitiveAuditEnvelope.phase must be L6 phase4")
        for field_name in ("actor_ref", "scope_ref", "trace_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, field_name), f"CognitiveAuditEnvelope.{field_name}")
        ensure_ref_items(self.evidence_refs, "CognitiveAuditEnvelope.evidence_refs", required=True)
        ensure_ref_items(self.redacted_evidence_refs, "CognitiveAuditEnvelope.redacted_evidence_refs", required=True)
        ensure_no_live_or_sensitive_text(self.digest_summary, "CognitiveAuditEnvelope.digest_summary")
        ensure_bool(self.writes_audit_store, "CognitiveAuditEnvelope.writes_audit_store")
        ensure_bool(self.grants_authorization, "CognitiveAuditEnvelope.grants_authorization")
        if self.writes_audit_store or self.grants_authorization:
            raise ValueError("cognitive audit envelope is not an audit write or authorization")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class MemoryCandidateEvidenceIndex(CognitiveAuditEnvelope):
    audit_envelope_ref: str = "audit:l6_phase4_memory_candidate_evidence_index"
    scope_ref: str = "l6:l6_phase4_memory_candidate_scope"
    memory_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_memory_candidate",))

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.memory_candidate_refs, "MemoryCandidateEvidenceIndex.memory_candidate_refs", required=True)


@dataclass(frozen=True)
class CandidateFactAuditEnvelope(CognitiveAuditEnvelope):
    audit_envelope_ref: str = "audit:l6_phase4_candidate_fact_audit_envelope"
    scope_ref: str = "l6:l6_phase4_candidate_fact_scope"
    candidate_fact_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_candidate_fact",))
    l2_write_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.candidate_fact_refs, "CandidateFactAuditEnvelope.candidate_fact_refs", required=True)
        ensure_bool(self.l2_write_allowed, "CandidateFactAuditEnvelope.l2_write_allowed")
        if self.l2_write_allowed:
            raise ValueError("candidate fact audit envelope cannot write L2")


@dataclass(frozen=True)
class ReflectionLearningAuditRecord(CognitiveAuditEnvelope):
    audit_envelope_ref: str = "audit:l6_phase4_reflection_learning_audit_record"
    scope_ref: str = "l6:l6_phase4_reflection_learning_scope"
    learning_candidate_refs: tuple[str, ...] = field(default_factory=lambda: ("projection:l6_phase4_learning_need",))
    auto_repair_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.learning_candidate_refs, "ReflectionLearningAuditRecord.learning_candidate_refs", required=True)
        ensure_bool(self.auto_repair_allowed, "ReflectionLearningAuditRecord.auto_repair_allowed")
        if self.auto_repair_allowed:
            raise ValueError("reflection learning audit record cannot allow auto repair")


@dataclass(frozen=True)
class CognitiveReentryAuditEnvelope(CognitiveAuditEnvelope):
    audit_envelope_ref: str = "audit:l6_phase4_reentry_audit_envelope"
    scope_ref: str = "l6:l6_phase4_reentry_scope"
    reentry_envelope_refs: tuple[str, ...] = field(default_factory=lambda: ("l6:l6_phase4_cognitive_reentry_envelope",))
    l3_l5_review_required: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.reentry_envelope_refs, "CognitiveReentryAuditEnvelope.reentry_envelope_refs", required=True)
        ensure_bool(self.l3_l5_review_required, "CognitiveReentryAuditEnvelope.l3_l5_review_required")
        if not self.l3_l5_review_required:
            raise ValueError("reentry audit envelope must require L3/L5 review")


@dataclass(frozen=True)
class L6Phase4AuditPublicProjection(CognitiveOutputBase):
    output_ref: str = "public:l6_phase4_audit_public_projection"
    plugin_ref: str = "l6_phase4:audit_evidence"
    redacted_evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_redacted_evidence",))
    exposes_complete_evidence: bool = False
    exposes_sensitive_context: bool = False
    exposes_real_paths: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.redacted_evidence_refs, "L6Phase4AuditPublicProjection.redacted_evidence_refs", required=True)
        for field_name in ("exposes_complete_evidence", "exposes_sensitive_context", "exposes_real_paths"):
            ensure_bool(getattr(self, field_name), f"L6Phase4AuditPublicProjection.{field_name}")
        if self.exposes_complete_evidence or self.exposes_sensitive_context or self.exposes_real_paths:
            raise ValueError("audit public projection must be minimal and redacted")


@dataclass(frozen=True)
class AuditCoverageReport(CognitiveOutputBase):
    output_ref: str = "projection:l6_phase4_audit_coverage_report"
    plugin_ref: str = "l6_phase4:audit_evidence"
    all_candidates_have_evidence: bool = True
    all_candidates_have_trace: bool = True
    all_candidates_have_responsibility_chain: bool = True
    all_candidates_have_tamper_evidence: bool = True

    def __post_init__(self) -> None:
        super().__post_init__()
        fields = (
            "all_candidates_have_evidence",
            "all_candidates_have_trace",
            "all_candidates_have_responsibility_chain",
            "all_candidates_have_tamper_evidence",
        )
        for field_name in fields:
            ensure_bool(getattr(self, field_name), f"AuditCoverageReport.{field_name}")
        if not all(getattr(self, field_name) for field_name in fields):
            raise ValueError("audit coverage report is blocking when any audit chain field is missing")
