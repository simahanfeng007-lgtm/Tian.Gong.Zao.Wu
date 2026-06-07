"""L5 phase 3 registry quality gate data shells.

The gate records and evaluates declaration reports only. It does not execute
tests, scan files, write registries, mutate snapshots, issue permits, or trigger
plugin lifecycle actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ._common import L5_PLUGIN_HOST_SCHEMA_VERSION, ensure_bool, ensure_ref_items, ensure_ref_text, ensure_schema_version, ensure_short_text
from .registry_conflict import PluginRegistryConflictReport
from .registry_delta import PluginRegistryDelta
from .registry_snapshot import PluginRegistrySnapshot


@dataclass(frozen=True, slots=True)
class PluginRegistryQualityGateResult:
    result_ref: str
    snapshot_ref: str
    conflict_report_ref: str
    passed: bool
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    missing_required_refs: tuple[str, ...] = field(default_factory=tuple)
    actor_ref: str = ""
    scope_ref: str = ""
    trace_ref: str = ""
    policy_ref: str = ""
    approval_ref: str = ""
    responsibility_chain_ref: str = ""
    accountability_ref: str = ""
    provenance_refs: tuple[str, ...] = field(default_factory=tuple)
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    tamper_evidence_ref: str = ""
    summary: str = ""
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.result_ref, "PluginRegistryQualityGateResult.result_ref")
        ensure_ref_text(self.snapshot_ref, "PluginRegistryQualityGateResult.snapshot_ref")
        ensure_ref_text(self.conflict_report_ref, "PluginRegistryQualityGateResult.conflict_report_ref")
        ensure_bool(self.passed, "PluginRegistryQualityGateResult.passed")
        for field_name in self.missing_required_refs:
            ensure_ref_text(field_name, "PluginRegistryQualityGateResult.missing_required_refs")
        for name in ("actor_ref", "scope_ref", "trace_ref", "policy_ref", "approval_ref", "responsibility_chain_ref", "accountability_ref", "tamper_evidence_ref"):
            ensure_ref_text(getattr(self, name), f"PluginRegistryQualityGateResult.{name}", required=False)
        ensure_ref_items(self.provenance_refs, "PluginRegistryQualityGateResult.provenance_refs")
        ensure_ref_items(self.evidence_refs, "PluginRegistryQualityGateResult.evidence_refs")
        ensure_short_text(self.summary, "PluginRegistryQualityGateResult.summary")
        ensure_schema_version(self.schema_version, "PluginRegistryQualityGateResult.schema_version")


@dataclass(frozen=True, slots=True)
class PluginRegistryQualityGate:
    gate_ref: str
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.gate_ref, "PluginRegistryQualityGate.gate_ref")
        ensure_schema_version(self.schema_version, "PluginRegistryQualityGate.schema_version")

    def evaluate(self, snapshot: PluginRegistrySnapshot, conflict_report: PluginRegistryConflictReport) -> PluginRegistryQualityGateResult:
        missing: list[str] = []
        for attr in ("revision_ref", "snapshot_digest", "evidence_refs", "tamper_evidence_ref"):
            value = getattr(snapshot, attr)
            if value == "" or value == tuple():
                missing.append(f"snapshot.{attr}")
        for attr in ("rule_source_ref", "detected_by_ref", "trace_ref", "evidence_refs", "responsibility_chain_ref"):
            value = getattr(conflict_report, attr)
            if value == "" or value == tuple():
                missing.append(f"conflict_report.{attr}")
        passed = not missing and conflict_report.p0_count == 0 and conflict_report.p1_count == 0
        return PluginRegistryQualityGateResult(
            result_ref=f"registry_quality_gate:{snapshot.snapshot_ref}",
            snapshot_ref=snapshot.snapshot_ref,
            conflict_report_ref=conflict_report.report_ref,
            passed=passed,
            p0_count=conflict_report.p0_count,
            p1_count=conflict_report.p1_count,
            p2_count=conflict_report.p2_count,
            p3_count=conflict_report.p3_count,
            missing_required_refs=tuple(missing),
            actor_ref=snapshot.actor_ref,
            scope_ref=snapshot.scope_ref,
            trace_ref=snapshot.trace_ref,
            policy_ref=snapshot.policy_ref,
            approval_ref=snapshot.approval_ref,
            responsibility_chain_ref=snapshot.responsibility_chain_ref,
            accountability_ref=snapshot.accountability_ref,
            provenance_refs=snapshot.provenance_refs,
            evidence_refs=snapshot.evidence_refs,
            tamper_evidence_ref=snapshot.tamper_evidence_ref,
            summary="passed" if passed else "blocked",
        )


@dataclass(frozen=True, slots=True)
class L5Phase3QualityGateDecision:
    phase: str = "L5_PHASE3"
    p0_count: int = 0
    p1_count: int = 0
    p2_count: int = 0
    p3_count: int = 0
    compileall_passed: bool = False
    collect_only_passed: bool = False
    targeted_pytest_passed: bool = False
    plugin_host_subset_passed: bool = False
    full_pytest_passed: bool = False
    forbidden_scan_passed: bool = False
    l0_l4_hash_clean: bool = False
    l5_phase1_phase2_hash_clean: bool = False
    zip_integrity_passed: bool = False
    registry_quality_gate_passed: bool = False
    snapshot_delta_determinism_passed: bool = False
    public_projection_safety_passed: bool = False
    allow_enter_l5_phase4: bool = False
    blocking_reasons: tuple[str, ...] = field(default_factory=tuple)
    evidence_index_refs: tuple[str, ...] = field(default_factory=tuple)
    regression_index_refs: tuple[str, ...] = field(default_factory=tuple)
    schema_version: str = L5_PLUGIN_HOST_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.phase != "L5_PHASE3":
            raise ValueError("L5Phase3QualityGateDecision.phase must be L5_PHASE3")
        bool_fields = (
            "compileall_passed", "collect_only_passed", "targeted_pytest_passed", "plugin_host_subset_passed",
            "full_pytest_passed", "forbidden_scan_passed", "l0_l4_hash_clean", "l5_phase1_phase2_hash_clean",
            "zip_integrity_passed", "registry_quality_gate_passed", "snapshot_delta_determinism_passed",
            "public_projection_safety_passed", "allow_enter_l5_phase4",
        )
        for name in bool_fields:
            ensure_bool(getattr(self, name), f"L5Phase3QualityGateDecision.{name}")
        for reason in self.blocking_reasons:
            ensure_short_text(reason, "L5Phase3QualityGateDecision.blocking_reasons")
        ensure_ref_items(self.evidence_index_refs, "L5Phase3QualityGateDecision.evidence_index_refs")
        ensure_ref_items(self.regression_index_refs, "L5Phase3QualityGateDecision.regression_index_refs")
        ensure_schema_version(self.schema_version, "L5Phase3QualityGateDecision.schema_version")
        if self.allow_enter_l5_phase4:
            blockers = (
                self.p0_count > 0,
                self.p1_count > 0,
                not self.full_pytest_passed,
                not self.forbidden_scan_passed,
                not self.l0_l4_hash_clean,
                not self.l5_phase1_phase2_hash_clean,
            )
            if any(blockers):
                raise ValueError("L5Phase3QualityGateDecision cannot allow phase 4 when blocking conditions exist")
