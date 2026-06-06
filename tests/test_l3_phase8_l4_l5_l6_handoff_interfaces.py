from l3_phase8_builders import build_l3_phase8_objects


def test_l3_phase8_l4_handoff_is_request_and_ref_only():
    objects = build_l3_phase8_objects()
    envelope = objects["l4_envelope"]
    assert envelope.handoff_only is True
    assert envelope.request_bundle.bundle_only is True
    assert envelope.ref_bundle.ref_only is True
    assert envelope.readiness_summary.advisory_only is True
    assert envelope.non_execution_guarantee.guarantee_only is True
    assert "no_tool_call" in envelope.non_execution_guarantee.guarantee_items
    assert objects["l4_compat"].compatibility_score == 1.0


def test_l3_phase8_l5_handoff_is_non_decision():
    objects = build_l3_phase8_objects()
    envelope = objects["l5_envelope"]
    assert envelope.handoff_only is True
    assert envelope.request_bundle.bundle_only is True
    assert envelope.ref_bundle.ref_only is True
    assert envelope.readiness_summary.advisory_only is True
    assert envelope.non_decision_guarantee.guarantee_only is True
    assert objects["boundary_decision_ref"].ref_only is True
    assert objects["policy_decision_ref"].ref_only is True
    assert objects["denial_reason_ref"].ref_only is True
    assert objects["l5_compat"].compatibility_score == 1.0


def test_l3_phase8_l6_handoff_is_non_implementation():
    objects = build_l3_phase8_objects()
    envelope = objects["l6_envelope"]
    assert envelope.handoff_only is True
    assert envelope.request_bundle.bundle_only is True
    assert envelope.ref_bundle.ref_only is True
    assert envelope.readiness_summary.advisory_only is True
    assert envelope.non_implementation_guarantee.guarantee_only is True
    assert objects["observation_service"].request_only is True
    assert objects["validation_service"].request_only is True
    assert objects["evolution_service"].request_only is True
    assert objects["l6_compat"].compatibility_score == 1.0
