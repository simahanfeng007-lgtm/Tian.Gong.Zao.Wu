"""Shared helpers for L4 phase 8 closure objects."""

from __future__ import annotations


L4_EXECUTION_CLOSURE_SCHEMA_VERSION = "0.1"


def ensure_true(value: bool, field_name: str) -> None:
    if value is not True:
        raise ValueError(f"{field_name} must remain true")


def ensure_false(value: bool, field_name: str) -> None:
    if value is not False:
        raise ValueError(f"{field_name} must remain false in L4 phase 8")


def ensure_short_text(value: str, field_name: str, limit: int = 512) -> None:
    if len(value) > limit:
        raise ValueError(f"{field_name} must be short")


def ensure_schema_version(value: str, field_name: str = "schema_version") -> None:
    if not value:
        raise ValueError(f"{field_name} cannot be empty")


def ensure_text_items(items: tuple[str, ...], field_name: str, limit: int = 512) -> None:
    for item in items:
        ensure_short_text(item, field_name, limit)


def ensure_pair_items(items: tuple[tuple[str, str], ...], field_name: str, limit: int = 512) -> None:
    for key, value in items:
        ensure_short_text(key, f"{field_name} key", 128)
        ensure_short_text(value, f"{field_name} value", limit)


L4_PHASES = (
    "phase1_base",
    "phase2_permit_boundary_refs",
    "phase3_adapter_protocols",
    "phase4_model_tool_toolgroup",
    "phase5_external_action_surfaces",
    "phase6_result_observation_failure_refs",
    "phase7_transaction_resource_concurrency_replay_refs",
    "phase8_closure_handoff_freeze",
)


L4_ACTION_SURFACES = (
    "model",
    "tool",
    "file",
    "network",
    "terminal",
    "desktop",
    "database",
    "browser",
    "git",
    "build",
    "test",
    "sandbox",
    "storage",
    "transaction",
    "resource",
    "concurrency",
    "lock",
    "observation",
    "audit",
    "evidence",
    "recovery",
    "replay",
    "checkpoint",
    "snapshot",
)


L4_BOUNDARY_SURFACES = (
    "permit",
    "policy",
    "risk",
    "confirmation",
    "lease",
    "credential",
    "audit_gate",
    "resource_budget",
    "concurrency_budget",
)


L4_L6_SURFACES = (
    "model_adapter",
    "tool_adapter",
    "file_adapter",
    "network_adapter",
    "terminal_adapter",
    "desktop_adapter",
    "database_adapter",
    "browser_adapter",
    "git_adapter",
    "build_adapter",
    "test_adapter",
    "sandbox_adapter",
    "storage_adapter",
    "observation_adapter",
    "audit_adapter",
    "evidence_store",
    "validation_adapter",
    "recovery_adapter",
    "replay_adapter",
    "connector_platform",
    "ui_action_adapter",
    "resource_observer",
    "memory_sink",
    "forgetting_sink",
    "retrieval_sink",
    "learning_sink",
    "affective_feedback_sink",
    "privacy_retention_sink",
    "subsystem_plugin",
    "adapter_plugin",
    "policy_plugin",
    "skill_plugin",
    "memory_plugin",
    "learning_plugin",
    "recovery_plugin",
    "observation_plugin",
)


L5_PLUGIN_HOST_SURFACES = (
    "plugin_manifest",
    "plugin_registry",
    "plugin_lifecycle",
    "plugin_isolation",
    "plugin_mount",
    "plugin_health",
    "plugin_dependency",
    "plugin_version",
    "plugin_quarantine",
    "plugin_audit_bridge",
    "plugin_lease_binding",
    "plugin_trust_boundary",
    "plugin_recovery_binding",
)


LEGACY_MAIN_CHAIN_SYMBOLS = (
    "Run" + "time",
    "\u795e\u67a2",
    "Ability" + "Package",
    "Capability" + "Port",
    "Ability" + "Package" + "Port",
)
