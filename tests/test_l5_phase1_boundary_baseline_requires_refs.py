import pytest

from tiangong_kernel.l5_plugin_host import PluginHostBoundaryBaseline


def test_boundary_baseline_requires_phase1_gate_refs():
    baseline = PluginHostBoundaryBaseline(
        baseline_ref="boundary:phase1",
        actor_ref="actor:engineer",
        scope_ref="scope:l5_phase1",
        trace_ref="trace:boundary",
        policy_ref="policy:phase1",
        permit_requirement_ref="permit:req_ref_only",
        lease_requirement_ref="lease:req_ref_only",
        audit_requirement_ref="audit:req_ref_only",
        resource_requirement_ref="resource:req_ref_only",
        credential_requirement_ref="credential:req_ref_only",
        evidence_refs=("evidence:boundary",),
        provenance_refs=("provenance:l4",),
        accountability_ref="accountability:owner",
        tamper_evidence_ref="tamper:boundary",
    )
    assert baseline.permit_requirement_ref == "permit:req_ref_only"


def test_boundary_baseline_rejects_missing_required_gate_ref():
    with pytest.raises(ValueError):
        PluginHostBoundaryBaseline(
            baseline_ref="boundary:phase1",
            actor_ref="actor:engineer",
            scope_ref="scope:l5_phase1",
            trace_ref="trace:boundary",
            policy_ref="policy:phase1",
            permit_requirement_ref="",
            lease_requirement_ref="lease:req_ref_only",
            audit_requirement_ref="audit:req_ref_only",
            resource_requirement_ref="resource:req_ref_only",
        )
