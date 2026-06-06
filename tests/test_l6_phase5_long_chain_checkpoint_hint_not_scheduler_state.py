import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_long_chain_checkpoint_hint_not_scheduler_state():
    checkpoint = LongChainCheckpointHint()
    assert checkpoint.stored_as_file is False
    assert checkpoint.scheduler_state is False
    assert checkpoint.direct_resume_action is False
    with pytest.raises(ValueError):
        LongChainCheckpointHint(scheduler_state=True)
