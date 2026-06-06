import pytest

from l4_phase8_builders import (
    l6_adapter_requirement,
    l6_execution_service_need,
    l6_observation_requirement,
    l6_recovery_requirement,
    l6_replay_requirement,
    phase8_ref,
)
from tiangong_kernel.l4_execution import (
    L4ToL6AdapterRequirement,
    L4ToL6ExecutionServiceNeed,
    L4ToL6ObservationRequirement,
    L4ToL6RecoveryRequirement,
    L4ToL6ReplayRequirement,
)


def test_l4_phase8_l4_to_l6_handoff_is_requirements_only():
    adapter = l6_adapter_requirement()
    observation = l6_observation_requirement()
    recovery = l6_recovery_requirement()
    replay = l6_replay_requirement()
    service_need = l6_execution_service_need()

    assert adapter.requirement_only is True
    assert adapter.implements_adapter is False
    assert adapter.calls_model is False
    assert adapter.invokes_tool is False
    assert observation.samples_real_observation is False
    assert observation.reads_screen is False
    assert observation.stores_evidence is False
    assert recovery.executes_recovery is False
    assert recovery.executes_rollback is False
    assert replay.executes_replay is False
    assert replay.creates_snapshot is False
    assert replay.stores_sensitive_plaintext is False
    assert service_need.need_only is True
    assert service_need.implements_service is False
    assert service_need.executes_external_action is False
    assert service_need.hosts_plugin_or_connector is False


def test_l4_phase8_l4_to_l6_handoff_rejects_l6_implementation_flags():
    with pytest.raises(ValueError):
        L4ToL6AdapterRequirement(adapter_requirement_ref=phase8_ref(190, "adapter_requirement"), implements_adapter=True)
    with pytest.raises(ValueError):
        L4ToL6ObservationRequirement(observation_requirement_ref=phase8_ref(191, "observation_requirement"), samples_real_observation=True)
    with pytest.raises(ValueError):
        L4ToL6RecoveryRequirement(recovery_requirement_ref=phase8_ref(192, "recovery_requirement"), executes_recovery=True)
    with pytest.raises(ValueError):
        L4ToL6ReplayRequirement(replay_requirement_ref=phase8_ref(193, "replay_requirement"), executes_replay=True)
    with pytest.raises(ValueError):
        L4ToL6ExecutionServiceNeed(execution_service_need_ref=phase8_ref(194, "service_need"), implements_service=True)
