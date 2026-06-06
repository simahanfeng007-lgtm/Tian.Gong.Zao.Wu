from __future__ import annotations

import pytest

from tiangong_agent_runtime.affective_execution_route import AffectiveExecutionRouter
from tiangong_agent_runtime.affective_state import AffectiveState
from tiangong_agent_runtime.four_path_context_router import FourPathContextRouter
from tiangong_agent_runtime.lifecycle_coordinator import LifecycleCoordinator
from tiangong_agent_runtime.memory_recall_router import L640MemoryRecallRoute, PlannerMemoryHint
from tiangong_agent_runtime.model_planner import ModelPlanner
from tiangong_agent_runtime.planner_unified_consumption import PlannerUnifiedConsumptionBridge
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def _four_path_report():
    memory_route = L640MemoryRecallRoute(
        route_id="memory_route:l6_43_1_test",
        query_digest="query-digest",
        hints=(
            PlannerMemoryHint(
                memory_id="memory:1",
                sanitized_summary="用户偏好：交付完成后简短报告。",
                recall_score=0.88,
                evidence_refs=("evidence:memory:1",),
                content_digest="digest-1",
            ),
        ),
        planner_hint="memory planner hint",
    )
    affective_route = AffectiveExecutionRouter().route(AffectiveState())
    lifecycle_bundle = LifecycleCoordinator().build_bundle(
        active_user_task=True,
        user_allowed_autonomy=False,
        idle_seconds=0,
        budget_pressure=0.1,
        context_pressure=0.1,
    )
    return FourPathContextRouter().build(
        user_task="继续 Planner 消费层统一改造",
        memory_route=memory_route,
        affective_route=affective_route,
        lifecycle_bundle=lifecycle_bundle,
        budget_snapshot={"snapshot_id": "budget:test", "planner_budget_hint": "A0-A4 low friction"},
        provider_envelope={"schema": "provider:test", "summary": "no naked SDK"},
        quality_gate={"schema": "quality:test", "summary": "activation requires gate"},
    )


def test_planner_consumes_only_unified_context_pack_as_hint() -> None:
    report = _four_path_report()
    bridge = PlannerUnifiedConsumptionBridge()
    hint = bridge.build_context_hint(report)
    text = hint.model_context_hint
    assert "UnifiedPlannerContextPack ONLY" in text
    assert "不得直接消费 Memory、Affective、Lifecycle 散对象" in text
    assert "用户偏好" in text
    assert "raw_memory_body" not in text.lower()
    assert hint.consumes_unified_context_pack_only is True
    assert hint.no_direct_execution is True
    assert hint.no_memory_write is True
    assert hint.no_kernel_mutation is True


def test_plan_preflight_keeps_a0_a4_low_friction_and_blocks_a5() -> None:
    bridge = PlannerUnifiedConsumptionBridge()
    allowed = ToolInvocation("return_analysis", {"content": "safe analysis"})
    confirm = ToolInvocation("write_workspace_file", {"path": "/absolute/needs_confirm.txt", "content": "draft"})
    blocked = ToolInvocation("unknown_tool", {"content": "x"})
    decision = bridge.preflight_plan([allowed, confirm, blocked])
    assert decision.passed is False
    assert len(decision.allowed_steps) == 1
    assert len(decision.confirmation_steps) == 1
    assert len(decision.blocked_steps) == 1
    assert decision.a0_a4_low_friction_preserved is True
    assert decision.a5_hard_boundary_preserved is True


def test_preflight_blocks_sensitive_raw_memory_or_secret_arguments() -> None:
    bridge = PlannerUnifiedConsumptionBridge()
    decision = bridge.preflight_plan(
        [ToolInvocation("return_analysis", {"raw_memory_body": "secret body"}), ToolInvocation("return_analysis", {"content": "api_key=abc"})]
    )
    assert decision.passed is False
    assert len(decision.blocked_steps) == 2
    rendered = str(decision.public_dict()).lower()
    assert "sensitive" in rendered


class _FakeChatResult:
    content = '{"steps":[{"tool_name":"return_analysis","arguments":{"content":"ok"},"reason":"safe"}]}'


class _FakeModelClient:
    def __init__(self) -> None:
        self.messages = []

    def chat(self, messages, model_config):
        self.messages = messages
        return _FakeChatResult()


class _FakeModelConfig:
    api_key = "fake-key"


def test_model_planner_receives_unified_pack_hint_and_plan_is_preflighted() -> None:
    report = _four_path_report()
    client = _FakeModelClient()
    result, consumption = PlannerUnifiedConsumptionBridge().build_model_plan(
        ModelPlanner(),
        "输出安全分析",
        four_path_report=report,
        model_config=_FakeModelConfig(),
        model_client=client,
        max_steps=3,
    )
    assert result.ok is True
    assert consumption.status == "planner_consumption_ready"
    assert consumption.plan_preflight.passed is True
    joined = "\n".join(message["content"] for message in client.messages)
    assert "UnifiedPlannerContextPack ONLY" in joined
    assert "context_digest" in joined


def test_bridge_rejects_non_four_path_report_and_failed_preflight() -> None:
    bridge = PlannerUnifiedConsumptionBridge()
    with pytest.raises(TypeError):
        bridge.build_context_hint({"memory": "scatter"})  # type: ignore[arg-type]
