from l3_phase1_builders import typed
from l4_phase2_builders import audit_requirement, broader_scope, credential, full_permit, resource_limit
from tiangong_kernel.l4_action_grounding import (
    ActionPermitRef,
    AuditRequirementRef,
    CredentialHandleRef,
    PermitExpiry,
    PermitScope,
    ResourceLimitRef,
    action_grounding_stable_hash,
    action_grounding_to_primitive,
)


def test_l4_phase2_permit_ref_objects_create_and_serialize():
    permit = full_permit(audit=audit_requirement(), credential=credential(), resource=resource_limit())
    primitive = action_grounding_to_primitive(permit)
    assert isinstance(permit, ActionPermitRef)
    assert permit.is_structurally_complete is True
    assert primitive["ref_only"] is True
    assert primitive["l4_issued"] is False
    assert len(action_grounding_stable_hash(permit)) == 64


def test_l4_phase2_permit_scope_structural_matching():
    permitted = broader_scope()
    requested = PermitScope(action_scope=("tool_call",), resource_scope=("workspace_ref",), environment_scope=("local_test_env",))
    not_requested = PermitScope(action_scope=("network_call",), resource_scope=("workspace_ref",), environment_scope=("local_test_env",))
    assert permitted.structurally_covers(requested) is True
    assert permitted.structurally_covers(not_requested) is False


def test_l4_phase2_permit_expiry_is_explicit_only():
    active = PermitExpiry("2099-01-01T00:00:00Z")
    expired = PermitExpiry("2000-01-01T00:00:00Z", explicit_expired=True)
    assert active.is_expired is False
    assert expired.is_expired is True


def test_l4_phase2_refs_do_not_hold_plain_credentials_or_real_resources():
    cred = CredentialHandleRef(handle_ref=typed(5200, "credential_handle"))
    audit = AuditRequirementRef(requirement_ref=typed(5201, "audit_requirement"))
    resource = ResourceLimitRef(limit_ref=typed(5202, "resource_limit"))
    assert cred.contains_plain_secret is False
    assert cred.l4_resolved_credential is False
    assert audit.l4_audit_written is False
    assert resource.l4_budget_created is False
    assert resource.l4_resource_consumed is False
