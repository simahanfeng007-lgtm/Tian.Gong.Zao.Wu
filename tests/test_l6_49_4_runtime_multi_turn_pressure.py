from __future__ import annotations

from pathlib import Path
from time import time

from tiangong_agent_runtime.memory_math_core import MemoryCategory, MemoryLevel
from tiangong_agent_runtime.memory_store_bridge import MemoryRecord, MemoryStoreBridge
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry


def _seed_pressure_memory(store: MemoryStoreBridge, *, now: float) -> None:
    records = [
        MemoryRecord(
            memory_id="mem_l6_49_4_runtime_wiring_baseline",
            memory_level=MemoryLevel.L3,
            memory_category=MemoryCategory.PROCEDURAL,
            sanitized_summary="Runtime 接线 情志 previous_state 遗忘审查 生命周期 四路径 预算 Planner 消费 压测基线。",
            evidence_refs=("test:l6_49_4_pressure_baseline",),
            confidence_score=0.96,
            importance_score=0.90,
            task_relevance_score=0.95,
            reuse_count=6,
            success_count=6,
            privacy_risk_score=0.05,
            last_accessed_at=now - 30,
            half_life_seconds=300.0,
        ),
        MemoryRecord(
            memory_id="mem_l6_49_4_old_interface_mismatch",
            memory_level=MemoryLevel.L3,
            memory_category=MemoryCategory.PROCEDURAL,
            sanitized_summary="旧接口错配 TypeError 静默吞错 遗忘复核 高陈旧 低复用 压测样本。",
            evidence_refs=("test:l6_49_4_pressure_old",),
            confidence_score=0.22,
            importance_score=0.35,
            task_relevance_score=0.45,
            reuse_count=0,
            success_count=0,
            failure_count=1,
            privacy_risk_score=0.12,
            conflict_score=0.55,
            last_accessed_at=now - 7200,
            half_life_seconds=300.0,
        ),
        MemoryRecord(
            memory_id="mem_l6_49_4_user_forget_request",
            memory_level=MemoryLevel.L2,
            memory_category=MemoryCategory.WORKING,
            sanitized_summary="用户明确要求遗忘的临时摘要；压测只能生成 delete_review，不允许物理删除。",
            evidence_refs=("test:l6_49_4_pressure_forget_request",),
            confidence_score=0.70,
            importance_score=0.50,
            task_relevance_score=0.30,
            reuse_count=0,
            privacy_risk_score=0.80,
            last_accessed_at=now - 3600,
            half_life_seconds=300.0,
            user_forget_request_ref="user_request:l6_49_4_pressure",
        ),
    ]
    for record in records:
        store.add_candidate(record)


def test_l6_49_4_runtime_interfaces_survive_10_turn_pressure_without_state_reset_or_memory_mutation(tmp_path: Path) -> None:
    now = time()
    store = MemoryStoreBridge(tmp_path / "memory.jsonl")
    _seed_pressure_memory(store, now=now)
    before_store = store.export_snapshot()
    runtime = RuntimeEntry(memory_store=store)

    messages = [
        "第1轮：确认 Runtime 接口接线是否正常。",
        "第2轮：继续检查情志 previous_state 和遗忘审查。",
        "第3轮：压测多轮状态，关注生命周期和四路径。",
        "第4轮：模拟 bug 风险复核和回滚路径。",
        "第5轮：确认预算低摩擦治理不阻断 A0-A4。",
        "第6轮：连续任务后检查记忆召回是否稳定。",
        "第7轮：模拟 A5 高危 凭证 泄露 词，但仍不得直接调工具。",
        "第8轮：继续长链压测，检查 Planner 消费层。",
        "第9轮：确认没有内核污染、没有第二 Runtime、没有裸调 Provider。",
        "第10轮：收口压测，输出冻结验证状态。",
    ]

    risk_attention_values: list[float] = []
    delta_snapshots: list[dict[str, float]] = []
    four_path_digests: set[str] = set()
    planner_consumption_digests: set[str] = set()

    for index, message in enumerate(messages, start=1):
        runtime.run_planner_execution_task(
            message,
            workspace=tmp_path,
            planner_mode=PlannerMode.RULE_ONLY,
            max_steps=1,
        )
        snapshot = runtime.interface_wiring_snapshot()

        assert snapshot["no_second_runtime"] is True
        assert snapshot["no_direct_tool_call"] is True
        assert snapshot["no_provider_sdk_call"] is True
        assert snapshot["no_memory_mutation_from_projection"] is True
        assert snapshot["no_kernel_mutation"] is True

        affective = snapshot["affective"]
        assert affective["turn_count"] == index
        assert affective["has_previous_state"] is True
        assert affective["not_authorization"] is True
        assert affective["no_tool_dispatch"] is True
        assert affective["no_quality_gate_override"] is True
        risk_attention_values.append(float(affective["route"]["planner_hint"]["risk_attention_hint"]))
        delta_snapshots.append(dict(affective["state"]["emotion_temporary_delta"]))

        memory_recall = snapshot["memory_recall"]
        assert memory_recall["memory_store_attached"] is True
        assert memory_recall["last_error"] == ""
        assert memory_recall["route"] is not None
        assert memory_recall["route"]["hints"], "十轮压测中每轮都应真实调用 MemoryRecallRouter.route"
        assert memory_recall["no_raw_memory_body"] is True
        assert memory_recall["no_long_term_write"] is True
        assert memory_recall["no_memory_delete"] is True

        forgetting = snapshot["forgetting_review"]
        assert forgetting["memory_store_attached"] is True
        assert forgetting["last_error"] == ""
        assert forgetting["review_count"] == 3
        assert forgetting["no_physical_delete"] is True
        assert forgetting["no_memory_mutation"] is True
        by_id = {item["memory_id"]: item for item in forgetting["decisions"]}
        assert "delete_review" in by_id["mem_l6_49_4_user_forget_request"]["recommended_actions"]
        assert by_id["mem_l6_49_4_user_forget_request"]["direct_delete_allowed"] is False
        assert by_id["mem_l6_49_4_old_interface_mismatch"]["forgetting_score"] > 0.55

        budget = snapshot["budget_low_friction"]
        assert budget["runtime_projection_only"] is True
        assert budget["no_budget_mutation"] is True
        assert budget["no_execution_block"] is True
        assert budget["a0_a4_low_friction_preserved"] is True
        assert budget["a5_hard_boundary_preserved"] is True

        lifecycle = snapshot["lifecycle"]
        assert lifecycle["bundle"] is not None
        assert lifecycle["bundle"]["planner_hints"]
        assert lifecycle["bundle"]["no_direct_execution"] is True
        assert lifecycle["bundle"]["no_tool_invocation"] is True
        assert lifecycle["bundle"]["no_patch_apply"] is True
        assert lifecycle["bundle"]["no_hot_switch"] is True
        assert lifecycle["bundle"]["no_kernel_mutation"] is True

        four_path = snapshot["four_path"]
        assert four_path["report"] is not None
        assert four_path["report"]["status"] == "four_path_context_ready"
        assert four_path["report"]["context_pack"]["memory_hint_count"] >= 1
        assert four_path["report"]["context_pack"]["lifecycle_hint_count"] >= 1
        assert four_path["no_second_runtime"] is True
        assert four_path["no_direct_execution"] is True
        assert four_path["no_model_dispatch"] is True
        assert four_path["no_memory_write"] is True
        four_path_digests.add(str(four_path["report"]["report_digest"]))

        planner = snapshot["planner_unified_consumption"]
        assert planner["report"] is not None
        assert planner["report"]["status"] == "planner_consumption_ready"
        assert planner["report"]["context_hint"]["source_context_digest"]
        assert planner["no_second_runtime"] is True
        assert planner["no_direct_execution"] is True
        assert planner["no_tool_dispatch"] is True
        assert planner["no_kernel_mutation"] is True
        planner_consumption_digests.add(str(planner["report"]["report_digest"]))

    after_store = store.export_snapshot()
    assert before_store == after_store, "压测只能产生只读投影/复核建议，不能改写 MemoryStore"
    assert len(set(round(value, 4) for value in risk_attention_values)) >= 4, "情志风险关注系数必须随任务压力波动"
    assert risk_attention_values[6] > 0.35, "A5/凭证泄露输入必须提升风险关注，而不是固定常数"
    assert len({tuple(sorted(delta.items())) for delta in delta_snapshots}) == 10, "emotion_temporary_delta 必须跨十轮连续演化，不能每轮归零"
    assert len(four_path_digests) >= 3, "四路径报告必须随任务输入/状态变化，不应是固定样本"
    assert len(planner_consumption_digests) >= 3, "Planner 消费报告必须随四路径上下文变化"
