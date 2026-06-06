from l4_phase5_builders import terminal_request
from tiangong_kernel.l4_action_grounding import DisabledRealTerminalAdapterStub, NoRealShellExecutionInvariant


def test_l4_phase5_no_shell_without_l5_permit():
    request = terminal_request()
    failure = DisabledRealTerminalAdapterStub().prepare_terminal_action(request)
    invariant = NoRealShellExecutionInvariant(invariant_ref=request.request_ref)

    assert request.permit_ref is None
    assert failure.real_command_executed is False
    assert failure.process_started is False
    assert invariant.live_action_allowed is False
