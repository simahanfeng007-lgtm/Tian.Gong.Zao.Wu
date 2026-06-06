from tiangong_kernel.l6_plugins.product_delivery import *

def test_product_long_chain_checkpoint_hint_required():
    checkpoint = ProductCheckpointHint()
    state = ProductionLongChainState()
    assert checkpoint.scheduler_state is False
    assert state.real_scheduler_state is False
    assert state.checkpoint_refs
