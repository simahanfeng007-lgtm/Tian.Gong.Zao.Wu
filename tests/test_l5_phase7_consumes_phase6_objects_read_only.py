from dataclasses import replace
from tiangong_kernel.l5_plugin_host import PluginHealthSignalDeclaration, PluginHostBoundaryGateValidator


def test_phase7_consumes_phase6_objects_read_only():
    signal = PluginHealthSignalDeclaration()
    before = signal
    report = PluginHostBoundaryGateValidator().check(signal)
    assert signal == before
    assert report.p0_count == 0
