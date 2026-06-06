from tiangong_kernel.l2_state import ObservationSourceKind, ObservationSourceState, ObservationSourceStatus
from tests.test_l2_phase5_cross_phase_references import build_phase5_chain, identity, status, typed


def test_l2_phase5_observation_source_expresses_source_kinds_and_statuses():
    for source_kind in (
        ObservationSourceKind.MODEL_OUTPUT,
        ObservationSourceKind.TOOL_RESULT,
        ObservationSourceKind.BOUNDARY_EVENT,
        ObservationSourceKind.TEST_EVENT,
    ):
        state = ObservationSourceState(identity=identity(200), status=status(), source_kind=source_kind)
        assert state.source_kind is source_kind

    for source_status in (
        ObservationSourceStatus.AVAILABLE,
        ObservationSourceStatus.STALE,
        ObservationSourceStatus.REDACTED,
        ObservationSourceStatus.UNKNOWN,
    ):
        state = ObservationSourceState(identity=identity(201), status=status(), source_status=source_status)
        assert state.source_status is source_status


def test_l2_phase5_observation_source_links_boundary_security_environment_and_main_chain_refs():
    objects = build_phase5_chain()
    source = objects["source"]
    phase4 = objects["phase4"]
    phase3 = phase4["phase3"]

    assert source.boundary_state_refs == (phase4["boundary_check"].identity.state_ref,)
    assert source.security_state_refs == (phase4["security"].identity.state_ref,)
    assert source.environment_state_refs == (phase4["environment"].identity.state_ref,)
    assert source.related_run_ref == phase3["run"].identity.state_ref
    assert source.related_task_ref == phase3["task"].identity.state_ref
    assert source.related_skill_ref == phase3["skill_activation"].identity.state_ref
    assert source.related_tool_group_ref == phase3["tool_release"].identity.state_ref
    assert source.related_tool_intent_ref == phase3["tool_intent"].identity.state_ref
    assert source.related_action_ref == phase3["action_intent"].identity.state_ref
    assert source.related_effect_ref == phase3["effect_observation"].identity.state_ref
    assert source.created_at_ref == typed(12, "time")
