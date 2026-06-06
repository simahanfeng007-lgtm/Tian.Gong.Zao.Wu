import pytest

from tiangong_kernel.l6_plugins.common import (
    L6PermissionRequirement,
    L6BudgetRequirement,
    L6AuditRequirement,
    L6CredentialRequirement,
    L6ContextRequirement,
)


def test_governance_requirements_are_not_permits_allocations_records_or_access():
    assert L6PermissionRequirement().grants_permission is False
    assert L6BudgetRequirement().allocates_budget is False
    assert L6BudgetRequirement().decrements_budget is False
    assert L6AuditRequirement().writes_audit_record is False
    assert L6CredentialRequirement().reads_credential is False
    assert L6ContextRequirement().reads_full_context is False


def test_governance_requirements_reject_execution_meaning():
    with pytest.raises(ValueError):
        L6PermissionRequirement(grants_permission=True)
    with pytest.raises(ValueError):
        L6BudgetRequirement(decrements_budget=True)
    with pytest.raises(ValueError):
        L6AuditRequirement(writes_audit_record=True)
    with pytest.raises(ValueError):
        L6CredentialRequirement(reads_credential=True)
    with pytest.raises(ValueError):
        L6ContextRequirement(reads_full_context=True)
