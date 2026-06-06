from tiangong_agent_runtime.affective_execution_route import AffectiveExecutionRouter
from tiangong_agent_runtime.affective_state import AffectiveState
from tiangong_agent_runtime.four_path_context_router import FourPathContextRouter, UnifiedPlannerContextPack
from tiangong_agent_runtime.lifecycle_coordinator import LifecycleCoordinator
from tiangong_agent_runtime.memory_recall_router import L640MemoryRecallRoute, PlannerMemoryHint


def _memory_route(count=7):
    hints = tuple(
        PlannerMemoryHint(
            memory_id=f"memory:{idx}",
            sanitized_summary=f"安全摘要 {idx}",
            recall_score=max(0.0, 0.9 - idx * 0.04),
            evidence_refs=(f"evidence:memory:{idx}",),
            content_digest=f"digest-{idx}",
        )
        for idx in range(count)
    )
    return L640MemoryRecallRoute(
        route_id="memory_route:l6_40_test",
        query_digest="query-digest",
        hints=hints,
        planner_hint="memory planner hint",
    )


def _affective_route():
    return AffectiveExecutionRouter().route(AffectiveState())


def _lifecycle_bundle():
    return LifecycleCoordinator().build_bundle(
        active_user_task=True,
        user_allowed_autonomy=False,
        idle_seconds=0.0,
        budget_pressure=0.15,
        context_pressure=0.20,
        notes="L6.43 test lifecycle",
    )


def test_four_path_router_builds_unified_planner_context_pack_with_limits():
    report = FourPathContextRouter().build(
        user_task="继续 L6.43 四主路径统一投影",
        memory_route=_memory_route(7),
        affective_route=_affective_route(),
        lifecycle_bundle=_lifecycle_bundle(),
        provider_envelope={"schema": "test.provider", "fallback_reason": "sample replay only"},
        budget_snapshot={"snapshot_id": "budget:test", "planner_budget_hint": "A0-A4 low friction", "resource_exhausted": False},
        skill_envelope={"execution_hints": [{"skill_name": "test_skill", "hint_text": "draft only"}]},
        handoff_envelope={"parent_collect_report": {"suggested_parent_steps": ["return to parent chain"]}},
        quality_gate={"schema": "test.quality", "summary": "activation requires quality gate"},
        notes="no core pollution",
    )
    pack = report.context_pack
    assert report.status == "four_path_context_ready"
    assert report.preflight.passed is True
    assert len(pack.top_memory_hints) == 5
    assert len(pack.lifecycle_next_action_hints) <= 3
    assert pack.planner_consumable is True
    assert pack.no_second_runtime is True
    assert pack.no_direct_execution is True
    assert pack.no_tool_dispatch is True
    assert pack.no_kernel_mutation is True
    assert pack.summary_only is True
    assert pack.evidence_ref_only is True
    assert pack.a0_a4_low_friction is True
    assert pack.a5_hard_boundary_preserved is True
    assert report.priority_policy.execution_contract_first is True


def test_four_path_router_redacts_sensitive_evidence_projection():
    report = FourPathContextRouter().build(
        user_task="包含路径 /home/user/project 和 token=abc123 的用户输入必须脱敏",
        memory_route=_memory_route(1),
        affective_route=_affective_route(),
        lifecycle_bundle=_lifecycle_bundle(),
        provider_envelope={"schema": "provider", "summary": "api_key=abc secret=xyz /tmp/raw/path/file.txt"},
    )
    rendered = str(report.public_dict()).lower()
    assert "abc123" not in rendered
    assert "api_key=abc" not in rendered
    assert "secret=xyz" not in rendered
    assert "/tmp/raw/path" not in rendered
    assert "[redacted-sensitive]" in rendered or "[redacted-path]" in rendered
    assert report.context_pack.redacted_evidence_refs


def test_unified_planner_context_pack_rejects_more_than_five_memory_hints():
    too_many = tuple({"memory_id": str(i), "sanitized_summary": "x"} for i in range(6))
    try:
        UnifiedPlannerContextPack(
            pack_id="bad",
            user_task_summary="task",
            execution_contract_ref="execution_contract:L6.37",
            top_memory_hints=too_many,
        )
    except ValueError as exc:
        assert "at most 5 memory" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_four_path_router_policy_keeps_affective_and_lifecycle_non_executing():
    report = FourPathContextRouter().build(
        user_task="检查边界",
        memory_route=_memory_route(2),
        affective_route=_affective_route(),
        lifecycle_bundle=_lifecycle_bundle(),
    )
    data = report.public_dict()
    assert data["no_tool_invocation"] is True
    assert data["no_budget_mutation"] is True
    assert data["no_memory_write"] is True
    assert data["no_kernel_mutation"] is True
    decisions = data["priority_policy"]["decisions"]
    assert any(item["conflict"] == "Affective vs PermitGateway" and item["winner"] == "permit_gateway" for item in decisions)
    assert any(item["conflict"] == "Lifecycle vs UserTask" and item["winner"] == "current_user_task" for item in decisions)
