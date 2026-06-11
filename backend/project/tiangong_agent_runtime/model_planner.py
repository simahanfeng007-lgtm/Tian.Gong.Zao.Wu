"""L6.72.51 提示词整合器中转模型计划器。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from tiangong_agent_shell.errors import AgentShellError
from tiangong_agent_shell.prompt_compiler import build_prompt_context, compile_prompt_envelope
from tiangong_agent_shell.safe_logging import redact_text

from .activation_protocol import (
    ActivationForm,
    activation_execution_card,
    activation_failure_message,
    activation_schema_card,
    parse_activation_form,
)
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
    activation_form: ActivationForm | None = None
    compiled_prompt_ids: tuple[str, ...] = tuple()
    failure_kind: str = ""
    provider_status: str = ""
    repair_attempted: bool = False
    repair_stage: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "source": self.source,
            "message": self.message,
            "activation_form": self.activation_form.public_dict() if self.activation_form else None,
            "compiled_prompt_ids": list(self.compiled_prompt_ids),
            "failure_kind": self.failure_kind,
            "provider_status": self.provider_status,
            "repair_attempted": self.repair_attempted,
            "repair_stage": self.repair_stage,
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

    L6.72.51 关键边界：Planner 不能绕过 PromptCompiler 直接拼 messages
    调模型。每轮必须先经过 ActivationForm 决策，再由 PromptCompiler 整合
    执行阶段完整上下文，最后才让 LLM 输出 JSON plan。
    """

    def build_plan(
        self,
        user_message: str,
        *,
        model_config: Any,
        model_client: Any,
        max_steps: int = 80,
        context_hint: str = "",
        activation_form: dict[str, Any] | None = None,
        active_model_policy: Any | None = None,
    ) -> ModelPlannerResult:
        policy_max_steps = max(1, int(getattr(active_model_policy, "effective_max_steps", max_steps) or max_steps))
        prompt_contract = str(getattr(active_model_policy, "prompt_contract", "strict_json") or "strict_json")
        if model_client is None or model_config is None:
            return ModelPlannerResult(False, message="模型计划器缺少 model_client/model_config。", failure_kind="provider_not_ready", provider_status="provider_not_ready")

        # 离线兼容回放专用：只验证旧 plan shape 兼容性，不代表真实执行链。
        if str(getattr(model_client, "provider", "")) == "deepseek-sample-replay":
            return self._build_legacy_replay_plan(user_message, model_config=model_config, model_client=model_client, max_steps=policy_max_steps)

        api_key = str(getattr(model_config, "api_key", "") or "")
        compiled_ids: list[str] = []

        if activation_form is not None:
            try:
                # Runtime 已经通过 PromptIntegrator 中转拿到 LLM 填写的 ActivationForm；
                # Planner 只复校验字段，不能再次替 LLM 重判模式。
                activation_form = parse_activation_form(__import__("json").dumps(dict(activation_form), ensure_ascii=False))
            except Exception as exc:  # noqa: BLE001
                return ModelPlannerResult(False, message=activation_failure_message(exc), raw_preview=str(exc)[:500], failure_kind="activation_invalid")
        else:
            activation_envelope = _build_activation_envelope(user_message, model_config=model_config, context_hint=context_hint)
            compiled_ids.append(activation_envelope.compiled_prompt_id)
            try:
                activation_result = model_client.chat(activation_envelope, model_config)
                activation_raw = str(getattr(activation_result, "content", "") or "")
                activation_form = parse_activation_form(activation_raw)
            except AgentShellError as exc:
                status = _provider_status_from_error(exc)
                return ModelPlannerResult(
                    False,
                    message=redact_text(exc.user_message, [api_key]),
                    raw_preview=redact_text(exc.detail, [api_key])[:500],
                    compiled_prompt_ids=tuple(compiled_ids),
                    failure_kind=_provider_failure_kind(status),
                    provider_status=status,
                )
            except Exception as exc:  # noqa: BLE001 - boundary must convert model/parse failures
                return ModelPlannerResult(
                    False,
                    message=activation_failure_message(exc),
                    raw_preview=str(exc)[:500],
                    compiled_prompt_ids=tuple(compiled_ids),
                    failure_kind="activation_failed",
                )

        if activation_form.mode != "work" or not activation_form.tools_requested:
            return ModelPlannerResult(
                False,
                message="LLM ActivationForm 裁决为 chat 或不需要工具；Runtime 未激活工具链。",
                activation_form=activation_form,
                compiled_prompt_ids=tuple(compiled_ids),
                failure_kind="activation_chat_or_no_tools",
            )
        if activation_form.risk_level == "A5" or activation_form.need_user_confirm:
            return ModelPlannerResult(
                False,
                message="LLM ActivationForm 标记为 A5 或需要用户确认；Runtime 未自动执行。",
                activation_form=activation_form,
                compiled_prompt_ids=tuple(compiled_ids),
                failure_kind="a5_blocked" if activation_form.risk_level == "A5" else "confirmation_required",
            )

        execution_envelope = _build_execution_plan_envelope(
            user_message,
            activation_form=activation_form,
            model_config=model_config,
            max_steps=policy_max_steps,
            context_hint=context_hint,
            prompt_contract=prompt_contract,
        )
        context_retry_attempted = False
        context_retry_stage = ""
        compiled_ids.append(execution_envelope.compiled_prompt_id)
        try:
            chat_result = model_client.chat(execution_envelope, model_config)
        except AgentShellError as exc:
            if _is_context_overflow_error(exc):
                retry_context_hint = _compact_context_hint(context_hint)
                retry_envelope = _build_execution_plan_envelope(
                    user_message,
                    activation_form=activation_form,
                    model_config=model_config,
                    max_steps=max(1, min(policy_max_steps, 3)),
                    context_hint=retry_context_hint,
                    phase="planner_execution_context_retry",
                    prompt_contract="choice_or_short_json",
                )
                compiled_ids.append(retry_envelope.compiled_prompt_id)
                try:
                    chat_result = model_client.chat(retry_envelope, model_config)
                    context_retry_attempted = True
                    context_retry_stage = "context_overflow_compact_retry"
                except AgentShellError as retry_exc:
                    return ModelPlannerResult(
                        False,
                        message=redact_text(retry_exc.user_message, [api_key]),
                        raw_preview=redact_text(retry_exc.detail, [api_key])[:500],
                        activation_form=activation_form,
                        compiled_prompt_ids=tuple(compiled_ids),
                        failure_kind="context_overflow",
                        provider_status="context_overflow",
                        repair_attempted=True,
                        repair_stage="context_overflow_compact_retry",
                    )
                except Exception as retry_exc:  # noqa: BLE001
                    return ModelPlannerResult(
                        False,
                        message=f"模型计划器上下文压缩重试失败：{type(retry_exc).__name__}。",
                        activation_form=activation_form,
                        compiled_prompt_ids=tuple(compiled_ids),
                        failure_kind="context_overflow",
                        provider_status="context_overflow",
                        repair_attempted=True,
                        repair_stage="context_overflow_compact_retry",
                    )
            else:
                status = _provider_status_from_error(exc)
                return ModelPlannerResult(
                    False,
                    message=redact_text(exc.user_message, [api_key]),
                    raw_preview=redact_text(exc.detail, [api_key])[:500],
                    activation_form=activation_form,
                    compiled_prompt_ids=tuple(compiled_ids),
                    failure_kind=_provider_failure_kind(status),
                    provider_status=status,
                )
        except Exception as exc:  # noqa: BLE001
            if _is_context_overflow_text(str(exc)):
                retry_context_hint = _compact_context_hint(context_hint)
                retry_envelope = _build_execution_plan_envelope(
                    user_message,
                    activation_form=activation_form,
                    model_config=model_config,
                    max_steps=max(1, min(policy_max_steps, 3)),
                    context_hint=retry_context_hint,
                    phase="planner_execution_context_retry",
                    prompt_contract="choice_or_short_json",
                )
                compiled_ids.append(retry_envelope.compiled_prompt_id)
                try:
                    chat_result = model_client.chat(retry_envelope, model_config)
                    context_retry_attempted = True
                    context_retry_stage = "context_overflow_compact_retry"
                except Exception as retry_exc:  # noqa: BLE001
                    return ModelPlannerResult(
                        False,
                        message=f"模型计划器上下文压缩重试失败：{type(retry_exc).__name__}。",
                        activation_form=activation_form,
                        compiled_prompt_ids=tuple(compiled_ids),
                        failure_kind="context_overflow",
                        provider_status="context_overflow",
                        repair_attempted=True,
                        repair_stage="context_overflow_compact_retry",
                    )
            else:
                return ModelPlannerResult(
                    False,
                    message=f"模型计划器调用失败：{type(exc).__name__}。",
                    activation_form=activation_form,
                    compiled_prompt_ids=tuple(compiled_ids),
                    failure_kind="provider_error",
                    provider_status="provider_error",
                )

        raw = str(getattr(chat_result, "content", "") or "")
        try:
            payload = parse_plan_json(raw)
        except PlanValidationError as exc:
            if raw.strip() and any(issue.code == "invalid_json" for issue in exc.issues):
                repair = self._try_plan_repair(
                    user_message,
                    raw=raw,
                    issues=list(exc.issues),
                    model_config=model_config,
                    model_client=model_client,
                    max_steps=policy_max_steps,
                    context_hint=context_hint,
                    prompt_contract=prompt_contract,
                    activation_form=activation_form,
                    compiled_ids=compiled_ids,
                    api_key=api_key,
                )
                if repair.ok:
                    return repair
                if _can_virtualize_validation_failure(exc.issues, raw):
                    try:
                        payload = build_virtual_return_payload(user_message, raw)
                    except Exception:  # noqa: BLE001
                        return repair
                else:
                    return repair
            else:
                return ModelPlannerResult(
                    False,
                    message="模型计划未通过安全校验。",
                    issues=list(exc.issues),
                    raw_preview=raw[:500],
                    activation_form=activation_form,
                    compiled_prompt_ids=tuple(compiled_ids),
                    failure_kind="plan_schema_invalid",
                )
        try:
            plan = validate_and_build_plan(payload, max_steps=policy_max_steps)
        except PlanValidationError as exc:
            if _can_virtualize_validation_failure(exc.issues, raw):
                try:
                    fallback_payload = build_virtual_return_payload(user_message, raw)
                    plan = validate_and_build_plan(fallback_payload, max_steps=policy_max_steps)
                except PlanValidationError as fallback_exc:
                    return ModelPlannerResult(
                        False,
                        message=_format_plan_failure_message(fallback_exc.issues),
                        issues=list(fallback_exc.issues),
                        raw_preview=raw[:500],
                        activation_form=activation_form,
                        compiled_prompt_ids=tuple(compiled_ids),
                        failure_kind="plan_repair_failed",
                    )
                return ModelPlannerResult(
                    True,
                    plan=plan,
                    message=f"ActivationForm 已激活；模型输出非标准 plan，已归一为审计型虚拟返回：{len(plan)} steps。",
                    raw_preview=raw[:500],
                    activation_form=activation_form,
                    compiled_prompt_ids=tuple(compiled_ids),
                    repair_attempted=context_retry_attempted,
                    repair_stage=context_retry_stage,
                )
            return ModelPlannerResult(
                False,
                message=_format_plan_failure_message(exc.issues),
                issues=list(exc.issues),
                raw_preview=raw[:500],
                activation_form=activation_form,
                compiled_prompt_ids=tuple(compiled_ids),
                failure_kind="plan_schema_invalid",
            )
        return ModelPlannerResult(
            True,
            plan=plan,
            message=f"ActivationForm 已激活；模型计划生成成功：{len(plan)} steps。",
            raw_preview=raw[:500],
            activation_form=activation_form,
            compiled_prompt_ids=tuple(compiled_ids),
            repair_attempted=context_retry_attempted,
            repair_stage=context_retry_stage,
        )

    def _try_plan_repair(
        self,
        user_message: str,
        *,
        raw: str,
        issues: list[PlanValidationIssue],
        model_config: Any,
        model_client: Any,
        max_steps: int,
        context_hint: str,
        prompt_contract: str,
        activation_form: ActivationForm,
        compiled_ids: list[str],
        api_key: str,
    ) -> ModelPlannerResult:
        repair_envelope = _build_plan_repair_envelope(
            user_message,
            activation_form=activation_form,
            model_config=model_config,
            max_steps=max_steps,
            context_hint=context_hint,
            prompt_contract=prompt_contract,
            raw_preview=raw[:900],
            issues=issues,
        )
        repair_ids = list(compiled_ids) + [repair_envelope.compiled_prompt_id]
        try:
            repair_result = model_client.chat(repair_envelope, model_config)
            repair_raw = str(getattr(repair_result, "content", "") or "")
            repair_payload = parse_plan_json(repair_raw)
            repair_plan = validate_and_build_plan(repair_payload, max_steps=max(1, min(max_steps, 6)))
            return ModelPlannerResult(
                True,
                plan=repair_plan,
                message=f"plan_repair 成功：模型计划 JSON 已经通过短 schema 修复，{len(repair_plan)} steps。",
                raw_preview=repair_raw[:500],
                activation_form=activation_form,
                compiled_prompt_ids=tuple(repair_ids),
                failure_kind="",
                repair_attempted=True,
                repair_stage="short_json",
            )
        except AgentShellError as exc:
            status = _provider_status_from_error(exc)
            return ModelPlannerResult(
                False,
                message=redact_text(exc.user_message, [api_key]),
                issues=list(issues),
                raw_preview=redact_text(exc.detail, [api_key])[:500],
                activation_form=activation_form,
                compiled_prompt_ids=tuple(repair_ids),
                failure_kind="plan_repair_failed",
                provider_status=status,
                repair_attempted=True,
                repair_stage="short_json",
            )
        except Exception as exc:  # noqa: BLE001
            return ModelPlannerResult(
                False,
                message=f"plan_repair 失败：{type(exc).__name__}。",
                issues=list(issues),
                raw_preview=str(raw or "")[:500],
                activation_form=activation_form,
                compiled_prompt_ids=tuple(repair_ids),
                failure_kind="plan_repair_failed",
                repair_attempted=True,
                repair_stage="short_json",
            )

    def _build_legacy_replay_plan(self, user_message: str, *, model_config: Any, model_client: Any, max_steps: int) -> ModelPlannerResult:
        """保留 DeepSeek plan shape 兼容回放，不进入真实工作链。"""
        try:
            from tiangong_agent_shell.model_client_port import CompiledPromptEnvelope
            prompt = CompiledPromptEnvelope(
                messages=({"role": "system", "content": "sample replay"}, {"role": "user", "content": user_message}),
                compiled_prompt_id="cp_sample_replay",
                phase="planner_replay",
                metadata={"replay": True},
            )
            chat_result = model_client.chat(prompt, model_config)
        except Exception as exc:  # noqa: BLE001
            return ModelPlannerResult(False, message=f"模型计划器回放失败：{type(exc).__name__}。")
        raw = str(getattr(chat_result, "content", "") or "")
        try:
            payload = parse_plan_json(raw)
        except PlanValidationError as exc:
            if raw.strip() and any(issue.code == "invalid_json" for issue in exc.issues):
                try:
                    payload = build_virtual_return_payload(user_message, raw)
                except Exception:  # noqa: BLE001
                    return ModelPlannerResult(False, message=_format_plan_failure_message(exc.issues), issues=list(exc.issues), raw_preview=raw[:500])
            else:
                return ModelPlannerResult(False, message=_format_plan_failure_message(exc.issues), issues=list(exc.issues), raw_preview=raw[:500])
        try:
            plan = validate_and_build_plan(payload, max_steps=max_steps)
            return ModelPlannerResult(True, plan=plan, message=f"兼容回放通过：{len(plan)} steps。", raw_preview=raw[:500])
        except PlanValidationError as exc:
            return ModelPlannerResult(False, message=_format_plan_failure_message(exc.issues), issues=list(exc.issues), raw_preview=raw[:500])


def _build_activation_envelope(user_message: str, *, model_config: Any, context_hint: str = ""):
    card = activation_schema_card(user_selected_mode="work", context_hint=context_hint)
    prompt_context = build_prompt_context(
        model_config,
        task_mode="tool_task",
        output_contract="activation_form",
        extra_cards=(card,),
    )
    user = "\n".join([
        "请只填写本轮 ActivationForm JSON。",
        "不要执行任务，不要解释，不要输出 Markdown。",
        f"用户请求：{user_message}",
    ])
    return compile_prompt_envelope(
        prompt_context,
        [{"role": "user", "content": user}],
        phase="activation_decision",
        metadata={"runtime_material": "ActivationFormSpec", "planner": "ModelPlanner", "schema": "L6.72.51"},
    )


def _build_execution_plan_envelope(user_message: str, *, activation_form: ActivationForm, model_config: Any, max_steps: int, context_hint: str = "", phase: str = "planner_execution", prompt_contract: str = "strict_json"):
    contract_lines = _prompt_contract_lines(prompt_contract, max_steps)
    execution_card = "\n".join([
        activation_execution_card(activation_form, context_hint=context_hint),
        "[ExecutionPlanSchema / 工具计划 JSON schema]",
        "你现在必须输出 JSON plan，不能输出自然语言解释。",
        "代码、补丁、Shell/命令应作为工具参数进入 Runtime，而不是被普通聊天吞掉。",
        "A0-A4 默认进入 Runtime 审计链；A5 必须阻断。",
        "读取普通文本/代码优先 read_file；创建/写入文件用 write_workspace_file；目录列表用 list_dir；质量验证用 run_python_quality_check；交付包用 create_zip_package。",
        "只有明确文档解析、总结、排版、导出任务才使用 document_parse/document_query/document_rewrite_plan/document_apply_rewrite。",
        f"建议输出不超过 {max_steps} 个步骤；长链任务可分批续接。",
        *contract_lines,
        "可用 schema：",
        planner_schema_prompt(),
    ])
    prompt_context = build_prompt_context(
        model_config,
        task_mode="tool_task",
        output_contract="json_only",
        extra_cards=(execution_card,),
    )
    user = f"任务：{user_message}\n请根据 ActivationForm 输出 JSON plan。"
    return compile_prompt_envelope(
        prompt_context,
        [{"role": "user", "content": user}],
        phase=phase,
        metadata={"runtime_material": "ExecutionPlanSchema", "planner": "ModelPlanner", "activation": activation_form.public_dict(), "context_window_retry": phase.endswith("context_retry")},
    )


def _build_plan_repair_envelope(
    user_message: str,
    *,
    activation_form: ActivationForm,
    model_config: Any,
    max_steps: int,
    context_hint: str = "",
    prompt_contract: str = "short_json",
    raw_preview: str = "",
    issues: list[PlanValidationIssue] | None = None,
):
    issue_codes = ", ".join(sorted({issue.code for issue in (issues or [])})) or "invalid_json"
    repair_card = "\n".join([
        activation_execution_card(activation_form, context_hint=context_hint),
        "[PlannerRequest / plan_repair / short_json]",
        "上一次模型计划不是合法 JSON。现在只允许输出可解析 JSON，不要 Markdown，不要解释。",
        "输出必须形如：{\"steps\":[{\"tool_name\":\"list_dir\",\"arguments\":{\"path\":\".\"},\"reason\":\"...\"}]}",
        f"最多 {max(1, min(max_steps, 6))} 个 steps。",
        *_prompt_contract_lines(prompt_contract, max_steps),
        f"上次错误码：{issue_codes}",
        "可用 schema：",
        planner_schema_prompt(),
    ])
    prompt_context = build_prompt_context(
        model_config,
        task_mode="tool_task",
        output_contract="json_only",
        extra_cards=(repair_card,),
    )
    user = "\n".join([
        f"任务：{user_message}",
        "请把上一轮输出修复为合法 JSON plan。",
        "上一轮输出摘要：",
        str(raw_preview or "")[:900],
    ])
    return compile_prompt_envelope(
        prompt_context,
        [{"role": "user", "content": user}],
        phase="planner_repair",
        metadata={"runtime_material": "ExecutionPlanRepairSchema", "planner": "ModelPlanner", "repair_stage": "short_json", "activation": activation_form.public_dict()},
    )



def _provider_status_from_error(exc: AgentShellError) -> str:
    kind = str(getattr(exc, "error_kind", "") or "").strip().lower()
    if kind:
        return kind
    if _is_context_overflow_error(exc):
        return "context_overflow"
    return "provider_error"


def _provider_failure_kind(status: str) -> str:
    if status in {"auth_error", "model_not_found", "rate_limited", "timeout", "server_error", "unsupported_feature", "refusal"}:
        return "provider_" + status
    if status == "context_overflow":
        return "context_overflow"
    if status == "invalid_json":
        return "provider_invalid_json"
    return "provider_error"


def _prompt_contract_lines(prompt_contract: str, max_steps: int) -> list[str]:
    contract = str(prompt_contract or "strict_json").strip().lower()
    if contract == "choice_or_short_json":
        return [
            "prompt_contract=choice_or_short_json：只允许 1-3 步微计划；优先从候选工具里选择，不生成复杂工具链。",
            f"本轮硬上限 {max(1, min(max_steps, 3))} steps；无法完成时输出可续接的下一步，而不是假装完成。",
        ]
    if contract == "short_json":
        return [
            "prompt_contract=short_json：输出最短合法 JSON；每步只保留 tool_name/arguments/reason。",
            f"本轮硬上限 {max(1, min(max_steps, 8))} steps；长链必须分轮续接。",
        ]
    if contract == "disabled":
        return ["prompt_contract=disabled：当前模型策略不允许进入工作模式。"]
    return ["prompt_contract=strict_json：必须输出完整合法 JSON plan，不允许 Markdown 或解释。"]


def _is_context_overflow_error(exc: AgentShellError) -> bool:
    return _is_context_overflow_text(f"{getattr(exc, 'user_message', '')} {getattr(exc, 'detail', '')}")


def _is_context_overflow_text(text: str) -> bool:
    lowered = str(text or "").lower()
    return any(token in lowered for token in ("context_overflow", "context length", "maximum context", "too many tokens", "token limit", "上下文", "超出上下文"))


def _compact_context_hint(context_hint: str, *, max_chars: int = 1800) -> str:
    text = redact_text(str(context_hint or ""))
    if len(text) <= max_chars:
        return "[ContextWindowManager compact_retry]\n" + text
    head = text[:700]
    tail = text[-900:]
    return (
        "[ContextWindowManager compact_retry / provider_context_overflow]\n"
        "已因 Provider context_overflow 压缩上下文；保留 mission/state/error/tool/constraint，舍弃长 evidence。\n"
        + head
        + "\n[...context_window_compacted...]\n"
        + tail
    )[:max_chars]

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
