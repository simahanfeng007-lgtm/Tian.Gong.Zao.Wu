"""L6.72.55 AdaptiveWorkLoop V1。

目标：在 work 模式原计划失败后，只允许一次受控自适应修复。
- 不启动后台循环。
- 不绕过 PromptIntegrator。
- 不直接调用 adapter；repair plan 仍回到 PlannerExecutionController / ExecutionSpine 执行。
- 失败宁可 partial_with_resume，不假装 completed_pass。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from tiangong_agent_shell.prompt_compiler import RuntimeState, build_prompt_context, compile_prompt_envelope
from tiangong_agent_shell.safe_logging import redact_text

from .observation_normalizer import RepairContext, normalize_execution_observation
from .plan_schema import PlanValidationError, parse_plan_json, validate_and_build_plan, plan_to_public_dict
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult

ADAPTIVE_WORK_LOOP_SCHEMA = "tiangong.l6_72_55.adaptive_work_loop.v1"
REPAIR_PHASE = "adaptive_repair_plan"

RepairExecutor = Callable[[list[ToolInvocation], str, str], tuple[list[ToolResult], Any, Any]]


@dataclass(frozen=True)
class AdaptiveRepairPlannerResult:
    ok: bool
    repair_plan: list[ToolInvocation] = field(default_factory=list)
    source: str = "none"
    message: str = ""
    failure_kind: str = ""
    compiled_prompt_ids: tuple[str, ...] = tuple()
    raw_preview: str = ""
    repair_context: RepairContext | None = None

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_72_55.adaptive_repair_planner_result.v1",
            "ok": self.ok,
            "source": _safe(self.source, 100),
            "message": _safe(self.message, 600),
            "failure_kind": _safe(self.failure_kind, 120),
            "compiled_prompt_ids": list(self.compiled_prompt_ids),
            "raw_preview": _safe(self.raw_preview, 600),
            "repair_step_count": len(self.repair_plan),
            "repair_plan": plan_to_public_dict(self.repair_plan),
            "repair_context": self.repair_context.public_dict() if self.repair_context is not None else None,
        }


@dataclass(frozen=True)
class AdaptiveWorkLoopResult:
    attempted: bool
    original_failed: bool
    repair_attempted: bool
    repair_executed: bool
    repair_succeeded: bool
    status: str
    failure_kind: str
    next_action: str
    user_visible_summary: str
    repair_context: RepairContext
    original_plan: list[ToolInvocation] = field(default_factory=list)
    repair_plan: list[ToolInvocation] = field(default_factory=list)
    repair_results: list[ToolResult] = field(default_factory=list)
    repair_execution_report: Any | None = None
    repair_chain_summary: Any | None = None
    quality_status: str = ""
    retry_budget_used: int = 0
    retry_budget_max: int = 1
    compiled_prompt_ids: tuple[str, ...] = tuple()
    repair_source: str = ""
    planner_result: AdaptiveRepairPlannerResult | None = None

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": ADAPTIVE_WORK_LOOP_SCHEMA,
            "attempted": self.attempted,
            "original_failed": self.original_failed,
            "repair_attempted": self.repair_attempted,
            "repair_executed": self.repair_executed,
            "repair_succeeded": self.repair_succeeded,
            "status": _safe(self.status, 120),
            "failure_kind": _safe(self.failure_kind, 120),
            "next_action": _safe(self.next_action, 240),
            "user_visible_summary": _safe(self.user_visible_summary, 900),
            "repair_context": self.repair_context.public_dict(),
            "original_plan": plan_to_public_dict(self.original_plan),
            "repair_plan": plan_to_public_dict(self.repair_plan),
            "repair_results": [_tool_result_public(item) for item in self.repair_results],
            "repair_execution_report": _public_dict(self.repair_execution_report),
            "quality_status": _safe(self.quality_status, 120),
            "retry_budget": {"used": self.retry_budget_used, "max": self.retry_budget_max},
            "compiled_prompt_ids": list(self.compiled_prompt_ids),
            "repair_source": _safe(self.repair_source, 120),
            "planner_result": self.planner_result.public_dict() if self.planner_result is not None else None,
            "storage_boundary": {
                "no_raw_prompt": True,
                "no_api_key": True,
                "summary_and_refs_only": True,
                "repair_details_channel": "workbench",
            },
        }

    def final_results(self, original_results: list[ToolResult]) -> list[ToolResult]:
        return list(original_results or []) + list(self.repair_results or [])


class AdaptiveWorkLoop:
    """一次性自适应修复控制器。"""

    def __init__(self, *, max_repair_attempts: int = 1, max_repair_steps: int = 3) -> None:
        self.max_repair_attempts = 1 if max_repair_attempts != 1 else 1
        self.max_repair_steps = max(1, min(int(max_repair_steps or 3), 3))
        self.last_result: AdaptiveWorkLoopResult | None = None

    def run_once(
        self,
        *,
        user_message: str,
        original_plan: list[ToolInvocation],
        original_results: list[ToolResult],
        original_execution_report: Any | None,
        execute_repair_plan: RepairExecutor,
        model_config: Any | None = None,
        model_client: Any | None = None,
        context_hint: str = "",
        task_id: str = "",
        run_id: str = "",
    ) -> AdaptiveWorkLoopResult:
        repair_context = normalize_execution_observation(
            user_goal=user_message,
            results=original_results,
            planner_report=original_execution_report,
            original_plan=original_plan,
            retry_budget_used=0,
            retry_budget_max=self.max_repair_attempts,
        )
        if not repair_context.failed:
            result = AdaptiveWorkLoopResult(
                attempted=False,
                original_failed=False,
                repair_attempted=False,
                repair_executed=False,
                repair_succeeded=False,
                status="completed_pass",
                failure_kind="",
                next_action="final_report",
                user_visible_summary="原计划已完成，无需自适应修复。",
                repair_context=repair_context,
                original_plan=original_plan,
                quality_status=repair_context.quality_decision,
                retry_budget_used=0,
                retry_budget_max=self.max_repair_attempts,
            )
            self.last_result = result
            return result
        if repair_context.terminal:
            status = "blocked_A5" if repair_context.primary_failure_type in {"risk_blocked", "blocked_A5", "a5_blocked"} else "awaiting_confirmation"
            result = self._non_repaired_result(
                repair_context,
                original_plan,
                status=status,
                failure_kind=repair_context.primary_failure_type,
                next_action="await_user_confirmation" if status == "awaiting_confirmation" else "blocked_by_a5",
                summary="原计划命中终止类风险或确认边界，L6.72.55 不进入自动修复。",
            )
            self.last_result = result
            return result
        if not repair_context.can_auto_repair:
            result = self._non_repaired_result(
                repair_context,
                original_plan,
                status="failed_recoverable",
                failure_kind=repair_context.primary_failure_type,
                next_action=repair_context.next_action or "manual_resume",
                summary="原计划失败，但当前失败不适合自动改动；已生成可续接 repair_context。",
            )
            self.last_result = result
            return result

        planner_result = self.build_repair_plan(
            repair_context,
            model_config=model_config,
            model_client=model_client,
            context_hint=context_hint,
        )
        if not planner_result.ok or not planner_result.repair_plan:
            result = AdaptiveWorkLoopResult(
                attempted=True,
                original_failed=True,
                repair_attempted=True,
                repair_executed=False,
                repair_succeeded=False,
                status="partial_with_resume",
                failure_kind=planner_result.failure_kind or repair_context.primary_failure_type,
                next_action="resume_from_repair_context",
                user_visible_summary="原计划失败；自动修复计划未能安全生成，已转为可续接状态。",
                repair_context=repair_context,
                original_plan=original_plan,
                quality_status=repair_context.quality_decision,
                retry_budget_used=1,
                retry_budget_max=self.max_repair_attempts,
                compiled_prompt_ids=planner_result.compiled_prompt_ids,
                repair_source=planner_result.source,
                planner_result=planner_result,
            )
            self.last_result = result
            return result

        repair_results, repair_chain_summary, repair_execution_report = execute_repair_plan(
            planner_result.repair_plan,
            task_id or "runtime_text",
            f"{run_id or 'run'}_adaptive_repair",
        )
        repair_failed = any(not item.ok for item in repair_results or [])
        repair_succeeded = bool(repair_results) and not repair_failed
        has_validation = any(item.tool_name == "run_python_quality_check" for item in repair_results or [])
        status = "completed_pass" if repair_succeeded and has_validation else ("completed_with_warnings" if repair_succeeded else "partial_with_resume")
        failure_kind = "" if status == "completed_pass" else ("recovered_with_warnings" if status == "completed_with_warnings" else repair_context.primary_failure_type)
        next_action = "final_report" if repair_succeeded else "resume_from_repair_context"
        summary = (
            "原计划失败后，L6.72.55 已执行一次自适应修复并复检通过。"
            if status == "completed_pass"
            else "原计划失败后，L6.72.55 已执行一次自适应修复；修复仍未完全通过，已保留可续接状态。"
            if not repair_succeeded
            else "原计划失败后，L6.72.55 已执行一次自适应修复；结果完成但需要查看质量门警告。"
        )
        result = AdaptiveWorkLoopResult(
            attempted=True,
            original_failed=True,
            repair_attempted=True,
            repair_executed=True,
            repair_succeeded=repair_succeeded,
            status=status,
            failure_kind=failure_kind,
            next_action=next_action,
            user_visible_summary=summary,
            repair_context=repair_context,
            original_plan=original_plan,
            repair_plan=planner_result.repair_plan,
            repair_results=list(repair_results or []),
            repair_execution_report=repair_execution_report,
            repair_chain_summary=repair_chain_summary,
            quality_status=str(getattr(repair_execution_report, "status", "") or repair_context.quality_decision),
            retry_budget_used=1,
            retry_budget_max=self.max_repair_attempts,
            compiled_prompt_ids=planner_result.compiled_prompt_ids,
            repair_source=planner_result.source,
            planner_result=planner_result,
        )
        self.last_result = result
        return result

    def build_repair_plan(
        self,
        repair_context: RepairContext,
        *,
        model_config: Any | None = None,
        model_client: Any | None = None,
        context_hint: str = "",
    ) -> AdaptiveRepairPlannerResult:
        model_result: AdaptiveRepairPlannerResult | None = None
        if model_client is not None and model_config is not None:
            model_result = self._build_model_repair_plan(
                repair_context,
                model_config=model_config,
                model_client=model_client,
                context_hint=context_hint,
            )
            if model_result.ok and model_result.repair_plan:
                return model_result
        deterministic_plan = self._build_deterministic_repair_plan(repair_context)
        if deterministic_plan:
            compiled_ids = model_result.compiled_prompt_ids if model_result is not None else tuple()
            return AdaptiveRepairPlannerResult(
                ok=True,
                repair_plan=deterministic_plan[: self.max_repair_steps],
                source="deterministic_repair_after_model" if model_result is not None else "deterministic_repair",
                message="根据质量检查错误摘要生成最小确定性修复计划。",
                compiled_prompt_ids=compiled_ids,
                repair_context=repair_context,
            )
        if model_result is not None:
            return model_result
        return AdaptiveRepairPlannerResult(
            ok=False,
            source="model_not_available",
            message="未配置可用 Provider，且没有确定性 repair plan。",
            failure_kind="model_required_for_repair",
            repair_context=repair_context,
        )

    def _build_model_repair_plan(
        self,
        repair_context: RepairContext,
        *,
        model_config: Any,
        model_client: Any,
        context_hint: str = "",
    ) -> AdaptiveRepairPlannerResult:
        try:
            context = build_prompt_context(
                model_config,
                task_mode="work_task",
                output_contract="execution_report",
                runtime_state=RuntimeState(tools_available=True, available_tool_count=0, last_error_summary=repair_context.summary[:500]),
                runtime_material_cards=(repair_context.prompt_card(), context_hint[:1800]),
            )
            envelope = compile_prompt_envelope(
                context,
                [
                    {
                        "role": "user",
                        "content": (
                            "请基于 AdaptiveRepairContext 生成一次性 repair plan。"
                            "必须 JSON-only，最多 3 步，不能解释，不能输出 Markdown。"
                        ),
                    }
                ],
                phase=REPAIR_PHASE,
                metadata={"contract": ADAPTIVE_WORK_LOOP_SCHEMA, "max_repair_steps": self.max_repair_steps},
            )
            response = model_client.chat(envelope, model_config)
            raw = str(getattr(response, "content", "") or "")
            payload = parse_plan_json(raw)
            plan = validate_and_build_plan(payload, max_steps=self.max_repair_steps)
            if not plan:
                return AdaptiveRepairPlannerResult(
                    ok=False,
                    source="model_repair_plan",
                    message="模型 repair plan 为空。",
                    failure_kind="repair_plan_empty",
                    compiled_prompt_ids=(envelope.compiled_prompt_id,),
                    raw_preview=raw[:800],
                    repair_context=repair_context,
                )
            return AdaptiveRepairPlannerResult(
                ok=True,
                repair_plan=plan[: self.max_repair_steps],
                source="model_repair_plan",
                message="模型已通过 PromptIntegrator 生成一次性 repair plan。",
                compiled_prompt_ids=(envelope.compiled_prompt_id,),
                raw_preview=raw[:800],
                repair_context=repair_context,
            )
        except (PlanValidationError, ValueError, TypeError, json.JSONDecodeError) as exc:
            return AdaptiveRepairPlannerResult(
                ok=False,
                source="model_repair_plan",
                message=f"repair plan schema invalid: {type(exc).__name__}: {exc}",
                failure_kind="repair_plan_invalid",
                repair_context=repair_context,
            )
        except Exception as exc:  # noqa: BLE001
            return AdaptiveRepairPlannerResult(
                ok=False,
                source="model_repair_plan",
                message=f"repair planner failed: {type(exc).__name__}: {exc}",
                failure_kind="repair_planner_error",
                repair_context=repair_context,
            )

    def _build_deterministic_repair_plan(self, repair_context: RepairContext) -> list[ToolInvocation]:
        for failure in repair_context.failures:
            lower = failure.output_summary.lower()
            if failure.tool_name == "run_python_quality_check" and ("syntaxerror: expected ':'" in lower or "expected ':'" in lower):
                item = _compileall_expected_colon_repair(failure.output_summary)
                if item is not None:
                    path, old_line, new_line = item
                    return [
                        ToolInvocation(
                            "document_apply_rewrite",
                            {
                                "path": path,
                                "old_text": old_line,
                                "new_text": new_line,
                                "operation": "replace",
                                "overwrite": True,
                                "allow_no_match": False,
                            },
                            reason="L6.72.55 自动修复 compileall 报告的缺失冒号。",
                        ),
                        ToolInvocation(
                            "run_python_quality_check",
                            {"command": "compileall", "target": path},
                            reason="复跑 compileall 验证一次性修复结果。",
                        ),
                    ]
        return []

    def _non_repaired_result(
        self,
        repair_context: RepairContext,
        original_plan: list[ToolInvocation],
        *,
        status: str,
        failure_kind: str,
        next_action: str,
        summary: str,
    ) -> AdaptiveWorkLoopResult:
        return AdaptiveWorkLoopResult(
            attempted=True,
            original_failed=True,
            repair_attempted=False,
            repair_executed=False,
            repair_succeeded=False,
            status=status,
            failure_kind=failure_kind,
            next_action=next_action,
            user_visible_summary=summary,
            repair_context=repair_context,
            original_plan=original_plan,
            quality_status=repair_context.quality_decision,
            retry_budget_used=0,
            retry_budget_max=self.max_repair_attempts,
        )


def _compileall_expected_colon_repair(summary: str) -> tuple[str, str, str] | None:
    text = str(summary or "")
    py_paths = re.findall(r'File "([^"]+\.py)"', text)
    path = py_paths[-1] if py_paths else ""
    # compileall 输出在 SyntaxError 前通常包含源码行和 ^ 指示线；只取最近的非空源码行。
    before = text.split("SyntaxError: expected ':'", 1)[0]
    candidates: list[str] = []
    for line in before.splitlines():
        stripped = line.rstrip("\n")
        if not stripped.strip():
            continue
        if stripped.lstrip().startswith(("File ", "***", "Listing ", "Compiling ", "^")):
            continue
        if stripped.strip().startswith("^"):
            continue
        candidates.append(stripped)
    if not path or not candidates:
        return None
    old_line = candidates[-1].strip()
    if old_line.endswith(":"):
        return None
    new_line = old_line + ":  # linyuanzhe_l67255_repair"
    try:
        p = Path(path)
        path = p.name if p.is_absolute() else str(p)
    except Exception:  # noqa: BLE001
        pass
    return path, old_line, new_line


def _tool_result_public(result: ToolResult) -> dict[str, Any]:
    status = getattr(result, "status", "")
    return {
        "step_id": _safe(getattr(result, "step_id", ""), 120),
        "tool_name": _safe(getattr(result, "tool_name", ""), 120),
        "status": _safe(getattr(status, "value", status), 80),
        "output_summary": _safe(getattr(result, "output_summary", ""), 600),
        "artifacts": [_safe(item, 500) for item in (getattr(result, "artifacts", []) or [])[:20]],
        "error_code": _safe(getattr(result, "error_code", ""), 120),
        "audit_ref": _safe(getattr(result, "audit_ref", ""), 120),
    }


def _public_dict(value: Any) -> Any:
    if value is None:
        return None
    try:
        if hasattr(value, "public_dict"):
            return value.public_dict()
    except Exception:  # noqa: BLE001
        return None
    return None


def _safe(value: Any, limit: int) -> str:
    return redact_text(str(value or "").replace("\x00", ""))[: max(1, int(limit))]
