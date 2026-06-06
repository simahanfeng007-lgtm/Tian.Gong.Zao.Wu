import pytest

from tiangong_kernel.l5_plugin_host import (
    PluginHostAccountabilityRef,
    PluginHostAuditAnchor,
    PluginHostEvidenceRef,
    PluginHostProvenanceRef,
    PluginHostTamperEvidenceRef,
)


def test_audit_anchor_and_refs_store_compact_reference_metadata_only():
    evidence = PluginHostEvidenceRef(
        ref="evidence:manifest",
        summary="短摘要",
        digest="b" * 64,
        source_layer="L5.phase1",
        created_by_ref="actor:engineer",
        trace_ref="trace:audit",
        scope_ref="scope:l5_phase1",
    )
    provenance = PluginHostProvenanceRef(ref="provenance:l4", summary="handoff ref")
    accountability = PluginHostAccountabilityRef(ref="accountability:owner", summary="owner ref")
    tamper = PluginHostTamperEvidenceRef(ref="tamper:manifest", summary="digest ref")
    anchor = PluginHostAuditAnchor(
        anchor_ref="audit_anchor:phase1",
        evidence_ref=evidence.ref,
        provenance_ref=provenance.ref,
        accountability_ref=accountability.ref,
        tamper_evidence_ref=tamper.ref,
    )
    assert anchor.evidence_ref == "evidence:manifest"
    assert evidence.digest == "b" * 64


def test_audit_refs_reject_large_inline_content():
    with pytest.raises(ValueError):
        PluginHostEvidenceRef(ref="evidence:large", summary="长" * 600)
