import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASELINE = ROOT / "docs" / "l3_phase1_l0_l1_l2_hash_before.txt"


MATH_ENGINE_PATCH_ALLOWED_L1_L2_CHANGES = {
    "tiangong_kernel/l1_ports/__init__.py",
    "tiangong_kernel/l1_ports/approval_human_gate_ports.py",
    "tiangong_kernel/l1_ports/audit_chain_ports.py",
    "tiangong_kernel/l1_ports/communication_handoff_envelope_ports.py",
    "tiangong_kernel/l1_ports/contract_constraint_ports.py",
    "tiangong_kernel/l1_ports/context_belief_world_ports.py",
    "tiangong_kernel/l1_ports/effect_authorization_ports.py",
    "tiangong_kernel/l1_ports/external_adapter_ports.py",
    "tiangong_kernel/l1_ports/math_engine_contract_ports.py",
    "tiangong_kernel/l1_ports/math_model_ports.py",
    "tiangong_kernel/l1_ports/model_provider_governance_ports.py",
    "tiangong_kernel/l1_ports/memory_governance_ports.py",
    "tiangong_kernel/l1_ports/plugin_host_ports.py",
    "tiangong_kernel/l1_ports/resource_cost_ports.py",
    "tiangong_kernel/l1_ports/security_boundary_ports.py",
    "tiangong_kernel/l1_ports/self_evolution_commit_ports.py",
    "tiangong_kernel/l1_ports/self_healing_ports.py",
    "tiangong_kernel/l1_ports/version_switch_ports.py",
    "tiangong_kernel/l2_state/__init__.py",
    "tiangong_kernel/l2_state/agent_state.py",
    "tiangong_kernel/l2_state/audit_chain_state.py",
    "tiangong_kernel/l2_state/belief_state.py",
    "tiangong_kernel/l2_state/communication_handoff_state.py",
    "tiangong_kernel/l2_state/context_state.py",
    "tiangong_kernel/l2_state/context_safety_state.py",
    "tiangong_kernel/l2_state/data_governance_state.py",
    "tiangong_kernel/l2_state/external_adapter_state.py",
    "tiangong_kernel/l2_state/goal_plan_state.py",
    "tiangong_kernel/l2_state/math_engine_state.py",
    "tiangong_kernel/l2_state/math_model_governance_state.py",
    "tiangong_kernel/l2_state/model_interaction_state.py",
    "tiangong_kernel/l2_state/memory_forgetting_state.py",
    "tiangong_kernel/l2_state/memory_state.py",
    "tiangong_kernel/l2_state/plugin_state.py",
    "tiangong_kernel/l2_state/resource_boundary_binding_state.py",
    "tiangong_kernel/l2_state/run_state.py",
    "tiangong_kernel/l2_state/security_state.py",
    "tiangong_kernel/l2_state/self_evolution_commit_state.py",
    "tiangong_kernel/l2_state/self_healing_state.py",
    "tiangong_kernel/l2_state/side_effect_governance_state.py",
    "tiangong_kernel/l2_state/version_switch_state.py",
    "tiangong_kernel/l2_state/world_state.py",
}


def test_l3_phase1_l0_hashes_match_and_math_patch_l1_l2_changes_are_whitelisted():
    expected = {}
    for line in BASELINE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, rel = line.split("  ", 1)
        expected[rel] = digest
    actual = {}
    for directory in ("tiangong_kernel/l0_primitives", "tiangong_kernel/l1_ports", "tiangong_kernel/l2_state"):
        for path in sorted((ROOT / directory).rglob("*.py")):
            actual[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    l0_actual = {rel: digest for rel, digest in actual.items() if rel.startswith("tiangong_kernel/l0_primitives/")}
    l0_expected = {rel: digest for rel, digest in expected.items() if rel.startswith("tiangong_kernel/l0_primitives/")}
    assert l0_actual == l0_expected

    changed_or_added = {
        rel
        for rel, digest in actual.items()
        if rel.startswith(("tiangong_kernel/l1_ports/", "tiangong_kernel/l2_state/"))
        and expected.get(rel) != digest
    }
    removed = {
        rel
        for rel in expected
        if rel.startswith(("tiangong_kernel/l1_ports/", "tiangong_kernel/l2_state/")) and rel not in actual
    }
    assert changed_or_added <= MATH_ENGINE_PATCH_ALLOWED_L1_L2_CHANGES
    assert removed == set()
