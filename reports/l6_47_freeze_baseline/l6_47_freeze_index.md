# L6.47 冻结基线索引

## 核心结论
- 四主路径 L6.40-L6.46 已收口为冻结基线。
- 核心污染检查 PASS，changed_core_files=0。
- 未发现 P0/P1 问题。
- L6.47 不新增执行能力，只新增冻结报告、索引和回归测试。

## 关键文件
- reports/l6_47_freeze_baseline/freeze_baseline_manifest.json
- reports/l6_47_freeze_baseline/l6_47_21_step_freeze_matrix.md
- reports/l6_47_freeze_baseline/l6_47_freeze_handoff.txt

## 关键模块
- tiangong_agent_runtime/memory_math_core.py
- tiangong_agent_runtime/memory_store_bridge.py
- tiangong_agent_runtime/memory_write_filter.py
- tiangong_agent_runtime/forgetting_review_router.py
- tiangong_agent_runtime/memory_recall_router.py
- tiangong_agent_runtime/affective_state.py
- tiangong_agent_runtime/affective_execution_route.py
- tiangong_agent_runtime/affective_pressure_bridge.py
- tiangong_agent_runtime/lifecycle_coordinator.py
- tiangong_agent_runtime/self_healing_execution_route.py
- tiangong_agent_runtime/self_learning_route.py
- tiangong_agent_runtime/free_will_candidate_route.py
- tiangong_agent_runtime/self_iteration_route.py
- tiangong_agent_runtime/lifecycle_clock.py
- tiangong_agent_runtime/autonomous_goal_queue.py
- tiangong_agent_runtime/self_iteration_frontend_projection.py
- tiangong_agent_runtime/four_path_public_projection.py
- tiangong_agent_runtime/four_path_priority_policy.py
- tiangong_agent_runtime/four_path_context_router.py
- tiangong_agent_runtime/planner_unified_consumption.py
- tiangong_agent_runtime/budget_low_friction_governance.py
- tiangong_agent_runtime/rollback_audit_binding.py
- tiangong_agent_runtime/long_chain_failure_injection_harness.py
- tiangong_agent_runtime/long_chain_pressure_probe.py
