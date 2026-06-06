import pytest

from l4_phase5_builders import file_request, network_request, terminal_request
from tiangong_kernel.l4_action_grounding import FileActionRequest, NetworkActionRequest, TerminalActionRequest


def test_l4_phase5_requests_do_not_read_credentials_or_write_state():
    file_action = file_request()
    network_action = network_request()
    terminal_action = terminal_request()

    assert file_action.contains_plain_credential is False
    assert file_action.writes_l2_state is False
    assert file_action.writes_audit_store is False
    assert network_action.resolves_plain_credential is False
    assert network_action.writes_l2_state is False
    assert terminal_action.reads_real_environment is False
    assert terminal_action.writes_l2_state is False


def test_l4_phase5_rejects_plain_credentials_and_state_writes():
    file_base = file_request()
    with pytest.raises(ValueError):
        FileActionRequest(
            request_ref=file_base.request_ref,
            path_intent_ref=file_base.path_intent_ref,
            operation_ref=file_base.operation_ref,
            action_envelope=file_base.action_envelope,
            scope=file_base.scope,
            side_effect=file_base.side_effect,
            reversibility=file_base.reversibility,
            resource_usage=file_base.resource_usage,
            risk_surface=file_base.risk_surface,
            contains_plain_credential=True,
        )

    network_base = network_request()
    with pytest.raises(ValueError):
        NetworkActionRequest(
            request_ref=network_base.request_ref,
            url_ref=network_base.url_ref,
            method_ref=network_base.method_ref,
            payload_ref=network_base.payload_ref,
            headers_ref=network_base.headers_ref,
            action_envelope=network_base.action_envelope,
            scope=network_base.scope,
            side_effect=network_base.side_effect,
            reversibility=network_base.reversibility,
            resource_usage=network_base.resource_usage,
            risk_surface=network_base.risk_surface,
            resolves_plain_credential=True,
        )

    terminal_base = terminal_request()
    with pytest.raises(ValueError):
        TerminalActionRequest(
            request_ref=terminal_base.request_ref,
            command_ref=terminal_base.command_ref,
            args_ref=terminal_base.args_ref,
            working_dir_ref=terminal_base.working_dir_ref,
            env_ref=terminal_base.env_ref,
            action_envelope=terminal_base.action_envelope,
            scope=terminal_base.scope,
            side_effect=terminal_base.side_effect,
            reversibility=terminal_base.reversibility,
            resource_usage=terminal_base.resource_usage,
            risk_surface=terminal_base.risk_surface,
            reads_real_environment=True,
        )
