"""L6.14 模型驱动计划生成器。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tiangong_agent_shell.errors import AgentShellError
from tiangong_agent_shell.safe_logging import redact_text

from .plan_schema import (
    PlanValidationError,
    PlanValidationIssue,
    build_virtual_return_payload,
    parse_plan_json,
    planner_schema_prompt,
    validate_and_build_plan,
)
from .tool_invocation import ToolInvocation


@dataclass(frozen=True)
class ModelPlannerResult:
    ok: bool
    plan: list[ToolInvocation] = field(default_factory=list)
    source: str = "model_planner"
    message: str = ""
    issues: list[PlanValidationIssue] = field(default_factory=list)
    raw_preview: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source": self.source,
            "message": self.message,
            "steps": [
                {
                    "step_id": step.step_id,
                    "tool_name": step.tool_name,
                    "arguments": dict(step.arguments),
                    "reason": step.reason,
                }
                for step in self.plan
            ],
            "issues": [issue.__dict__ for issue in self.issues],
            "raw_preview": self.raw_preview[:500],
        }


class ModelPlanner:
    """把自然语言任务转成结构化工具计划。

    模型只产出 JSON 计划；计划必须经 plan_schema 校验后才会进入执行链。
    """

    def build_plan(
        self,
        user_message: str,
        *,
        model_config: Any,
        model_client: Any,
        max_steps: int = 20,
        context_hint: str = "",
    ) -> ModelPlannerResult:
        if model_client is None or model_config is None:
            return ModelPlannerResult(False, message="模型计划器缺少 model_client/model_config。")
        messages = _build_planner_messages(user_message, max_steps=max_steps, context_hint=context_hint)
        api_key = str(getattr(model_config, "api_key", "") or "")
        try:
            chat_result = model_client.chat(messages, model_config)
        except AgentShellError as exc:
            return ModelPlannerResult(
                False,
                message=redact_text(exc.user_message, [api_key]),
                raw_preview=redact_text(exc.detail, [api_key])[:500],
            )
        except Exception as exc:  # noqa: BLE001 - model planner boundary must be non-crashy
            return ModelPlannerResult(False, message=f"模型计划器调用失败：{type(exc).__name__}。")

        raw = str(getattr(chat_result, "content", "") or "")
        try:
            payload = parse_plan_json(raw)
        except PlanValidationError as exc:
            # L6.32 P1: DeepSeek/兼容模型在纯代码、纯分析任务中可能直接输出正文或代码块。
            # 不把该正文当代码执行、不写文件，只包装为 return_code/return_analysis 虚拟步骤进入审计链，
            # 避免 invalid_json 后回退普通对话造成上下文断裂。
            if raw.strip() and any(issue.code == "invalid_json" for issue in exc.issues):
                payload = build_virtual_return_payload(user_message, raw)
            else:
                return ModelPlannerResult(
                    False,
                    message="模型计划未通过安全校验。",
                    issues=list(exc.issues),
                    raw_preview=raw[:500],
                )
        try:
            plan = validate_and_build_plan(payload, max_steps=max_steps)
        except PlanValidationError as exc:
            # L6.34：有些 DeepSeek 轮次会返回 {"answer": ...} / {"analysis": ...}
            # 这类输出不是危险工具计划，只是没有 steps 外形；归一为审计型虚拟返回，
            # 仍走 plan_schema + Runtime 安全链。危险工具、绝对路径、shell 字段不走该兜底。
            if _can_virtualize_validation_failure(exc.issues, raw):
                try:
                    fallback_payload = build_virtual_return_payload(user_message, raw)
                    plan = validate_and_build_plan(fallback_payload, max_steps=max_steps)
                except PlanValidationError as fallback_exc:
                    return ModelPlannerResult(
                        False,
                        message=_format_plan_failure_message(fallback_exc.issues),
                        issues=list(fallback_exc.issues),
                        raw_preview=raw[:500],
                    )
                return ModelPlannerResult(
                    True,
                    plan=plan,
                    message=f"模型输出非标准 plan，已归一为审计型虚拟返回：{len(plan)} steps。",
                    raw_preview=raw[:500],
                )
            return ModelPlannerResult(
                False,
                message=_format_plan_failure_message(exc.issues),
                issues=list(exc.issues),
                raw_preview=raw[:500],
            )
        return ModelPlannerResult(True, plan=plan, message=f"模型计划生成成功：{len(plan)} steps。", raw_preview=raw[:500])


def _build_planner_messages(user_message: str, *, max_steps: int, context_hint: str = "") -> list[dict[str, str]]:
    system = "\n".join(
        [
            "你是天工造物 L6.14 的计划生成器，只能输出 JSON。",
            "你的任务是把用户的每一项需求都转换为 steps 数组。",
            "即使用户要的是纯代码、纯分析、纯设计，也必须包装为 plan 输出。",
            "代码类任务使用 return_code step；分析类任务使用 return_analysis step。",
            "禁止直接输出代码块，必须走 JSON plan。",
            "禁止输出解释、Markdown、代码块以外的非 JSON 文本。",
            "禁止生成任意 shell 命令；禁止生成未列出的工具；禁止生成绝对路径或 ../。",
            "模型只建议计划，不执行工具。所有步骤随后会进入本地安全治理链。",
            f"最多输出 {max_steps} 个步骤。",
            "允许 schema：",
            planner_schema_prompt(),
        ]
    )
    context_block = f"\n{context_hint}\n" if context_hint else ""
    user = f"{context_block}任务：{user_message}\n请只输出 JSON。"
    return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def _format_plan_failure_message(issues: list[PlanValidationIssue]) -> str:
    codes = sorted({issue.code for issue in issues})
    if not codes:
        return "模型计划未通过安全校验。"
    return "模型计划未通过安全校验：" + ", ".join(codes) + "。"


def _can_virtualize_validation_failure(issues: list[PlanValidationIssue], raw: str) -> bool:
    """仅对“非标准回答外形”兜底，不对危险计划放权。"""
    codes = {issue.code for issue in issues}
    if not codes:
        return False
    unsafe_codes = {
        "tool_not_allowed",
        "unsafe_path",
        "unsafe_quality_command",
        "unsafe_unknown_arguments",
        "unknown_arguments",
        "missing_required_arguments",
        "arguments_not_object",
    }
    if codes & unsafe_codes:
        return False
    if not codes <= {"invalid_plan_shape", "empty_steps", "step_not_object", "empty_tool_name"}:
        return False
    text = str(raw or "").strip()
    if not text:
        return False
    lowered = text.lower()
    dangerous_fragments = ("rm -rf", "del /", "format ", "powershell", "curl ", "wget ", "http://", "https://")
    if any(fragment in lowered for fragment in dangerous_fragments):
        return False
    return True
