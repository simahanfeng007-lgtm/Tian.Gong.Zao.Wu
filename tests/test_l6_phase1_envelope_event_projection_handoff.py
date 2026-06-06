import pytest

from tiangong_kernel.l6_plugins.common import (
    L6PluginInvocationEnvelope,
    L6PluginOutputEnvelope,
    L6EventContract,
    L6StateProjectionContract,
    L6HandoffContract,
)


def test_invocation_envelope_is_read_only_and_contains_no_live_handles():
    envelope = L6PluginInvocationEnvelope()
    assert envelope.read_only is True
    assert envelope.contains_raw_credential is False
    assert envelope.contains_tool_handle is False
    assert envelope.contains_model_client is False
    assert envelope.contains_state_writer is False
    with pytest.raises(ValueError):
        L6PluginInvocationEnvelope(contains_model_client=True)
    with pytest.raises(ValueError):
        L6PluginInvocationEnvelope(read_only=False)


def test_output_envelope_is_refs_summaries_candidates_only():
    output = L6PluginOutputEnvelope(summary_items=("summary:l6_candidate_summary",))
    assert output.side_effect_free is True
    assert output.writes_state is False
    assert output.calls_model is False
    assert output.invokes_tool is False
    with pytest.raises(ValueError):
        L6PluginOutputEnvelope(writes_state=True)
    with pytest.raises(ValueError):
        L6PluginOutputEnvelope(calls_model=True)


def test_event_projection_and_handoff_do_not_connect_or_mutate_directly():
    event = L6EventContract()
    projection = L6StateProjectionContract()
    handoff = L6HandoffContract()
    assert event.no_direct_plugin_function_call is True
    assert event.no_direct_state_write is True
    assert projection.writes_l2_state_fact is False
    assert projection.treats_projection_as_fact is False
    assert handoff.ref_summary_digest_only is True
    assert handoff.transfers_authorization is False
    with pytest.raises(ValueError):
        L6EventContract(no_direct_plugin_function_call=False)
    with pytest.raises(ValueError):
        L6StateProjectionContract(writes_l2_state_fact=True)
    with pytest.raises(ValueError):
        L6HandoffContract(transfers_authorization=True)
