from tiangong_kernel.l5_plugin_host import AFFECTIVE_ALLOWED_MODULATION_REFS, L5CapabilityReadinessMatrix, L5CapabilityReadinessMatrixValidator


_ALLOWED_SUFFIXES = {
    "expression_style",
    "attention_bias",
    "priority_bias",
    "memory_weight_bias",
    "risk_sensitivity_bias",
    "learning_motivation_bias",
}


def test_affective_state_only_modulates_expression_attention_priority_memory_risk_learning():
    assert {ref.split(":", 1)[1] for ref in AFFECTIVE_ALLOWED_MODULATION_REFS} == _ALLOWED_SUFFIXES
    assert all("execution" not in ref for ref in AFFECTIVE_ALLOWED_MODULATION_REFS)
    assert all("authorization" not in ref for ref in AFFECTIVE_ALLOWED_MODULATION_REFS)


def test_affective_capability_readiness_is_l6_planning_only():
    matrix = L5CapabilityReadinessMatrix()
    readiness = dict(matrix.readiness_rows)
    assert readiness["AffectiveModulationCapability"] == "l6_planning_only"
    assert readiness["AffectiveExpressionStyleCapability"] == "l6_planning_only"
    assert matrix.affective_plugin_scope == "l6_planning_only"
    assert matrix.allow_execute_affective_plugin is False
    assert L5CapabilityReadinessMatrixValidator().check(matrix)
