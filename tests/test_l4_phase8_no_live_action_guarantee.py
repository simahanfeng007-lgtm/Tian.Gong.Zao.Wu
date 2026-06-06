import pytest

from l4_phase8_builders import no_live_action_guarantee, phase8_ref
from tiangong_kernel.l4_execution import L4NoLiveActionGuarantee


def test_l4_phase8_no_live_action_guarantee_covers_all_action_surfaces():
    guarantee = no_live_action_guarantee()

    for surface in ("model", "tool", "file", "network", "terminal", "desktop", "transaction", "replay", "audit", "recovery"):
        assert surface in guarantee.covered_surfaces
    assert guarantee.enables_live_action is False
    assert guarantee.calls_model is False
    assert guarantee.invokes_tool is False
    assert guarantee.writes_file is False
    assert guarantee.accesses_network is False
    assert guarantee.executes_shell is False
    assert guarantee.controls_desktop is False
    assert guarantee.commits_transaction is False
    assert guarantee.allocates_resource is False
    assert guarantee.schedules_concurrency is False
    assert guarantee.executes_replay is False


def test_l4_phase8_no_live_action_guarantee_rejects_live_flags():
    with pytest.raises(ValueError):
        L4NoLiveActionGuarantee(guarantee_ref=phase8_ref(140, "no_live_action"), executes_shell=True)
