from dataclasses import FrozenInstanceError

import pytest

from tiangong_kernel.l5_plugin_host import PluginHostContext, PluginHostIdentity, to_l5_primitive


def test_l5_phase1_identity_is_frozen_and_data_only():
    identity = PluginHostIdentity(host_ref="host:l5_phase1")
    assert identity.phase == "L5.phase1"
    assert "plugin_manifest_view" in identity.supported_surfaces
    with pytest.raises(FrozenInstanceError):
        identity.host_name = "changed"


def test_l5_phase1_context_requires_core_responsibility_refs():
    context = PluginHostContext(
        context_ref="context:phase1",
        host_ref="host:l5_phase1",
        actor_ref="actor:engineer",
        scope_ref="scope:l5_phase1",
        trace_ref="trace:phase1",
        policy_ref="policy:no_live_action",
        evidence_refs=("evidence:precheck",),
        provenance_refs=("provenance:l4_handoff",),
        accountability_ref="accountability:owner",
        tamper_evidence_ref="tamper:manifest",
        summary="上下文只保存引用。",
    )
    primitive = to_l5_primitive(context)
    assert primitive["actor_ref"] == "actor:engineer"
    assert primitive["evidence_refs"] == ["evidence:precheck"]


def test_l5_phase1_context_rejects_missing_required_ref():
    with pytest.raises(ValueError):
        PluginHostContext(
            context_ref="context:phase1",
            host_ref="host:l5_phase1",
            actor_ref="",
            scope_ref="scope:l5_phase1",
            trace_ref="trace:phase1",
            policy_ref="policy:no_live_action",
        )
