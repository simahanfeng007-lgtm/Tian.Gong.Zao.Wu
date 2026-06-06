from l4_phase5_builders import desktop_request, file_request, network_request, terminal_request
from tiangong_kernel.l4_action_grounding import (
    DesktopActionFailureKind,
    DisabledRealDesktopAdapterStub,
    DisabledRealFileAdapterStub,
    DisabledRealNetworkAdapterStub,
    DisabledRealTerminalAdapterStub,
    FileActionFailureKind,
    NetworkActionFailureKind,
    TerminalActionFailureKind,
)


def test_l4_phase5_disabled_real_external_stubs_default_reject():
    file_failure = DisabledRealFileAdapterStub().disabled_file_action(file_request())
    network_failure = DisabledRealNetworkAdapterStub().disabled_network_action(network_request())
    terminal_failure = DisabledRealTerminalAdapterStub().disabled_terminal_action(terminal_request())
    desktop_failure = DisabledRealDesktopAdapterStub().disabled_desktop_action(desktop_request())

    assert file_failure.failure_kind is FileActionFailureKind.DISABLED_BY_DEFAULT
    assert file_failure.real_file_mutation is False
    assert network_failure.failure_kind is NetworkActionFailureKind.DISABLED_BY_DEFAULT
    assert network_failure.real_network_access is False
    assert terminal_failure.failure_kind is TerminalActionFailureKind.DISABLED_BY_DEFAULT
    assert terminal_failure.process_started is False
    assert desktop_failure.failure_kind is DesktopActionFailureKind.DISABLED_BY_DEFAULT
    assert desktop_failure.real_desktop_control is False


def test_l4_phase5_disabled_real_external_descriptors_are_not_enabled():
    adapters = (
        DisabledRealFileAdapterStub(),
        DisabledRealNetworkAdapterStub(),
        DisabledRealTerminalAdapterStub(),
        DisabledRealDesktopAdapterStub(),
    )
    for adapter in adapters:
        descriptor = adapter.describe()
        assert descriptor.requires_l5_permit is True
        assert descriptor.enabled_by_default is False
        assert descriptor.production_enabled is False
