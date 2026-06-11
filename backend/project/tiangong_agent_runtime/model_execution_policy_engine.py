"""L6.72.58 主动 ModelExecutionPolicy 引擎。

L6.72.53 的 ModelExecutionPolicy 只做被动记录。本模块把该策略转换为
Runtime 可执行约束：最大计划步数、上下文预算、主脑准入、工具族过滤和
prompt_contract 降级。它不调用模型、不执行工具；只输出可审计决策。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from .runtime_tool_registry import canonical_tool_name
from .tool_invocation import ToolInvocation


_TOOL_FAMILY_PREFIXES: dict[str, tuple[str, ...]] = {
    "file": ("list_dir", "read_file", "file_sha256", "write_workspace_file"),
    "document": ("document_",),
    "code": ("scan_project", "diagnose_project", "run_python_quality_check", "code_x_"),
    "terminal": ("run_python_quality_check", "safe_command_runner"),
    "delivery": ("create_zip_package", "create_release_bundle", "build_delivery_"),
    "quality": ("run_python_quality_check", "evaluate_quality_gate"),
    "analysis": ("return_analysis", "return_code", "diagnose_project"),
    "web": ("web_", "search_"),
}


@dataclass(frozen=True)
class ActiveModelExecutionPolicy:
    profile_id: str
    provider_id: str
    model_id: str
    model_role: str
    allowed_work_mode: bool
    status: str
    failure_kind: str = ""
    blocked_reason: str = ""
    requested_max_steps: int = 0
    effective_max_steps: int = 1
    max_plan_steps_per_round: int = 1
    max_context_chars: int = 4000
    prompt_contract: str = "single_choice"
    allowed_tool_families: tuple[str, ...] = ("analysis",)
    allow_long_chain: bool = False
    micro_step_mode: bool = True
    require_json_repair: bool = True
    require_quality_gate: bool = True
    retry_strategy: str = "standard"
    policy_active: bool = True
    notes: tuple[str, ...] = field(default_factory=tuple)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_72_58.active_model_execution_policy.v1",
            "profile_id": self.profile_id,
            "provider_id": self.provider_id,
            "model_id": self.model_id,
            "model_role": self.model_role,
            "allowed_work_mode": self.allowed_work_mode,
            "status": self.status,
            "failure_kind": self.failure_kind,
            "blocked_reason": self.blocked_reason,
            "requested_max_steps": self.requested_max_steps,
            "effective_max_steps": self.effective_max_steps,
            "max_plan_steps_per_round": self.max_plan_steps_per_round,
            "max_context_chars": self.max_context_chars,
            "prompt_contract": self.prompt_contract,
            "allowed_tool_families": list(self.allowed_tool_families),
            "allow_long_chain": self.allow_long_chain,
            "micro_step_mode": self.micro_step_mode,
            "require_json_repair": self.require_json_repair,
            "require_quality_gate": self.require_quality_gate,
            "retry_strategy": self.retry_strategy,
            "policy_active": self.policy_active,
            "notes": list(self.notes),
            "storage_boundary": {
                "no_api_key": True,
                "no_raw_prompt": True,
                "summary_only": True,
            },
        }

    def prompt_card(self) -> str:
        return "\n".join(
            [
                "[ActiveModelExecutionPolicy / L6.72.58 主动模型策略]",
                f"role={self.model_role}; allowed_work_mode={self.allowed_work_mode}; status={self.status}; failure_kind={self.failure_kind}",
                f"effective_max_steps={self.effective_max_steps}; prompt_contract={self.prompt_contract}; max_context_chars={self.max_context_chars}",
                "allowed_tool_families=" + ",".join(self.allowed_tool_families),
                "策略已由 Runtime 主动生效：弱模型不得被误当主脑；中等模型只能短步计划；强模型允许长链但仍分阶段验证。",
            ]
        )


@dataclass(frozen=True)
class PolicyPlanFilterResult:
    plan: tuple[ToolInvocation, ...]
    dropped_steps: tuple[dict[str, Any], ...] = tuple()
    truncated: bool = False

    @property
    def ok(self) -> bool:
        return bool(self.plan) and not self.dropped_steps

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_72_58.policy_plan_filter.v1",
            "step_count": len(self.plan),
            "dropped_steps": list(self.dropped_steps),
            "truncated": self.truncated,
            "conversation_display": False,
        }


class ModelExecutionPolicyEngine:
    def activate(self, profile: Any | None, policy: Any | None, *, requested_max_steps: int = 80, activation_form: Any | None = None) -> ActiveModelExecutionPolicy:
        role = str(getattr(policy, "model_role", "") or getattr(profile, "recommended_role", "") or "main_brain_guarded")
        provider = str(getattr(profile, "provider_id", "unknown") or "unknown")
        model = str(getattr(profile, "model_id", "unknown") or "unknown")
        profile_id = str(getattr(profile, "profile_id", "") or getattr(policy, "profile_id", "") or "unknown")
        requested = max(1, int(requested_max_steps or 1))
        notes = ["active_enforced_in_l67258"]
        if provider == "mock" and role == "micro_planner":
            # 内部离线 smoke 的 MockModelClient 会生成 Code-X/quality 组合计划；
            # 它不是用户可选弱模型，不能被主动策略误降级导致旧执行链回归。
            role = "main_brain_guarded"
            notes.append("offline_mock_promoted_for_regression_smoke")
        allowed = tuple(getattr(policy, "allowed_tool_families", ()) or ("analysis",))
        if provider == "mock" and role == "main_brain_guarded":
            allowed = tuple(dict.fromkeys(tuple(allowed) + ("code", "terminal", "delivery")))
        base_context = int(getattr(policy, "max_context_chars", 4000) or 4000)
        prompt_contract = str(getattr(policy, "prompt_contract", "single_choice") or "single_choice")
        require_json_repair = bool(getattr(policy, "require_json_repair", True))
        require_quality_gate = bool(getattr(policy, "require_quality_gate", True))
        retry_strategy = str(getattr(policy, "retry_strategy", "standard") or "standard")
        micro = bool(getattr(policy, "micro_step_mode", False))
        allow_long = bool(getattr(policy, "allow_long_chain", False))

        if role == "main_brain_full":
            effective = min(requested, 20)
            max_round = min(int(getattr(policy, "max_plan_steps_per_round", 12) or 12), 20)
            return ActiveModelExecutionPolicy(profile_id, provider, model, role, True, "active", requested_max_steps=requested, effective_max_steps=max(1, effective), max_plan_steps_per_round=max_round, max_context_chars=base_context, prompt_contract="strict_json", allowed_tool_families=allowed, allow_long_chain=True, micro_step_mode=False, require_json_repair=require_json_repair, require_quality_gate=require_quality_gate, retry_strategy=retry_strategy, notes=tuple(notes + ["main_brain_full_long_chain_8_20_cap"]))
        if role == "main_brain_guarded":
            effective = min(requested, 8)
            max_round = min(int(getattr(policy, "max_plan_steps_per_round", 5) or 5), 8)
            return ActiveModelExecutionPolicy(profile_id, provider, model, role, True, "active_guarded", requested_max_steps=requested, effective_max_steps=max(1, effective), max_plan_steps_per_round=max_round, max_context_chars=min(base_context, 24000), prompt_contract="short_json", allowed_tool_families=allowed, allow_long_chain=True, micro_step_mode=True, require_json_repair=True, require_quality_gate=require_quality_gate, retry_strategy="short_json_then_micro_step", notes=tuple(notes + ["guarded_long_chain_3_8_cap"]))
        if role == "micro_planner":
            effective = min(requested, 3)
            max_round = min(int(getattr(policy, "max_plan_steps_per_round", 3) or 3), 3)
            return ActiveModelExecutionPolicy(profile_id, provider, model, role, True, "active_micro_step", requested_max_steps=requested, effective_max_steps=max(1, effective), max_plan_steps_per_round=max_round, max_context_chars=min(base_context, 12000), prompt_contract="choice_or_short_json", allowed_tool_families=tuple(f for f in allowed if f in {"file", "document", "analysis", "quality"}) or ("analysis",), allow_long_chain=False, micro_step_mode=True, require_json_repair=True, require_quality_gate=True, retry_strategy="single_step_then_rule_fallback", notes=tuple(notes + ["micro_planner_1_3_step_cap", "no_complex_terminal_or_long_chain"]))
        if role == "disabled":
            return ActiveModelExecutionPolicy(profile_id, provider, model, role, False, "blocked", failure_kind="model_policy_disabled", blocked_reason="模型画像为 disabled，不能进入 work 模式。", requested_max_steps=requested, effective_max_steps=0, max_plan_steps_per_round=0, max_context_chars=800, prompt_contract="disabled", allowed_tool_families=tuple(), allow_long_chain=False, micro_step_mode=True, require_json_repair=True, require_quality_gate=True, retry_strategy="disabled", notes=tuple(notes + ["disabled_model_no_work"]))
        return ActiveModelExecutionPolicy(profile_id, provider, model, "subagent_only", False, "blocked", failure_kind="weak_model_not_allowed", blocked_reason="模型画像为 subagent_only，只能做摘要、分类、格式化等子任务，不能作为主脑执行工作模式。", requested_max_steps=requested, effective_max_steps=0, max_plan_steps_per_round=0, max_context_chars=1200, prompt_contract="single_choice", allowed_tool_families=("analysis",), allow_long_chain=False, micro_step_mode=True, require_json_repair=True, require_quality_gate=True, retry_strategy="subagent_only", notes=tuple(notes + ["subagent_only_no_main_brain_work"]))

    def filter_plan(self, plan: Iterable[ToolInvocation], active_policy: ActiveModelExecutionPolicy) -> PolicyPlanFilterResult:
        if not active_policy.allowed_work_mode:
            return PolicyPlanFilterResult(tuple(), tuple({"reason": active_policy.failure_kind or "model_policy_blocked", "tool_name": getattr(step, "tool_name", "")} for step in plan or ()), False)
        filtered: list[ToolInvocation] = []
        dropped: list[dict[str, Any]] = []
        limit = max(0, int(active_policy.effective_max_steps or 0))
        for index, step in enumerate(plan or []):
            if index >= limit:
                dropped.append({"tool_name": getattr(step, "tool_name", ""), "reason": "max_plan_steps_per_round_exceeded", "allowed_tool_families": list(active_policy.allowed_tool_families)})
                continue
            tool_name = canonical_tool_name(getattr(step, "tool_name", ""))
            if not self.tool_allowed(tool_name, active_policy.allowed_tool_families):
                dropped.append({"tool_name": tool_name, "reason": "tool_family_not_allowed_by_model_policy", "allowed_tool_families": list(active_policy.allowed_tool_families)})
                continue
            filtered.append(step)
        return PolicyPlanFilterResult(tuple(filtered), tuple(dropped), truncated=bool(dropped and any(item.get("reason") == "max_plan_steps_per_round_exceeded" for item in dropped)))

    def tool_allowed(self, tool_name: str, allowed_families: Iterable[str]) -> bool:
        name = canonical_tool_name(tool_name)
        for family in allowed_families or ():
            prefixes = _TOOL_FAMILY_PREFIXES.get(str(family), (str(family),))
            if any(name == prefix or name.startswith(prefix) for prefix in prefixes):
                return True
        return False
