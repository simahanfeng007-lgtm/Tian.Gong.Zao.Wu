import pytest

from l4_phase5_builders import terminal_request
from tiangong_kernel.l4_action_grounding import TerminalActionEnvelope, TerminalActionRequest, action_grounding_stable_hash, action_grounding_to_primitive


def test_l4_phase5_terminal_action_request_is_structural_and_serializable():
    request = terminal_request()
    primitive = action_grounding_to_primitive(request)
    digest = action_grounding_stable_hash(request)

    assert isinstance(request, TerminalActionRequest)
    assert isinstance(request.action_envelope, TerminalActionEnvelope)
    assert primitive["request_only"] is True
    assert primitive["executes_real_command"] is False
    assert primitive["starts_process"] is False
    assert primitive["escalates_privilege"] is False
    assert digest


def test_l4_phase5_terminal_action_request_rejects_real_command_flags():
    base = terminal_request()
    with pytest.raises(ValueError):
        TerminalActionRequest(
            request_ref=base.request_ref,
            command_ref=base.command_ref,
            args_ref=base.args_ref,
            working_dir_ref=base.working_dir_ref,
            env_ref=base.env_ref,
            action_envelope=base.action_envelope,
            scope=base.scope,
            side_effect=base.side_effect,
            reversibility=base.reversibility,
            resource_usage=base.resource_usage,
            risk_surface=base.risk_surface,
            starts_process=True,
        )
