from tiangong_kernel.l2_state import (
    ToolGroupDeclarationStatus,
    ToolGroupLeaseStatus,
    ToolGroupReleaseStatus,
    ToolGroupVisibilityStatus,
)
from tests.test_l2_phase3_serialization import build_phase3_chain


def test_l2_phase3_tool_group_chain_links_declaration_visibility_release_lease():
    chain = build_phase3_chain()
    declaration = chain["tool_declaration"]
    visibility = chain["tool_visibility"]
    release = chain["tool_release"]
    lease = chain["tool_lease"]

    assert declaration.declaration_status == ToolGroupDeclarationStatus.DECLARED
    assert visibility.visibility_status == ToolGroupVisibilityStatus.VISIBLE
    assert release.release_status == ToolGroupReleaseStatus.RELEASED
    assert lease.lease_status == ToolGroupLeaseStatus.LEASED
    assert visibility.declaration_state_ref == declaration.identity.state_ref
    assert release.visibility_state_ref == visibility.identity.state_ref
    assert lease.release_state_ref == release.identity.state_ref
    assert release.released_tool_refs == declaration.required_tool_refs
