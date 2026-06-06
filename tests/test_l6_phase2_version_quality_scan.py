import pytest

from tiangong_kernel.l6_plugins.common import (
    L6BreakingChangeAssessment,
    L6CompatibilityMatrix,
    L6ContractChangeKind,
    L6ContractPatchPublicProjection,
    L6ContractPatchQualityGateDecision,
    L6HotSwitchReadinessDeclaration,
    L6MigrationPlanDeclaration,
    L6Phase2QualityGateDecision,
    L6Phase2RegressionMatrix,
    L6Phase2TestEvidenceIndex,
    L6ReplayCompatibilityDeclaration,
    L6RollbackRouteDeclaration,
    default_l6_forbidden_scan_rules,
    default_l6_invariant_rules,
    scan_l6_text,
)


def test_compatibility_matrix_is_not_permit_and_major_change_requires_governance():
    matrix = L6CompatibilityMatrix()
    assert matrix.grants_permit is False
    assert matrix.requires_governance_for(L6ContractChangeKind.MAJOR) is True
    assert matrix.requires_governance_for(L6ContractChangeKind.PATCH) is False
    with pytest.raises(ValueError):
        L6CompatibilityMatrix(grants_permit=True)


def test_migration_rollback_hotswitch_replay_declarations_are_not_execution():
    assert L6MigrationPlanDeclaration().applies_migration is False
    assert L6RollbackRouteDeclaration().applies_rollback is False
    assert L6HotSwitchReadinessDeclaration().performs_hot_switch is False
    assert L6ReplayCompatibilityDeclaration().action_replay_allowed is False
    with pytest.raises(ValueError):
        L6MigrationPlanDeclaration(applies_migration=True)
    with pytest.raises(ValueError):
        L6RollbackRouteDeclaration(applies_rollback=True)
    with pytest.raises(ValueError):
        L6HotSwitchReadinessDeclaration(performs_hot_switch=True)
    with pytest.raises(ValueError):
        L6ReplayCompatibilityDeclaration(action_replay_allowed=True)


def test_major_contract_change_has_migration_rollback_replay_l5_review_refs():
    assessment = L6BreakingChangeAssessment(change_kind=L6ContractChangeKind.MAJOR)
    assert assessment.major_change_has_required_controls is True


def test_contract_patch_quality_gate_requires_l5_compatibility_review_and_no_apply():
    assert L6ContractPatchQualityGateDecision().allow_freeze_contract_patch is False
    assert L6ContractPatchQualityGateDecision().allow_planning_patch_review is True
    assert L6ContractPatchQualityGateDecision(full_pytest_passed_for_freeze=True).allow_freeze_contract_patch is True
    assert L6ContractPatchQualityGateDecision(l5_compatibility_review_passed=False).allow_freeze_contract_patch is False
    assert L6ContractPatchQualityGateDecision(p0_count=1).allow_freeze_contract_patch is False
    with pytest.raises(ValueError):
        L6ContractPatchQualityGateDecision(applies_patch=True)


def test_public_contract_patch_projection_is_minimal_disclosure():
    projection = L6ContractPatchPublicProjection()
    assert projection.contains_raw_contract_body is False
    assert projection.contains_private_plugin_data is False
    with pytest.raises(ValueError):
        L6ContractPatchPublicProjection(contains_raw_contract_body=True)
    with pytest.raises(ValueError):
        L6ContractPatchPublicProjection(contains_private_plugin_data=True)


def test_phase2_quality_gate_blocks_p0_p1_and_hard_invariants():
    assert L6Phase2QualityGateDecision().allow_enter_phase3 is False
    assert L6Phase2QualityGateDecision().allow_planning_continuation is True
    assert L6Phase2QualityGateDecision(full_pytest_passed_for_freeze=True).allow_enter_phase3 is True
    assert L6Phase2QualityGateDecision(p0_count=1).allow_enter_phase3 is False
    assert L6Phase2QualityGateDecision(p1_count=1).allow_enter_phase3 is False
    assert L6Phase2QualityGateDecision(lifecycle_not_authorization_passed=False).allow_enter_phase3 is False
    assert L6Phase2QualityGateDecision(event_not_execution_passed=False).allow_enter_phase3 is False
    assert L6Phase2QualityGateDecision(projection_not_l2_fact_passed=False).allow_enter_phase3 is False
    assert L6Phase2QualityGateDecision(handoff_not_auto_merge_passed=False).allow_enter_phase3 is False
    assert L6Phase2QualityGateDecision(public_contract_breaking_plugin_blocked=False).allow_enter_phase3 is False
    assert L6Phase2QualityGateDecision(forbidden_scan_passed=False).allow_enter_phase3 is False
    assert L6Phase2QualityGateDecision(audit_evidence_chain_passed=False).allow_enter_phase3 is False


def test_phase2_quality_gate_does_not_accept_fake_full_pytest_value():
    assert L6Phase2QualityGateDecision(full_pytest_passed_for_freeze=False).full_pytest_passed_for_freeze is False
    with pytest.raises(ValueError):
        L6Phase2QualityGateDecision(full_pytest_passed_for_freeze="passed")


def test_phase2_test_evidence_index_and_regression_matrix_are_required_refs():
    assert L6Phase2TestEvidenceIndex().evidence_refs
    assert L6Phase2RegressionMatrix().passed is True
    assert L6Phase2RegressionMatrix(missing_blocking_item_refs=("test:l6_missing",)).passed is False


def test_default_invariants_cover_phase2_core_rules():
    refs = {rule.invariant_ref for rule in default_l6_invariant_rules()}
    assert "invariant:l6_lifecycle_is_not_authorization" in refs
    assert "invariant:l6_event_is_not_execution" in refs
    assert "invariant:l6_projection_is_not_l2_fact" in refs
    assert "invariant:l6_handoff_is_not_auto_merge" in refs
    assert "invariant:l6_no_plugin_direct_import" in refs
    assert "invariant:l6_public_projection_minimal_disclosure" in refs
    assert len(refs) >= 24


def test_forbidden_scan_blocks_sdk_http_subprocess_state_write_and_legacy_terms():
    rules = default_l6_forbidden_scan_rules()
    clean = scan_l6_text("l6:clean", "model capability requirement only; event projection handoff refs", rules)
    assert clean.passed is True
    dirty = scan_l6_text(
        "l6:dirty",
        "import openai\nrequests.get('x')\nPath.write_text('x')\nwrite_l2_fact()\ndirect_call_plugin()\nAbilityPackagePort\nsubprocess",
        rules,
    )
    assert dirty.passed is False
    assert dirty.p0_count >= 6
