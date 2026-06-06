import tiangong_kernel.l5_plugin_host.phase5_boundary as phase5_boundary


def test_phase5_module_does_not_export_l6_business_plugins():
    forbidden = {"MemoryPlugin", "LearningPlugin", "EvolutionPlugin", "AffectivePlugin", "MathEnginePlugin"}
    assert not (set(dir(phase5_boundary)) & forbidden)
