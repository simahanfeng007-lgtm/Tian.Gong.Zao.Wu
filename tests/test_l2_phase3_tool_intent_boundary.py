from tiangong_kernel.l2_state import ToolIntentBoundaryStatus, ToolIntentSource, ToolIntentStatus
from tests.test_l2_phase3_serialization import build_phase3_chain


def test_l2_phase3_tool_intent_and_boundary_are_status_only():
    chain = build_phase3_chain()
    intent = chain["tool_intent"]
    boundary = chain["tool_boundary"]
    response = chain["model_response"]
    release = chain["tool_release"]

    assert intent.intent_source == ToolIntentSource.MODEL
    assert intent.intent_status == ToolIntentStatus.PARSED
    assert intent.model_response_ref == response.identity.state_ref
    assert intent.tool_group_release_ref == release.identity.state_ref
    assert intent.argument_digest == "sha256:phase3"
    assert boundary.boundary_status == ToolIntentBoundaryStatus.WAITING_CHECK
    assert boundary.tool_intent_ref == intent.identity.state_ref
    assert boundary.decision_refs == ()
