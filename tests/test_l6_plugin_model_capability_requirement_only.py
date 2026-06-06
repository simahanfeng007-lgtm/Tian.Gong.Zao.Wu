from tiangong_kernel.l5_plugin_host.model_capability_invariants import build_plugin_model_access_invariants


def test_l6_good_plugin_declaration_passes_scan():
    source = "MODEL_REQUIREMENT_REF='req-ref:demo'\n"
    cap, sdk, http = build_plugin_model_access_invariants("plugin-ref:good", source, ("req-ref:demo",))
    assert cap.no_model_client is True
    assert sdk.passed is True
    assert http.passed is True
