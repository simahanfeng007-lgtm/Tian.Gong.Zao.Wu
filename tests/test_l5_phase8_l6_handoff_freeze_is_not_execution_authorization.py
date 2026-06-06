import pytest

from tiangong_kernel.l5_plugin_host import L5L6HandoffFreeze, L5L6HandoffFreezeValidator


def test_l5_phase8_l6_handoff_freeze_is_not_execution_authorization():
    handoff = L5L6HandoffFreeze()
    assert handoff.no_execution_authorization_ref
    assert handoff.no_direct_tool_call_ref
    assert handoff.no_direct_l4_adapter_ref
    assert handoff.message_envelope_refs
    assert handoff.conversation_refs
    assert handoff.channel_refs
    assert handoff.protocol_refs
    assert handoff.result_return_refs
    assert L5L6HandoffFreezeValidator().check(handoff)


@pytest.mark.parametrize(
    "kwargs",
    (
        {"actor_ref": ""},
        {"scope_ref": ""},
        {"trace_ref": ""},
        {"policy_refs": ()},
        {"evidence_refs": ()},
        {"provenance_refs": ()},
        {"responsibility_chain_ref": ""},
        {"accountability_ref": ""},
        {"tamper_evidence_ref": ""},
        {"message_envelope_refs": ()},
        {"conversation_refs": ()},
        {"protocol_refs": ()},
        {"result_return_refs": ()},
    ),
)
def test_l5_phase8_l6_handoff_rejects_missing_accountability_and_message_refs(kwargs):
    with pytest.raises(ValueError):
        L5L6HandoffFreeze(**kwargs)


def test_l5_phase8_l6_handoff_requires_key_forbidden_misuse_refs():
    with pytest.raises(ValueError):
        L5L6HandoffFreeze(l6_forbidden_misuse_refs=("forbid:some_generic",))
