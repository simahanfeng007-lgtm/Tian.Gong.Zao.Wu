from pathlib import Path


FORBIDDEN_TERMS = (
    "Runtime",
    "\u795e\u67a2",
    "AbilityPackage",
    "CapabilityPort",
    "AbilityPackagePort",
    "tiangong_kernel.l5",
    "tiangong_kernel.l6",
)


PHASE7_FILE_PREFIXES = (
    "concurrency_scope",
    "execution_checkpoint_ref",
    "execution_commit_intent",
    "execution_determinism_hint",
    "execution_idempotency_hint",
    "execution_isolation_context",
    "execution_lock_ref",
    "execution_operational_summary",
    "execution_reconciliation_advice",
    "execution_replay_summary",
    "execution_rollback_intent",
    "execution_side_effect_summary",
    "execution_snapshot_ref",
    "execution_transaction_ref",
    "execution_transaction_scope",
    "l4_to_l5_resource_feedback",
    "l4_to_l6_recovery_replay_requirement",
    "l5_concurrency_budget_port",
    "l5_resource_budget_port",
    "l6_recovery_service_port",
    "l6_replay_service_port",
    "phase7_invariants",
    "resource_budget_consumption_summary",
    "resource_budget_failure",
    "resource_budget_ref",
    "resource_usage_report",
    "transaction_resource_dry_run",
    "transaction_resource_fake",
    "transaction_resource_noop",
)


def test_l4_phase7_has_no_legacy_runtime_ability_package_or_future_layer_imports():
    root = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l4_action_grounding"
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in root.glob("*.py")
        if path.stem.startswith(PHASE7_FILE_PREFIXES)
    )

    for term in FORBIDDEN_TERMS:
        assert term not in source
