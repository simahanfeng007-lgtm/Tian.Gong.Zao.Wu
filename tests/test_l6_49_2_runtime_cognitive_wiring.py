from __future__ import annotations

from time import time

from tiangong_agent_runtime.memory_math_core import MemoryCategory, MemoryLevel
from tiangong_agent_runtime.memory_store_bridge import MemoryRecord, MemoryStoreBridge
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def test_l6_49_2_runtime_affective_state_carries_previous_state_across_turns(tmp_path) -> None:
    rt = RuntimeEntry()

    rt.run_planner_execution_task(
        "确认这个 bug 是否存在，做风险复核和最小修复。",
        workspace=tmp_path,
        planner_mode=PlannerMode.RULE_ONLY,
        max_steps=1,
    )
    first = rt.affective_runtime_snapshot()

    rt.run_planner_execution_task(
        "确认这个 bug 是否存在，做风险复核和最小修复。",
        workspace=tmp_path,
        planner_mode=PlannerMode.RULE_ONLY,
        max_steps=1,
    )
    second = rt.affective_runtime_snapshot()

    assert first["turn_count"] == 1
    assert second["turn_count"] == 2
    assert first["has_previous_state"] is True
    assert second["has_previous_state"] is True

    first_delta = first["state"]["emotion_temporary_delta"]
    second_delta = second["state"]["emotion_temporary_delta"]
    assert first_delta != second_delta
    assert second["route"]["planner_consumable"] is True
    assert second["not_authorization"] is True
    assert second["no_tool_dispatch"] is True


def test_l6_49_2_runtime_forgetting_review_uses_record_vector_signature_without_mutation(tmp_path) -> None:
    store = MemoryStoreBridge(tmp_path / "memory.jsonl")
    now = time()
    store.add_candidate(
        MemoryRecord(
            memory_id="mem_l6_49_2_old_low_confidence",
            memory_level=MemoryLevel.L3,
            memory_category=MemoryCategory.PROCEDURAL,
            sanitized_summary="旧执行经验，低信心且长期未复用，应该进入遗忘复核候选。",
            evidence_refs=("evidence:l6_49_2_forget",),
            source_audit_refs=("audit:l6_49_2_forget",),
            confidence_score=0.20,
            importance_score=0.30,
            task_relevance_score=0.20,
            reuse_count=0,
            success_count=0,
            failure_count=1,
            privacy_risk_score=0.10,
            conflict_score=0.70,
            last_accessed_at=now - 4000,
            half_life_seconds=100,
        )
    )
    before = store.export_snapshot()
    rt = RuntimeEntry(memory_store=store)

    rt.run_planner_execution_task(
        "执行一次普通任务，同时让 Runtime 运行遗忘复核。",
        workspace=tmp_path,
        planner_mode=PlannerMode.RULE_ONLY,
        max_steps=1,
    )

    snapshot = rt.forgetting_review_runtime_snapshot()
    after = store.export_snapshot()
    assert snapshot["memory_store_attached"] is True
    assert snapshot["last_error"] == ""
    assert snapshot["review_count"] == 1
    decision = snapshot["decisions"][0]
    assert decision["memory_id"] == "mem_l6_49_2_old_low_confidence"
    assert decision["forgetting_score"] > 0.5
    assert "demote" in decision["recommended_actions"] or "archive" in decision["recommended_actions"]
    assert decision["direct_delete_allowed"] is False
    assert snapshot["no_physical_delete"] is True
    assert snapshot["no_memory_mutation"] is True
    assert before == after
