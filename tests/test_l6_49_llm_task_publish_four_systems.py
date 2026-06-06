from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

from tiangong_agent_runtime.affective_execution_route import AffectiveExecutionRouter
from tiangong_agent_runtime.affective_state import AffectiveStateEngine, SevenEmotionSignalSources, SixDesireSignalSources
from tiangong_agent_runtime.four_path_context_router import FourPathContextRouter
from tiangong_agent_runtime.lifecycle_coordinator import LifecycleCoordinator
from tiangong_agent_runtime.memory_math_core import MemoryCategory, MemoryLevel
from tiangong_agent_runtime.memory_recall_router import MemoryRecallRouter
from tiangong_agent_runtime.memory_store_bridge import MemoryRecord, MemoryStoreBridge
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.public_projection_bridge import build_desktop_dashboard_projection
from tiangong_agent_runtime.runtime_entry import RuntimeEntry


class FakeLLMTaskPublisher:
    """离线模拟 LLM 发布任务；只返回 JSON plan，不触网不读凭证。"""

    def chat(self, messages, config):  # noqa: ANN001 - 与项目 model_client duck typing 保持一致
        payload = {
            "output": {
                "steps": [
                    {
                        "tool_name": "build_l6_39_memory_integration",
                        "arguments": {"notes": "模拟 LLM 发布：读取记忆摘要，不写长期记忆", "max_items": 5},
                        "reason": "检查记忆/遗忘路径只读接入",
                    },
                    {
                        "tool_name": "build_l6_38_budget_snapshot",
                        "arguments": {"notes": "模拟 LLM 发布：生成预算快照", "max_steps": 8, "planned_steps": 4},
                        "reason": "检查执行链预算分池投影",
                    },
                    {
                        "tool_name": "build_l6_39_quality_gate_integration",
                        "arguments": {"notes": "模拟 LLM 发布：质量门引用检查"},
                        "reason": "检查质量门仍在链上",
                    },
                    {
                        "tool_name": "build_l6_39_recovery_integration",
                        "arguments": {"notes": "模拟 LLM 发布：恢复续接票据检查", "max_items": 5},
                        "reason": "检查生命周期/恢复候选不直接执行补丁",
                    },
                    {
                        "tool_name": "return_analysis",
                        "arguments": {"content": "四主路径模拟任务已进入 Runtime 执行链；本步骤为审计型最终分析返回，不写文件不调工具。"},
                        "reason": "模拟 assistant_final 可回收输出",
                    },
                ]
            }
        }
        return SimpleNamespace(content=json.dumps(payload, ensure_ascii=False), provider="fake-llm", model="task-publisher")


def test_l6_49_llm_task_publish_drives_four_main_paths_without_core_pollution(tmp_path: Path) -> None:
    store = MemoryStoreBridge(tmp_path / "memory.jsonl")
    store.add_candidate(
        MemoryRecord(
            memory_id="mem_l6_49_sim_1",
            memory_level=MemoryLevel.L4,
            memory_category=MemoryCategory.PROCEDURAL,
            sanitized_summary="L6.49 模拟任务发布应优先验证执行链、记忆、情感、生命周期四主路径，禁止前端裸写记忆。",
            evidence_refs=("evidence:l6_49_sim",),
            source_audit_refs=("audit:l6_49_sim",),
            confidence_score=0.93,
            importance_score=0.82,
            task_relevance_score=0.95,
            reuse_count=3,
            success_count=3,
            public_projection_allowed=True,
        )
    )
    memory_route = MemoryRecallRouter(store).route("L6.49 四主路径 模拟 LLM 任务发布", top_k=5)

    affective_state = AffectiveStateEngine().evolve(
        SevenEmotionSignalSources(
            joy_reward_signal=0.35,
            reflection_load_signal=0.8,
            uncertainty_future_risk_signal=0.35,
        ),
        SixDesireSignalSources(
            achievement_goal_gap_signal=0.85,
            order_entropy_signal=0.75,
            curiosity_knowledge_gap_signal=0.45,
        ),
    )
    affective_route = AffectiveExecutionRouter().route(affective_state)

    lifecycle_bundle = LifecycleCoordinator().build_bundle(
        active_user_task=True,
        user_allowed_autonomy=False,
        user_requested_learning=True,
        user_confirmed_iteration=False,
        idle_seconds=0,
        budget_pressure=0.15,
        context_pressure=0.25,
        notes="L6.49 模拟发布时用户任务优先，生命周期只能输出候选。",
        conversation_need_refs=["conversation_need:l6_49_task_publish"],
        user_feedback_refs=["feedback:l6_49_simulation"],
        long_term_goal_refs=["goal:l6_four_path_stability"],
    )

    four_path_report = FourPathContextRouter().build(
        user_task="模拟 LLM 发布任务，验证四主路径是否正常运行。",
        memory_route=memory_route,
        affective_route=affective_route,
        lifecycle_bundle=lifecycle_bundle,
        budget_snapshot={
            "snapshot_id": "budget:l6_49_sim",
            "resource_exhausted": False,
            "planner_budget_hint": "A0-A4 low friction",
        },
        quality_gate={"schema": "quality:l6_49_sim", "summary": "质量门仅引用，不自动放行发布。"},
        notes="L6.49 simulation",
    )

    rt = RuntimeEntry()
    result = rt.run_planner_execution_task(
        "模拟 LLM 发布任务：检查执行、记忆、情感、生命周期四主路径。",
        workspace=tmp_path,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=SimpleNamespace(api_key="sk-test-should-not-leak", provider="fake", model="task-publisher", has_real_api_key=False),
        model_client=FakeLLMTaskPublisher(),
        max_steps=8,
        external_context_hint=four_path_report.summary_text(),
    )

    dashboard = build_desktop_dashboard_projection(
        result.projection,
        task_title="L6.49 模拟 LLM 任务发布",
        quality_gate=rt.quality_gate_snapshot(),
        audit_events=result.audit_events,
        context_snapshot=rt.context_snapshot(),
        budget_snapshot={"current_consumption": len(result.results), "task_count": len(result.plan), "balance": "not_reported"},
        conversation_guide="固定聊天输入栏；只读展示四主路径投影。",
    ).public_dict()

    assert result.planner_result is not None and result.planner_result.ok is True
    assert [step.tool_name for step in result.plan] == [
        "build_l6_39_memory_integration",
        "build_l6_38_budget_snapshot",
        "build_l6_39_quality_gate_integration",
        "build_l6_39_recovery_integration",
        "return_analysis",
    ]
    assert result.projection.status == "ok"
    assert result.projection.chain["executed_steps"] == 5
    assert result.projection.chain["failure_count"] == 0
    assert all(tool_result.ok for tool_result in result.results)

    memory_payload = memory_route.public_dict()
    assert memory_payload["hints"]
    assert memory_payload["summary_only"] is True
    assert memory_payload["no_raw_memory_body"] is True
    assert memory_payload["no_long_term_write"] is True
    assert memory_payload["no_memory_deletion"] is True

    affective_payload = affective_route.public_dict()
    assert affective_payload["planner_consumable"] is True
    assert affective_payload["not_authorization"] is True
    assert affective_payload["not_refusal"] is True
    assert affective_payload["no_tool_dispatch"] is True
    assert affective_payload["no_quality_gate_override"] is True

    lifecycle_payload = lifecycle_bundle.public_dict()
    assert lifecycle_payload["planner_consumable"] is True
    assert lifecycle_payload["blocked_by_active_user_task"] is True
    assert lifecycle_payload["no_direct_execution"] is True
    assert lifecycle_payload["no_memory_write"] is True
    assert lifecycle_payload["no_patch_apply"] is True
    assert lifecycle_payload["no_hot_switch"] is True

    four_path_payload = four_path_report.public_dict()
    assert four_path_payload["status"] == "four_path_context_ready"
    assert four_path_payload["preflight"]["passed"] is True
    assert four_path_payload["context_pack"]["execution_first"] is True
    assert four_path_payload["context_pack"]["a5_hard_boundary_preserved"] is True
    assert four_path_payload["no_memory_write"] is True
    assert four_path_payload["no_tool_invocation"] is True

    for flag in (
        "frontend_readonly",
        "projection_only",
        "no_direct_tool_call",
        "no_provider_sdk",
        "no_memory_write",
        "no_self_iteration_merge",
        "no_plain_endpoint",
        "no_plain_token",
    ):
        assert dashboard[flag] is True
    rendered = json.dumps(dashboard, ensure_ascii=False).lower()
    assert "sk-test-should-not-leak" not in rendered
    assert "http://" not in rendered and "https://" not in rendered
