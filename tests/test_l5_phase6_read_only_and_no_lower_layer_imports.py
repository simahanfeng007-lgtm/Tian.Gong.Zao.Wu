from dataclasses import replace
from tiangong_kernel.l5_plugin_host import PluginPhase5QualityGateDecision, PluginPhase6QualityGateDecision, to_l5_digest
from l5_phase6_factories import quality_gate


def test_consumes_phase5_objects_read_only():
    phase6 = quality_gate()
    before = to_l5_digest(phase6)
    after_obj = replace(phase6, p2_count=1)
    assert to_l5_digest(phase6) == before
    assert to_l5_digest(after_obj) != before
    assert PluginPhase6QualityGateDecision.__name__ != PluginPhase5QualityGateDecision.__name__


def test_no_l4_adapter_imports_and_no_l6_plugin_implementation():
    import types
    from tiangong_kernel.l5_plugin_host import phase6_health

    module_values = [value for value in phase6_health.__dict__.values() if isinstance(value, types.ModuleType)]
    module_names = {value.__name__ for value in module_values}
    assert not any(name.startswith("tiangong_kernel.l4_action_grounding") for name in module_names)
    assert not any(name.startswith("tiangong_kernel.l4_execution") for name in module_names)
    assert not any(name.endswith("MemoryPlugin") or name.endswith("LearningPlugin") for name in phase6_health.__dict__)
