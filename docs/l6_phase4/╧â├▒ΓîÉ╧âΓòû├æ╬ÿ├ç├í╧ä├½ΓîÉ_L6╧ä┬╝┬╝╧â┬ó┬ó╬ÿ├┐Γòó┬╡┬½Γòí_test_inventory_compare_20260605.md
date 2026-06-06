# L6 第四阶段 Test Inventory Compare

- old_tests=810
- new_tests=850
- added_tests=40
- removed_tests=0
- added_phase4_tests=40

新增 phase4 tests:
- `tests/test_l6_phase4_affective_context_hint_no_injection.py`
- `tests/test_l6_phase4_affective_direct_call_forbidden.py`
- `tests/test_l6_phase4_affective_governance_binding_no_synthetic_reason.py`
- `tests/test_l6_phase4_affective_memory_hint_no_write.py`
- `tests/test_l6_phase4_affective_pollution_no_delete.py`
- `tests/test_l6_phase4_affective_projection_is_not_fact.py`
- `tests/test_l6_phase4_affective_reentry_goes_through_l3_l5.py`
- `tests/test_l6_phase4_audit_evidence_chain_required.py`
- `tests/test_l6_phase4_belief_world_candidate_not_fact.py`
- `tests/test_l6_phase4_candidate_fact_review_not_l2_write.py`
- `tests/test_l6_phase4_cognitive_group_is_not_runtime.py`
- `tests/test_l6_phase4_cognitive_reentry_goes_through_l3_l5.py`
- `tests/test_l6_phase4_context_memory_forgetting_chain.py`
- `tests/test_l6_phase4_context_projection_not_prompt_injection.py`
- `tests/test_l6_phase4_declarations_inert.py`
- `tests/test_l6_phase4_fatigue_projection_no_refusal.py`
- `tests/test_l6_phase4_forbidden_scan_blocks_model_http_tool_state.py`
- `tests/test_l6_phase4_forbidden_scan_blocks_public_leakage.py`
- `tests/test_l6_phase4_forgetting_candidate_not_delete.py`
- `tests/test_l6_phase4_hash_digest_canonicalization.py`
- `tests/test_l6_phase4_humanized_refusal_requires_governance_reason.py`
- `tests/test_l6_phase4_interoperation_host_mediated_only.py`
- `tests/test_l6_phase4_invariant_suite_exists.py`
- `tests/test_l6_phase4_l5_protected_memory_retention_exception.py`
- `tests/test_l6_phase4_long_term_affective_drift_report_only.py`
- `tests/test_l6_phase4_memory_candidate_not_memory_write.py`
- `tests/test_l6_phase4_memory_proposal_goes_to_review.py`
- `tests/test_l6_phase4_product_bridge_seed_inert.py`
- `tests/test_l6_phase4_public_projection_hides_sensitive_payload.py`
- `tests/test_l6_phase4_public_projection_redaction.py`
- `tests/test_l6_phase4_quality_gate_blocks_p0_p1.py`
- `tests/test_l6_phase4_resource_pressure_not_fatigue.py`
- `tests/test_l6_phase4_score_models_explainable_and_bounded.py`
- `tests/test_l6_phase4_score_not_decision.py`
- `tests/test_l6_phase4_self_reflection_learning_not_auto_repair.py`
- `tests/test_l6_phase4_seven_emotions_no_permission_bypass.py`
- `tests/test_l6_phase4_six_desires_no_action_dispatch.py`
- `tests/test_l6_phase4_state_is_not_l2_fact.py`
- `tests/test_l6_phase4_user_forget_request_review_tombstone_suppression.py`
- `tests/test_l6_phase4_value_stability_not_value_dictatorship.py`

结论：未删除旧测试；新增 40 个 L6 phase4 targeted tests。
