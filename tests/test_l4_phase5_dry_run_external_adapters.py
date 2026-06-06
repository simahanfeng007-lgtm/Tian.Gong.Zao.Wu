from l4_phase5_builders import desktop_request, file_request, network_request, terminal_request
from tiangong_kernel.l4_action_grounding import DryRunDesktopAdapter, DryRunFileAdapter, DryRunNetworkAdapter, DryRunTerminalAdapter


def test_l4_phase5_dry_run_external_adapters_return_preview_only():
    file_result = DryRunFileAdapter().prepare_file_action(file_request())
    network_result = DryRunNetworkAdapter().prepare_network_action(network_request())
    terminal_result = DryRunTerminalAdapter().prepare_terminal_action(terminal_request())
    desktop_result = DryRunDesktopAdapter().prepare_desktop_action(desktop_request())

    assert file_result.dry_run_only is True
    assert file_result.real_file_read is False
    assert file_result.real_file_mutation is False
    assert network_result.dry_run_only is True
    assert network_result.real_network_access is False
    assert terminal_result.dry_run_only is True
    assert terminal_result.process_started is False
    assert desktop_result.dry_run_only is True
    assert desktop_result.real_input_sent is False
