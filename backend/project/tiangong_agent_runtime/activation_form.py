"""L6.72.51 ActivationForm 兼容入口。

真实协议定义在 ``activation_protocol.py``。本模块保留旧导入路径，避免
Runtime / smoke / 历史模块因为迁移过程中的 import 名称不一致而崩溃。

边界：Runtime 只生成 ActivationFormSpec 材料；PromptCompiler 统一整合；
LLM 填 ActivationForm；Runtime 只校验，不用关键词重判用户意图。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from tiangong_agent_shell.errors import AgentShellError
from tiangong_agent_shell.prompt_compiler import compile_activation_decision_prompt
from tiangong_agent_shell.safe_logging import redact_text

from .activation_protocol import ActivationForm, activation_schema_card, parse_activation_form


@dataclass(frozen=True)
class ActivationFormSpec:
    user_selected_mode: str = "chat"
    user_message_preview: str = ""
    available_tool_names: tuple[str, ...] = tuple()
    session_context_hint: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "user_selected_mode": self.user_selected_mode,
            "user_message_preview": self.user_message_preview,
            "available_tool_names": list(self.available_tool_names),
            "session_context_hint": self.session_context_hint,
        }

    def prompt_card(self) -> str:
        tool_line = ", ".join(self.available_tool_names[:120]) or "未上报"
        context_hint = self.session_context_hint
        if tool_line:
            context_hint = (context_hint + "\n" if context_hint else "") + f"available_tool_names={tool_line}"
        return activation_schema_card(user_selected_mode=self.user_selected_mode, context_hint=context_hint)


@dataclass(frozen=True)
class ActivationResult:
    ok: bool
    form: ActivationForm | None = None
    message: str = ""
    raw_preview: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "form": self.form.public_dict() if self.form else None,
            "message": self.message,
            "raw_preview": self.raw_preview[:500],
        }


class ActivationFormDecider:
    """通过 PromptCompiler 中转，让 LLM 填写 ActivationForm。"""

    @staticmethod
    def _needs_work_retry(form: ActivationForm, user_selected_mode: str) -> bool:
        return (
            str(user_selected_mode or "").strip().lower() == "work"
            and (form.mode != "work" or not form.tools_requested)
        )

    @staticmethod
    def _work_retry_hint(context_hint: str) -> str:
        strict = (
            "STRICT_ACTIVATION_RETRY: The user explicitly selected work mode. "
            "If the request asks to read/list/create/modify files, inspect a directory, "
            "run a command, test code, package, repair, verify, or otherwise complete a "
            "real local task, output mode='work' and tools_requested=true. "
            "Use mode='chat' only for pure discussion with no requested local action. "
            "Return only one valid ActivationForm JSON object."
        )
        return (str(context_hint or "").strip() + "\n" + strict).strip()

    @staticmethod
    def _looks_like_local_work(user_message: str) -> bool:
        text = str(user_message or "").lower()
        if not text.strip():
            return False
        markers = (
            "read", "list", "create", "write", "modify", "edit", "run", "test",
            "package", "repair", "fix", "verify", "inspect", "check",
            "读取", "列出", "创建", "写入", "修改", "编辑", "运行", "测试",
            "打包", "修复", "验证", "检查", "质检", "目录", "文件", "代码",
        )
        return any(marker in text for marker in markers)

    @staticmethod
    def _fallback_work_form(user_message: str) -> ActivationForm:
        text = str(user_message or "").lower()
        if any(marker in text for marker in ("代码", "code", "pytest", "test", "测试")):
            work_type = "code"
            required = ("file_read", "terminal_test")
        elif any(marker in text for marker in ("run", "运行", "命令", "打包", "package")):
            work_type = "terminal"
            required = ("terminal",)
        elif any(marker in text for marker in ("目录", "list", "列出", "read", "读取")):
            work_type = "file"
            required = ("file_read", "list_dir")
        else:
            work_type = "file"
            required = ("file_read", "file_write")
        return ActivationForm(
            mode="work",
            work_type=work_type,
            execution_depth="single_step",
            tools_requested=True,
            required_tool_classes=required,
            risk_level="A1",
            need_quality_gate=True,
            need_user_confirm=False,
            expected_result="执行用户显式工作模式请求，并返回可审计执行报告。",
            final_output_contract="execution_report",
            reason="deterministic fallback after model returned chat/no_tools for explicit work mode",
        )

    def decide(
        self,
        user_message: str,
        *,
        model_config: Any,
        model_client: Any,
        user_selected_mode: str = "work",
        max_steps: int = 80,
        context_hint: str = "",
    ) -> ActivationResult:
        if model_client is None or model_config is None:
            return ActivationResult(False, message="ActivationForm 缺少 model_client/model_config。")
        envelope = compile_activation_decision_prompt(
            user_message,
            config=model_config,
            user_selected_mode=user_selected_mode,
            context_hint=context_hint,
            max_steps=max_steps,
        )
        api_key = str(getattr(model_config, "api_key", "") or "")
        try:
            chat_result = model_client.chat(envelope, model_config)
        except AgentShellError as exc:
            return ActivationResult(
                False,
                message=redact_text(exc.user_message, [api_key]),
                raw_preview=redact_text(exc.detail, [api_key])[:500],
            )
        except UnicodeEncodeError as exc:
            return ActivationResult(
                False,
                message="ActivationForm 调用失败：模型接口请求编码失败；请检查 API Key、Base URL、模型名是否包含中文、全角符号或不可见字符。",
                raw_preview=redact_text(str(exc), [api_key])[:500],
            )
        except Exception as exc:  # noqa: BLE001 - 激活边界不得打崩 Runtime
            return ActivationResult(False, message=f"ActivationForm 调用失败：{type(exc).__name__}。", raw_preview=redact_text(str(exc), [api_key])[:500])
        raw = str(getattr(chat_result, "content", "") or "")
        try:
            form = parse_activation_form(raw)
        except Exception as exc:  # noqa: BLE001
            return ActivationResult(False, message=f"ActivationForm 未通过校验：{type(exc).__name__}: {exc}。", raw_preview=raw[:500])
        if self._needs_work_retry(form, user_selected_mode):
            retry_envelope = compile_activation_decision_prompt(
                user_message,
                config=model_config,
                user_selected_mode=user_selected_mode,
                context_hint=self._work_retry_hint(context_hint),
                max_steps=max_steps,
            )
            try:
                retry_result = model_client.chat(retry_envelope, model_config)
                retry_raw = str(getattr(retry_result, "content", "") or "")
                retry_form = parse_activation_form(retry_raw)
            except AgentShellError as exc:
                return ActivationResult(
                    False,
                    form=form,
                    message=redact_text(exc.user_message, [api_key]),
                    raw_preview=redact_text(exc.detail, [api_key])[:500],
                )
            except Exception:
                retry_raw = locals().get("retry_raw", "")
            else:
                if retry_form.mode == "work" and retry_form.tools_requested:
                    return ActivationResult(
                        True,
                        form=retry_form,
                        message=(
                            "ActivationForm 已填写："
                            f"mode={retry_form.mode} work_type={retry_form.work_type} depth={retry_form.execution_depth}。"
                        ),
                        raw_preview=retry_raw[:500],
                    )
            if self._looks_like_local_work(user_message):
                fallback_form = self._fallback_work_form(user_message)
                return ActivationResult(
                    True,
                    form=fallback_form,
                    message=(
                        "ActivationForm 已由显式工作模式兜底激活："
                        f"mode={fallback_form.mode} work_type={fallback_form.work_type} "
                        f"depth={fallback_form.execution_depth}。"
                    ),
                    raw_preview=(locals().get("retry_raw", raw) or raw)[:500],
                )
        return ActivationResult(
            True,
            form=form,
            message=f"ActivationForm 已填写：mode={form.mode} work_type={form.work_type} depth={form.execution_depth}。",
            raw_preview=raw[:500],
        )
