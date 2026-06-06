from tiangong_kernel.l6_plugins.final_closure import L6LongChainCapabilitySummary

def test_long_chain_capability_summary_exists():
    assert L6LongChainCapabilitySummary().object_ref == 'summary:l6_phase8_long_chain_capability'
