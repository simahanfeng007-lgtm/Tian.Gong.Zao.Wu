"""L6 phase8 audit evidence chain coverage contracts."""
from __future__ import annotations
from dataclasses import dataclass
from .common import FinalClosureArtifactBase

@dataclass(frozen=True)
class L6AuditEvidenceChainIndex(FinalClosureArtifactBase):
    object_ref: str = "audit:l6_phase8_evidence_chain_index"
    trace_coverage: bool = True
    responsibility_coverage: bool = True
    tamper_coverage: bool = True
    digest_coverage: bool = True
    def __post_init__(self) -> None:
        super().__post_init__()
        if not (self.trace_coverage and self.responsibility_coverage and self.tamper_coverage and self.digest_coverage):
            raise ValueError("Audit evidence chain coverage is incomplete")
@dataclass(frozen=True)
class L6TraceCoverageReport(L6AuditEvidenceChainIndex): object_ref: str = "report:l6_phase8_trace_coverage"
@dataclass(frozen=True)
class L6ResponsibilityChainCoverageReport(L6AuditEvidenceChainIndex): object_ref: str = "report:l6_phase8_responsibility_coverage"
@dataclass(frozen=True)
class L6TamperEvidenceCoverageReport(L6AuditEvidenceChainIndex): object_ref: str = "report:l6_phase8_tamper_coverage"
@dataclass(frozen=True)
class L6DigestCoverageReport(L6AuditEvidenceChainIndex): object_ref: str = "report:l6_phase8_digest_coverage"
@dataclass(frozen=True)
class L6EvidenceGapReport(L6AuditEvidenceChainIndex): object_ref: str = "report:l6_phase8_evidence_gap"
