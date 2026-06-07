"""L5 phase 1 quality gate decision shells.

These objects record externally observed validation results. They do not run
commands, scan files, load plugins, issue permits, or change registries.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_PHASE, L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text, ensure_text_items

_ALLOW_NEXT = "allow_next_phase"
_BLOCK_NEXT = "block_next_phase"


@dataclass(frozen=True, slots=True)
class L5Phase1BlockingFinding:
    finding_ref: str
    reason: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.finding_ref, "L5Phase1BlockingFinding.finding_ref")
        ensure_short_text(self.reason, "L5Phase1BlockingFinding.reason")
        ensure_ref_items(self.evidence_refs, "L5Phase1BlockingFinding.evidence_refs")
        ensure_schema_version(self.schema_version, "L5Phase1BlockingFinding.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1NonBlockingFinding:
    finding_ref: str
    reason: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.finding_ref, "L5Phase1NonBlockingFinding.finding_ref")
        ensure_short_text(self.reason, "L5Phase1NonBlockingFinding.reason")
        ensure_ref_items(self.evidence_refs, "L5Phase1NonBlockingFinding.evidence_refs")
        ensure_schema_version(self.schema_version, "L5Phase1NonBlockingFinding.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1QualityGateSummary:
    gate_id: str
    phase: str = L5_PLUGIN_HOST_PHASE
    baseline_refs: tuple[str, ...] = field(default_factory=tuple)
    required_checks: tuple[str, ...] = field(default_factory=tuple)
    observed_results: tuple[str, ...] = field(default_factory=tuple)
    blocking_findings: tuple[L5Phase1BlockingFinding, ...] = field(default_factory=tuple)
    non_blocking_findings: tuple[L5Phase1NonBlockingFinding, ...] = field(default_factory=tuple)
    decision: str = _BLOCK_NEXT
    reason: str = ""
    recorded_at: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.gate_id, "L5Phase1QualityGateSummary.gate_id")
        ensure_short_text(self.phase, "L5Phase1QualityGateSummary.phase", 64)
        ensure_ref_items(self.baseline_refs, "L5Phase1QualityGateSummary.baseline_refs")
        ensure_text_items(self.required_checks, "L5Phase1QualityGateSummary.required_checks", limit=128)
        ensure_text_items(self.observed_results, "L5Phase1QualityGateSummary.observed_results", limit=256)
        for item in self.blocking_findings:
            if not isinstance(item, L5Phase1BlockingFinding):
                raise ValueError("blocking_findings must contain L5Phase1BlockingFinding")
        for item in self.non_blocking_findings:
            if not isinstance(item, L5Phase1NonBlockingFinding):
                raise ValueError("non_blocking_findings must contain L5Phase1NonBlockingFinding")
        if self.decision not in (_ALLOW_NEXT, _BLOCK_NEXT):
            raise ValueError("L5Phase1QualityGateSummary.decision has unsupported value")
        if self.blocking_findings and self.decision != _BLOCK_NEXT:
            raise ValueError("blocking findings require block_next_phase")
        ensure_short_text(self.reason, "L5Phase1QualityGateSummary.reason")
        ensure_short_text(self.recorded_at, "L5Phase1QualityGateSummary.recorded_at", 64)
        ensure_schema_version(self.schema_version, "L5Phase1QualityGateSummary.schema_version")


@dataclass(frozen=True, slots=True)
class L5Phase1QualityGateDecision:
    gate_id: str
    phase: str = L5_PLUGIN_HOST_PHASE
    baseline_refs: tuple[str, ...] = field(default_factory=tuple)
    required_checks: tuple[str, ...] = field(default_factory=tuple)
    observed_results: tuple[str, ...] = field(default_factory=tuple)
    blocking_findings: tuple[L5Phase1BlockingFinding, ...] = field(default_factory=tuple)
    non_blocking_findings: tuple[L5Phase1NonBlockingFinding, ...] = field(default_factory=tuple)
    decision: str = _BLOCK_NEXT
    reason: str = ""
    recorded_at: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        summary = L5Phase1QualityGateSummary(
            gate_id=self.gate_id,
            phase=self.phase,
            baseline_refs=self.baseline_refs,
            required_checks=self.required_checks,
            observed_results=self.observed_results,
            blocking_findings=self.blocking_findings,
            non_blocking_findings=self.non_blocking_findings,
            decision=self.decision,
            reason=self.reason,
            recorded_at=self.recorded_at,
            schema_version=self.schema_version,
        )
        if summary.gate_id != self.gate_id:
            raise ValueError("quality gate decision summary mismatch")
