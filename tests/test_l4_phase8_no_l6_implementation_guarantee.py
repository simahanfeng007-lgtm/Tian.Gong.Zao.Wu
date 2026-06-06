import pytest

from l4_phase8_builders import no_l6_implementation_guarantee, phase8_ref
from tiangong_kernel.l4_execution import L4NoL6ImplementationGuarantee


def test_l4_phase8_no_l6_implementation_guarantee_covers_l6_surfaces():
    guarantee = no_l6_implementation_guarantee()

    for surface in ("model_adapter", "tool_adapter", "file_adapter", "network_adapter", "observation_adapter", "recovery_adapter", "replay_adapter", "plugin_host", "connector_platform"):
        assert surface in guarantee.covered_l6_surfaces
    assert guarantee.implements_l6_service is False
    assert guarantee.implements_adapter is False
    assert guarantee.implements_observation_system is False
    assert guarantee.implements_recovery_system is False
    assert guarantee.implements_replay_system is False
    assert guarantee.hosts_plugins is False
    assert guarantee.hosts_connectors is False


def test_l4_phase8_no_l6_implementation_guarantee_rejects_l6_flags():
    with pytest.raises(ValueError):
        L4NoL6ImplementationGuarantee(guarantee_ref=phase8_ref(160, "no_l6"), implements_l6_service=True)
