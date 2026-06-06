from l4_phase5_builders import desktop_request, file_request, network_request, terminal_request
from tiangong_kernel.l4_action_grounding import NoOpDesktopAdapter, NoOpFileAdapter, NoOpNetworkAdapter, NoOpTerminalAdapter


def test_l4_phase5_no_op_external_adapters_do_nothing():
    assert NoOpFileAdapter().prepare_file_action(file_request()).no_op_result is True
    assert NoOpNetworkAdapter().prepare_network_action(network_request()).no_op_result is True
    assert NoOpTerminalAdapter().prepare_terminal_action(terminal_request()).no_op_result is True
    assert NoOpDesktopAdapter().prepare_desktop_action(desktop_request()).no_op_result is True
