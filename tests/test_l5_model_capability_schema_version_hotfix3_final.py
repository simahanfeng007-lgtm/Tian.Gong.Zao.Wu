from tiangong_kernel.l5_plugin_host.model_capability_invariants import L5_MODEL_CAPABILITY_SCHEMA_VERSION


def test_l5_model_capability_schema_version_is_finalized_for_hotfix3_p2p3():
    assert L5_MODEL_CAPABILITY_SCHEMA_VERSION == "0.1.hotfix3-p2p3-final-five-model"
