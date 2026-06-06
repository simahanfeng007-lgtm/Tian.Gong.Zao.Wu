from dataclasses import FrozenInstanceError

import pytest

from tiangong_kernel.l5_plugin_host import PluginHandoffEvidenceIndex, PluginHandoffEvidenceRecord


def test_handoff_index_accepts_only_caller_supplied_metadata():
    record = PluginHandoffEvidenceRecord(
        ref="handoff_doc:l4_to_l5",
        title="L4 to L5 handoff",
        summary="调用方传入摘要。",
        digest="a" * 64,
        path_hint="docs/l4_to_l5_handoff_zh.txt",
        source_layer="L4",
    )
    index = PluginHandoffEvidenceIndex(
        index_ref="handoff_index:phase1",
        records=(record,),
        actor_ref="actor:engineer",
        scope_ref="scope:l5_phase1",
        trace_ref="trace:handoff",
        policy_ref="policy:phase1",
        evidence_refs=("evidence:handoff",),
        provenance_refs=("provenance:l4",),
        accountability_ref="accountability:owner",
        tamper_evidence_ref="tamper:handoff",
    )
    assert index.records[0].path_hint.endswith("handoff_zh.txt")
    assert index.handoff_index_digest
    with pytest.raises(FrozenInstanceError):
        index.records = ()


def test_handoff_index_rejects_large_summary_payloads():
    with pytest.raises(ValueError):
        PluginHandoffEvidenceRecord(
            ref="handoff_doc:large",
            summary="大" * 600,
        )
