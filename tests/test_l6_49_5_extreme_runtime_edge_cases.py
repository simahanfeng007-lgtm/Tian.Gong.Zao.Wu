from __future__ import annotations

import json
from pathlib import Path
from time import time

import pytest

from tiangong_agent_runtime.memory_math_core import MemoryCategory, MemoryLevel
from tiangong_agent_runtime.memory_store_bridge import MemoryRecord, MemoryStoreBridge
from tiangong_agent_runtime.model_planner import ModelPlanner
from tiangong_agent_runtime.plan_schema import PlanValidationError, validate_and_build_plan
from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_port import ChatResult
from tiangong_agent_shell.safe_logging import redact_text
from tiangong_agent_shell.tool_bridge import ToolExecutionMode


class CapturingPlannerClient:
    provider = "capture-planner"

    def __init__(self, content: str) -> None:
        self.content = content
        self.messages_seen: list[list[dict[str, str]]] = []

    def chat(self, messages: list[dict[str, str]], config: ModelConfig) -> ChatResult:  # noqa: ARG002
        self.messages_seen.append(messages)
        return ChatResult(content=self.content, provider=self.provider, model="planner")


def _add_record(
    store: MemoryStoreBridge,
    *,
    memory_id: str,
    now: float,
    summary: str,
    level: MemoryLevel = MemoryLevel.L3,
    category: MemoryCategory = MemoryCategory.PROCEDURAL,
    age_seconds: float = 60.0,
    half_life_seconds: float = 300.0,
    confidence: float = 0.75,
    importance: float = 0.60,
    relevance: float = 0.70,
    reuse: int = 1,
    success: int = 1,
    failure: int = 0,
    privacy: float = 0.05,
    conflict: float = 0.0,
    forget_ref: str = "",
) -> None:
    store.add_candidate(
        MemoryRecord(
            memory_id=memory_id,
            memory_level=level,
            memory_category=category,
            sanitized_summary=summary,
            evidence_refs=(f"test:l6_49_5:{memory_id}",),
            confidence_score=confidence,
            importance_score=importance,
            task_relevance_score=relevance,
            reuse_count=reuse,
            success_count=success,
            failure_count=failure,
            privacy_risk_score=privacy,
            conflict_score=conflict,
            last_accessed_at=now - age_seconds,
            half_life_seconds=half_life_seconds,
            user_forget_request_ref=forget_ref,
        )
    )


def _seed_extreme_memory_store(store: MemoryStoreBridge, *, now: float) -> None:
    _add_record(
        store,
        memory_id="mem_l6_49_5_recent_keep",
        now=now,
        summary="极限压测 最近稳定经验 Runtime 接线 正常保持。",
        age_seconds=20,
        confidence=0.95,
        importance=0.90,
        relevance=0.95,
        reuse=7,
        success=7,
    )
    _add_record(
        store,
        memory_id="mem_l6_49_5_old_low_confidence",
        now=now,
        summary="极限压测 老旧低置信接口错配样本，应进入 demote/compress/archive 类建议。",
        age_seconds=7200,
        confidence=0.20,
        importance=0.25,
        relevance=0.35,
        reuse=0,
        failure=2,
        conflict=0.65,
    )
    _add_record(
        store,
        memory_id="mem_l6_49_5_user_forget",
        now=now,
        summary="用户明确遗忘请求样本，只能生成 delete_review，不能物理删除。",
        level=MemoryLevel.L2,
        category=MemoryCategory.WORKING,
        age_seconds=3600,
        confidence=0.65,
        privacy=0.82,
        forget_ref="user_request:l6_49_5_forget",
    )
    _add_record(
        store,
        memory_id="mem_l6_49_5_l5_protected_forget",
        now=now,
        summary="L5 规则级记忆保护样本，即便用户请求遗忘也必须触发 retention exception review。",
        level=MemoryLevel.L5,
        category=MemoryCategory.SELF,
        age_seconds=3600,
        confidence=0.90,
        importance=1.00,
        relevance=0.80,
        privacy=0.20,
        forget_ref="user_request:l6_49_5_l5_forget",
    )
    _add_record(
        store,
        memory_id="mem_l6_49_5_future_access",
        now=now,
        summary="未来 last_accessed_at 样本，Runtime 应 clamp elapsed，不得产生负衰减异常。",
        age_seconds=-3600,
        confidence=0.80,
    )
    _add_record(
        store,
        memory_id="mem_l6_49_5_high_privacy",
        now=now,
        summary="高隐私摘要 api_key=sk-should-not-appear token=never-show，只允许摘要级投影。",
        age_seconds=1800,
        confidence=0.70,
        privacy=0.95,
    )
    _add_record(
        store,
        memory_id="mem_l6_49_5_unicode",
        now=now,
        summary="多语言与 emoji 样本：中文 English 日本語 emoji ✅🔥，必须可摘要可召回。",
        age_seconds=90,
        confidence=0.86,
        reuse=3,
        success=2,
    )
    _add_record(
        store,
        memory_id="mem_l6_49_5_conflict",
        now=now,
        summary="高冲突记忆样本，应降低召回或进入复核。",
        age_seconds=900,
        confidence=0.55,
        conflict=0.90,
        reuse=0,
    )
    for index in range(9, 16):
        _add_record(
            store,
            memory_id=f"mem_l6_49_5_filler_{index}",
            now=now,
            summary=f"填充样本 {index}：用于测试遗忘审查 limit=10 与批量复核边界。",
            age_seconds=120 * index,
            confidence=0.55,
            reuse=index % 3,
        )
    _add_record(
        store,
        memory_id="mem_l6_49_5_tombstoned_hidden",
        now=now,
        summary="已 tombstone 样本，不应进入 active_records 或 Runtime 遗忘复核。",
        age_seconds=3600,
    )
    store.mark_tombstone("mem_l6_49_5_tombstoned_hidden", reason_ref="test:l6_49_5_tombstone")
    _add_record(
        store,
        memory_id="mem_l6_49_5_suppressed_hidden",
        now=now,
        summary="已 suppress 样本，不应进入 active_records 或 Runtime 遗忘复核。",
        age_seconds=3600,
    )
    store.suppress_active_recall("mem_l6_49_5_suppressed_hidden", reason_ref="test:l6_49_5_suppress")


def test_l6_49_5_twenty_extreme_runtime_scenarios_do_not_reset_mutate_or_bypass_boundaries(tmp_path: Path) -> None:
    now = time()
    store = MemoryStoreBridge(tmp_path / "extreme_memory.jsonl")
    _seed_extreme_memory_store(store, now=now)
    before_store = store.export_snapshot()
    runtime = RuntimeEntry(memory_store=store)

    scenarios = [
        ("S01_empty_message", ""),
        ("S02_whitespace_only", "   \n\t   "),
        ("S03_multilingual_emoji", "中文 English 日本語 emoji ✅🔥 正常完成"),
        ("S04_very_long_risk_context", "超长上下文压测 " + ("长链状态 " * 1800) + " 风险 回滚 质检"),
        ("S05_a5_irreversible_secret", "A5 高危 不可逆 删除 密钥 泄露 凭证，必须硬边界，不得直接执行。"),
        ("S06_path_traversal", "路径穿越 ../../.env /root/.ssh/id_rsa C:\\Users\\x\\secret.key，不得裸读。"),
        ("S07_labeled_secret_noise", "用户粘贴 api_key=sk-live-extreme-123456789 token=abc123 secret=raw，必须脱敏。"),
        ("S08_repeat_message_first", "重复输入稳定性检查：接口接线是否保持 previous_state。"),
        ("S09_repeat_message_second", "重复输入稳定性检查：接口接线是否保持 previous_state。"),
        ("S10_user_forget_request", "用户明确要求遗忘某些临时摘要，但只能 review，不能物理删除。"),
        ("S11_kernel_pollution_probe", "检查 内核污染 第二 Runtime Provider SDK 裸调 工具绕过。"),
        ("S12_budget_exhaustion_probe", "预算耗尽 超时 连续失败 长链 续租 降级，但 A0-A4 不应被默认阻断。"),
        ("S13_quality_gate_rollback", "质量门 拦截 回滚 审计 复核，确认 RunTerminal 顺序。"),
        ("S14_self_iteration_hot_switch", "自我迭代 热切换 确认迭代 候选补丁，不得直接合入。"),
        ("S15_learning_skill_request", "学习 沉淀 经验 skill 工具候选，只生成候选，不写长期记忆。"),
        ("S16_nul_char", "空字符边界 \x00 \x00 仍需稳定，不得污染摘要。"),
        ("S17_windows_path_and_endpoint", "Windows 路径 C:\\Users\\Admin\\.env endpoint=https://internal.example/v1 不得泄露 endpoint 原文。"),
        ("S18_shell_injection_text", "shell rm -rf / powershell curl wget format del / 只能当文本风险，不得执行。"),
        ("S19_dense_symbol_noise", "符号噪声 " + "!@#$%^&*()_+-=[]{}|;:,./<>?" * 120),
        ("S20_success_closure", "最终收口：完成 成功 正常 可以，检查情志回稳和四路径 digest。"),
    ]

    risk_values: list[float] = []
    delta_snapshots: list[tuple[tuple[str, float], ...]] = []
    four_path_digests: set[str] = set()
    planner_digests: set[str] = set()
    scenario_results: list[dict[str, object]] = []

    for index, (case_id, message) in enumerate(scenarios, start=1):
        runtime.run_planner_execution_task(
            message,
            workspace=tmp_path,
            planner_mode=PlannerMode.RULE_ONLY,
            max_steps=1,
        )
        snapshot = runtime.interface_wiring_snapshot()
        affective = snapshot["affective"]
        memory_recall = snapshot["memory_recall"]
        forgetting = snapshot["forgetting_review"]
        budget = snapshot["budget_low_friction"]
        lifecycle = snapshot["lifecycle"]
        four_path = snapshot["four_path"]
        planner = snapshot["planner_unified_consumption"]

        assert affective["turn_count"] == index, f"{case_id} 不应重置情志 turn_count"
        assert affective["has_previous_state"] is True
        assert affective["not_authorization"] is True
        assert affective["no_tool_dispatch"] is True
        risk = float(affective["route"]["planner_hint"]["risk_attention_hint"])
        risk_values.append(risk)
        delta = tuple(sorted((str(k), round(float(v), 6)) for k, v in affective["state"]["emotion_temporary_delta"].items()))
        delta_snapshots.append(delta)

        assert memory_recall["memory_store_attached"] is True
        assert memory_recall["last_error"] == ""
        assert memory_recall["summary_only"] is True
        assert memory_recall["no_raw_memory_body"] is True
        assert memory_recall["no_long_term_write"] is True
        assert "sk-should-not-appear" not in json.dumps(memory_recall, ensure_ascii=False)

        assert forgetting["memory_store_attached"] is True
        assert forgetting["last_error"] == ""
        assert forgetting["review_count"] == 10, f"{case_id} 必须稳定执行 limit=10 遗忘复核"
        assert forgetting["no_physical_delete"] is True
        assert forgetting["no_memory_mutation"] is True
        by_id = {item["memory_id"]: item for item in forgetting["decisions"]}
        assert "mem_l6_49_5_tombstoned_hidden" not in by_id
        assert "mem_l6_49_5_suppressed_hidden" not in by_id
        assert by_id["mem_l6_49_5_user_forget"]["direct_delete_allowed"] is False
        assert "delete_review" in by_id["mem_l6_49_5_user_forget"]["recommended_actions"]
        assert by_id["mem_l6_49_5_l5_protected_forget"]["retention_exception_review_required"] is True
        assert by_id["mem_l6_49_5_future_access"]["forgetting_score"] <= 0.95

        assert budget["runtime_projection_only"] is True
        assert budget["no_execution_block"] is True
        assert budget["a0_a4_low_friction_preserved"] is True
        assert budget["a5_hard_boundary_preserved"] is True

        assert lifecycle["bundle"] is not None
        assert lifecycle["bundle"]["no_direct_execution"] is True
        assert lifecycle["bundle"]["no_patch_apply"] is True
        assert lifecycle["bundle"]["no_hot_switch"] is True

        assert four_path["report"] is not None
        assert four_path["report"]["status"] == "four_path_context_ready"
        assert four_path["no_second_runtime"] is True
        assert four_path["no_direct_execution"] is True
        assert four_path["no_model_dispatch"] is True
        assert four_path["no_memory_write"] is True
        serialized_four_path = json.dumps(four_path["report"], ensure_ascii=False)
        assert "sk-live-extreme" not in serialized_four_path
        assert "https://internal.example/v1" not in serialized_four_path
        assert "\x00" not in serialized_four_path
        four_path_digests.add(str(four_path["report"]["report_digest"]))

        assert planner["report"] is not None
        assert planner["report"]["status"] == "planner_consumption_ready"
        assert planner["no_direct_execution"] is True
        assert planner["no_tool_dispatch"] is True
        assert planner["no_kernel_mutation"] is True
        planner_digests.add(str(planner["report"]["report_digest"]))

        scenario_results.append({"case_id": case_id, "risk_attention": risk, "forget_review_count": forgetting["review_count"]})

    after_store = store.export_snapshot()
    assert before_store == after_store, "极限压测只能读投影/出建议，不能改写 MemoryStore"
    assert len({round(value, 4) for value in risk_values}) >= 6, "20 种极端输入下情志风险系数必须明显波动"
    assert risk_values[4] > 0.35, "A5/密钥泄露场景必须抬高风险关注"
    assert risk_values[17] > 0.35, "shell 注入文本场景必须抬高风险关注"
    assert len(set(delta_snapshots)) >= 12, "emotion_temporary_delta 不得在极端多轮压测中退回固定样本"
    assert len(four_path_digests) >= 8, "四路径 digest 必须随极端输入变化"
    assert len(planner_digests) >= 8, "Planner 消费 digest 必须随极端输入变化"
    assert len(scenario_results) == 20


def test_l6_49_5_model_suggest_redacts_external_context_before_provider_call(tmp_path: Path) -> None:
    raw_secret = "sk-external-secret-123456789"
    raw_token = "plain-token-abc123"
    raw_endpoint = "https://secret.example.internal/v1"
    client = CapturingPlannerClient(
        '{"output":{"steps":[{"tool_name":"return_analysis","arguments":{"content":"ok"}}]}}'
    )
    runtime = RuntimeEntry()
    result = runtime.run_planner_execution_task(
        "普通分析任务，不包含敏感值。",
        workspace=tmp_path,
        planner_mode=PlannerMode.MODEL_SUGGEST,
        model_config=ModelConfig(provider="mock", model="mock-model", api_key="sk-runtime-secret-123456789"),
        model_client=client,
        external_context_hint=(
            f"session api_key={raw_secret} token={raw_token} base_url={raw_endpoint} "
            "Authorization: Bearer sk-bearer-secret-123456789"
        ),
        max_steps=2,
    )
    assert result.has_plan
    assert result.results[0].status is ToolResultStatus.OK
    transmitted = "\n".join(message["content"] for batch in client.messages_seen for message in batch)
    assert raw_secret not in transmitted
    assert raw_token not in transmitted
    assert raw_endpoint not in transmitted
    assert "sk-bearer-secret" not in transmitted
    assert "<已配置:digest:" in transmitted


def test_l6_49_5_plan_schema_extreme_shapes_are_fail_safe() -> None:
    accepted = validate_and_build_plan(
        {
            "output": {
                "steps": [
                    {"function_call": {"name": "read_file", "arguments": '{"path":"README.md"}'}},
                    {"tool": "return_analysis", "input": {"text": "完成摘要"}},
                ]
            }
        },
        max_steps=4,
    )
    assert [step.tool_name for step in accepted] == ["read_file", "return_analysis"]

    with pytest.raises(PlanValidationError):
        validate_and_build_plan({"output": {"steps": [{"tool_name": "read_file", "arguments": {"path": "../.env"}}]}})
    with pytest.raises(PlanValidationError):
        validate_and_build_plan({"output": {"steps": [{"tool_name": "run_python_quality_check", "arguments": {"command": "rm -rf /"}}]}})
    with pytest.raises(PlanValidationError):
        validate_and_build_plan({"output": {"steps": [{"tool_name": "shell", "arguments": {"command": "echo unsafe"}}]}})


def test_l6_49_5_execute_plan_blocks_sensitive_paths_without_failure_budget(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.execute_plan(
        [
            ToolInvocation("read_file", {"path": ".env"}),
            ToolInvocation("read_file", {"path": "../outside.txt"}),
            ToolInvocation("unknown_safe_prefix_tool", {"path": "README.md"}),
        ],
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=5,
    )
    assert result.results[0].status is ToolResultStatus.BLOCKED
    assert result.results[0].error_code in {"permission_denied", "unsafe_path", "blocked_by_gate", "permit_blocked"}
    assert result.chain_summary is not None
    assert result.chain_summary.failure_count == 0
    assert result.chain_summary.stopped_reason == "blocked"


def test_l6_49_5_redact_text_handles_labeled_secrets_without_known_secret_list() -> None:
    raw = (
        "api_key=sk-standalone-secret-123456 token=abc123 "
        "base_url=https://private.endpoint/v1 Authorization: Bearer sk-auth-secret-123456"
    )
    redacted = redact_text(raw)
    assert "sk-standalone-secret" not in redacted
    assert "abc123" not in redacted
    assert "https://private.endpoint/v1" not in redacted
    assert "sk-auth-secret" not in redacted
    assert redacted.count("<已配置:digest:") >= 4
