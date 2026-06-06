from l4_phase5_builders import desktop_request, file_request, network_request, terminal_request
from tiangong_kernel.l4_action_grounding import FakeDesktopAdapter, FakeFileAdapter, FakeNetworkAdapter, FakeTerminalAdapter


def test_l4_phase5_fake_external_adapters_are_deterministic_and_test_only():
    file_result = FakeFileAdapter().prepare_file_action(file_request())
    network_result = FakeNetworkAdapter().prepare_network_action(network_request())
    terminal_result = FakeTerminalAdapter().prepare_terminal_action(terminal_request())
    desktop_result = FakeDesktopAdapter().prepare_desktop_action(desktop_request())

    assert file_result.fake_result is True
    assert file_result.real_file_mutation is False
    assert network_result.fake_result is True
    assert network_result.real_network_access is False
    assert terminal_result.fake_result is True
    assert terminal_result.process_started is False
    assert desktop_result.fake_result is True
    assert desktop_result.real_desktop_control is False

    assert FakeFileAdapter().describe().test_only is True
    assert FakeNetworkAdapter().describe().test_only is True
    assert FakeTerminalAdapter().describe().test_only is True
    assert FakeDesktopAdapter().describe().test_only is True
