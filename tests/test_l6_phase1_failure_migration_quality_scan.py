import pytest

from tiangong_kernel.l6_plugins.common import (
    L6FailureContract,
    L6DegradationContract,
    L6MigrationContract,
    L6RollbackContract,
    L6HotSwitchReadinessContract,
    L6QualityGateDecision,
    default_l6_forbidden_scan_rules,
    scan_l6_text,
)


def test_failure_migration_rollback_hotswitch_are_inert_declarations():
    assert L6FailureContract().performs_recovery is False
    assert L6DegradationContract().degrades_by_self is False
    assert L6MigrationContract().applies_migration is False
    assert L6RollbackContract().applies_rollback is False
    assert L6HotSwitchReadinessContract().performs_hot_switch is False
    with pytest.raises(ValueError):
        L6MigrationContract(applies_migration=True)
    with pytest.raises(ValueError):
        L6RollbackContract(applies_rollback=True)
    with pytest.raises(ValueError):
        L6HotSwitchReadinessContract(performs_hot_switch=True)


def test_quality_gate_blocks_p0_and_p1_and_is_not_authorization():
    assert L6QualityGateDecision(p0_count=0, p1_count=0).allow_freeze_plugin is True
    assert L6QualityGateDecision(p0_count=1).allow_freeze_plugin is False
    assert L6QualityGateDecision(p1_count=1).allow_freeze_plugin is False
    with pytest.raises(ValueError):
        L6QualityGateDecision(is_execution_authorization=True)


def test_forbidden_scan_catches_model_sdk_http_secret_and_legacy_terms():
    rules = default_l6_forbidden_scan_rules()
    clean = scan_l6_text("l6:clean", "MODEL_REQUIREMENT_REF='model-cap:l6'", rules)
    assert clean.passed is True
    dirty = scan_l6_text("l6:dirty", "import openai\nbase_url='x'\napi_key='y'\nCapabilityPort\nsubprocess")
    assert dirty.passed is False
    assert dirty.p0_count >= 4
