"""Canonical memory-field and memory-review objects for L6 phase4.

These objects satisfy the L6 fourth-stage memory/forgetting freeze口径:
working/episodic/semantic/procedural/self/runtime memory are represented as
candidate fields only. User explicit forget requests are carried as priority
hints into legal deletion review, tombstone and active recall suppression; no
object here deletes or mutates memory.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l6_plugins.common._common import (
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)
from ..common import CognitiveOutputKind
from ..projection import CognitiveOutputBase, MemoryPromotionReviewCandidate, MemoryRecallReentryCandidate


class CanonicalMemoryField(str, Enum):
    WORKING_MEMORY = "working_memory"
    EPISODIC_MEMORY = "episodic_memory"
    SEMANTIC_MEMORY = "semantic_memory"
    PROCEDURAL_MEMORY = "procedural_memory"
    SELF_MEMORY = "self_memory"
    RUNTIME_MEMORY = "runtime_memory"


@dataclass(frozen=True)
class CanonicalMemoryFieldSet:
    field_set_ref: str = "memory:l6_phase4_canonical_memory_field_set"
    field_names: tuple[CanonicalMemoryField | str, ...] = tuple(field for field in CanonicalMemoryField)
    l2_fact_write_allowed: bool = False
    memory_write_allowed: bool = False
    memory_delete_allowed: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.field_set_ref, "CanonicalMemoryFieldSet.field_set_ref")
        if not isinstance(self.field_names, tuple) or not self.field_names:
            raise ValueError("CanonicalMemoryFieldSet.field_names must be non-empty tuple")
        object.__setattr__(self, "field_names", tuple(CanonicalMemoryField(field) for field in self.field_names))
        expected = tuple(CanonicalMemoryField)
        if tuple(self.field_names) != expected:
            raise ValueError("CanonicalMemoryFieldSet must preserve the six frozen memory fields")
        for field_name in ("l2_fact_write_allowed", "memory_write_allowed", "memory_delete_allowed"):
            ensure_bool(getattr(self, field_name), f"CanonicalMemoryFieldSet.{field_name}")
        if self.l2_fact_write_allowed or self.memory_write_allowed or self.memory_delete_allowed:
            raise ValueError("L6 canonical memory field set is descriptive only")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class MemoryRecallCandidate(MemoryRecallReentryCandidate):
    output_ref: str = "projection:l6_phase4_memory_recall_candidate"
    memory_field: CanonicalMemoryField | str = CanonicalMemoryField.WORKING_MEMORY
    raw_memory_exposed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "memory_field", CanonicalMemoryField(self.memory_field))
        ensure_bool(self.raw_memory_exposed, "MemoryRecallCandidate.raw_memory_exposed")
        if self.raw_memory_exposed:
            raise ValueError("memory recall candidate cannot expose raw memory")


@dataclass(frozen=True)
class MemoryPromotionProposal(MemoryPromotionReviewCandidate):
    output_ref: str = "projection:l6_phase4_memory_promotion_proposal"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.CANDIDATE
    target_memory_field: CanonicalMemoryField | str = CanonicalMemoryField.SEMANTIC_MEMORY
    evidence_index_ref: str = "evidence:l6_phase4_memory_promotion_index"
    writes_memory: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        object.__setattr__(self, "target_memory_field", CanonicalMemoryField(self.target_memory_field))
        ensure_ref_text(self.evidence_index_ref, "MemoryPromotionProposal.evidence_index_ref")
        ensure_bool(self.writes_memory, "MemoryPromotionProposal.writes_memory")
        if self.writes_memory:
            raise ValueError("memory promotion proposal cannot write memory")


@dataclass(frozen=True)
class MemoryEvidenceIndex(CognitiveOutputBase):
    output_ref: str = "evidence:l6_phase4_memory_evidence_index"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.REPORT
    plugin_ref: str = "l6_phase4:memory_candidate"
    source_evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase4_memory_source",))
    confidence_score_ref: str = "score:l6_phase4_memory_confidence"
    full_memory_content_included: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_items(self.source_evidence_refs, "MemoryEvidenceIndex.source_evidence_refs", required=True)
        ensure_ref_text(self.confidence_score_ref, "MemoryEvidenceIndex.confidence_score_ref")
        ensure_bool(self.full_memory_content_included, "MemoryEvidenceIndex.full_memory_content_included")
        if self.full_memory_content_included:
            raise ValueError("memory evidence index cannot include full memory content")


@dataclass(frozen=True)
class MemoryRetentionExceptionHint(CognitiveOutputBase):
    output_ref: str = "hint:l6_phase4_memory_retention_exception"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.HINT
    plugin_ref: str = "l6_phase4:forgetting_candidate"
    protected_rule_ref: str = "policy:l6_phase4_l5_system_rule_retention"
    protects_user_private_data: bool = False
    overrides_explicit_forget_request: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.protected_rule_ref, "MemoryRetentionExceptionHint.protected_rule_ref")
        ensure_bool(self.protects_user_private_data, "MemoryRetentionExceptionHint.protects_user_private_data")
        ensure_bool(self.overrides_explicit_forget_request, "MemoryRetentionExceptionHint.overrides_explicit_forget_request")
        if self.protects_user_private_data or self.overrides_explicit_forget_request:
            raise ValueError("retention exception cannot protect private/error/pollution memory or override explicit forget request")


@dataclass(frozen=True)
class ExplicitForgetRequestPriorityHint(CognitiveOutputBase):
    output_ref: str = "hint:l6_phase4_explicit_forget_priority"
    output_kind: CognitiveOutputKind | str = CognitiveOutputKind.HINT
    plugin_ref: str = "l6_phase4:forgetting_candidate"
    user_request_ref: str = "request:l6_phase4_explicit_forget"
    deletion_review_required: bool = True
    tombstone_review_required: bool = True
    active_recall_suppression_review_required: bool = True
    direct_delete_allowed: bool = False

    def __post_init__(self) -> None:
        super().__post_init__()
        ensure_ref_text(self.user_request_ref, "ExplicitForgetRequestPriorityHint.user_request_ref")
        for field_name in (
            "deletion_review_required",
            "tombstone_review_required",
            "active_recall_suppression_review_required",
            "direct_delete_allowed",
        ):
            ensure_bool(getattr(self, field_name), f"ExplicitForgetRequestPriorityHint.{field_name}")
        if not self.deletion_review_required or not self.tombstone_review_required or not self.active_recall_suppression_review_required or self.direct_delete_allowed:
            raise ValueError("explicit forget request must route through legal deletion review without direct delete")
