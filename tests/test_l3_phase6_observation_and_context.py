from l3_phase6_builders import build_l3_phase6_objects
from tiangong_kernel.l3_orchestration import (
    ObservationEnvelopeStatus,
    ObservationFeedbackKind,
)


def test_observation_feedback_objects_are_refs_and_advice_only():
    objects = build_l3_phase6_objects()
    observation_ref = objects["observation_ref"]
    envelope = objects["observation_envelope"]
    feedback = objects["feedback_advice"]
    routing = objects["routing_advice"]
    assert observation_ref.confidence == 0.82
    assert envelope.status is ObservationEnvelopeStatus.READY_FOR_ROUTING_ADVICE
    assert envelope.ref_only is True
    assert feedback.feedback_kind is ObservationFeedbackKind.ROUTE_TO_STEP
    assert feedback.advisory_only is True
    assert routing.top_target_ref == objects["step_ref"]
    assert not hasattr(observation_ref, "sample")
    assert not hasattr(feedback, "observer")


def test_context_carryover_objects_do_not_store_or_summarize_context():
    objects = build_l3_phase6_objects()
    carryover = objects["context_carryover"]
    window = objects["context_window"]
    compression = objects["compression_need"]
    retention = objects["retention"]
    drop = objects["drop"]
    priority = objects["priority"]
    assert carryover.advisory_only is True
    assert 0.0 <= carryover.value_hint <= 1.0
    assert window.advisory_only is True
    assert compression.advisory_only is True
    assert retention.advisory_only is True
    assert drop.advisory_only is True
    assert priority.top_context_ref == carryover.target_context_ref
    assert not hasattr(carryover, "context_store")
    assert not hasattr(compression, "model_summary")
