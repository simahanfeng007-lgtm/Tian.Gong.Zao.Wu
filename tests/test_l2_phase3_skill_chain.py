from tests.test_l2_phase3_serialization import build_phase3_chain


def test_l2_phase3_skill_chain_links_visibility_selection_activation_failure():
    chain = build_phase3_chain()
    visibility = chain["skill_visibility"]
    selection = chain["skill_selection"]
    activation = chain["skill_activation"]
    failure = chain["skill_failure"]

    assert visibility.skill_ref == selection.skill_ref == activation.skill_ref == failure.skill_ref
    assert visibility.run_ref == selection.run_ref == activation.run_ref == failure.run_ref
    assert visibility.task_ref == selection.task_ref == activation.task_ref == failure.task_ref
    assert activation.selection_state_ref == selection.identity.state_ref
    assert failure.activation_state_ref == activation.identity.state_ref
    assert activation.tool_group_state_refs
    assert failure.evidence_refs
