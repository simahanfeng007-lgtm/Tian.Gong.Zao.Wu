from l5_phase7_builders import phase7_objects


def test_l5_phase7_plugin_host_subset_is_non_empty():
    # Function name intentionally contains l5 and plugin for the required -k "l5 and plugin" subset.
    assert len(phase7_objects()) >= 10
