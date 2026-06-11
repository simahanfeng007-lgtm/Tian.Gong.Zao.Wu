"""L6.72.51 主脑填空激活协议。

Runtime 只生成 ActivationFormSpec 材料；PromptCompiler 统一整合后交给
LLM；LLM 填 ActivationForm；Runtime 只校验字段并按答案装配工具链。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

ALLOWED_MODES = {"chat", "work"}
ALLOWED_WORK_TYPES = {"none", "file", "document", "code", "terminal", "desktop", "web", "mixed"}
ALLOWED_EXECUTION_DEPTHS = {"single_turn", "single_step", "multi_step", "long_chain"}
ALLOWED_RISK_LEVELS = {"A0", "A1", "A2", "A3", "A4", "A5"}
ALLOWED_FINAL_OUTPUT_CONTRACTS = {"answer_only", "execution_report", "artifact_delivery"}


@dataclass(frozen=True)
class ActivationForm:
    mode: str = "chat"
    work_type: str = "none"
    execution_depth: str = "single_turn"
    tools_requested: bool = False
    required_tool_classes: tuple[str, ...] = tuple()
    risk_level: str = "A0"
    need_quality_gate: bool = False
    need_user_confirm: bool = False
    expected_result: str = ""
    final_output_contract: str = "answer_only"
    reason: str = ""
    raw: Mapping[str, Any] = field(default_factory=dict)

    def public_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "work_type": self.work_type,
            "execution_depth": self.execution_depth,
            "tools_requested": self.tools_requested,
            "required_tool_classes": list(self.required_tool_classes),
            "risk_level": self.risk_level,
            "need_quality_gate": self.need_quality_gate,
            "need_user_confirm": self.need_user_confirm,
            "expected_result": self.expected_result,
            "final_output_contract": self.final_output_contract,
            "reason": self.reason,
        }

    @property
    def activates_runtime_tools(self) -> bool:
        return self.mode == "work" and self.tools_requested and self.risk_level != "A5"


def activation_schema_card(*, user_selected_mode: str = "", context_hint: str = "") -> str:
    selected = _safe(user_selected_mode, 40) or "未显式选择"
    hint = _safe(context_hint, 1800)
    lines = [
        "[ActivationFormSpec / 主脑填空激活协议 / L6.72.51]",
        "Runtime 不能替 LLM 判断任务类型；Runtime 只提交本填空题材料给 PromptCompiler。",
        "PromptCompiler 是唯一提示词整合出口；你必须在完整上下文中填写 ActivationForm。",
        f"user_selected_mode={selected}；该值只是用户显式偏好，不是 Runtime 硬路由。",
        "只允许两个用户模式：chat 与 work。code/file/document/long_chain 都不是用户模式。",
        "当用户只是问答、解释、讨论、规划时：mode=chat, tools_requested=false。",
        "当用户要求真实完成任务时：mode=work, tools_requested=true。",
        "工作任务包括：文件、文档、代码、终端、桌面、网页、批处理、继续、下一步、修复、打包、完整验收。",
        "work_type 只能是：none/file/document/code/terminal/desktop/web/mixed。",
        "execution_depth 只能是：single_turn/single_step/multi_step/long_chain。长链是执行深度，不是用户模式。",
        "A0-A4 默认允许进入 Runtime/QualityGate 审计链；只有 A5 极高危需要硬拦或人工确认。",
        "文档系统不得抢占模式裁决：只有你填写 work_type=document 时，Runtime 才装配文档工具。",
        "必须只输出合法 JSON，不附加解释、Markdown 或代码块。",
        "JSON schema:",
        '{"mode":"chat|work","work_type":"none|file|document|code|terminal|desktop|web|mixed","execution_depth":"single_turn|single_step|multi_step|long_chain","tools_requested":true|false,"required_tool_classes":["file_read","code_patch"],"risk_level":"A0|A1|A2|A3|A4|A5","need_quality_gate":true|false,"need_user_confirm":true|false,"expected_result":"...","final_output_contract":"answer_only|execution_report|artifact_delivery","reason":"简短裁决理由"}',
    ]
    if hint:
        lines.extend(["[recent_context_hint]", hint])
    return "\n".join(lines)


def activation_execution_card(form: ActivationForm, *, context_hint: str = "") -> str:
    lines = [
        "[ActivationForm / LLM已填写的激活答案 / Runtime只校验不重判]",
        json.dumps(form.public_dict(), ensure_ascii=False, indent=2),
        "执行阶段规则：",
        "- Runtime 按上面的 mode/work_type/execution_depth/tools_requested 装配工具与长链协议。",
        "- 你现在必须输出可审计 JSON plan；不得只给建议而不执行。",
        "- 创建文件必须规划真实写入工具；列目录必须规划目录工具；修改代码必须读取/修改/验证。",
        "- 工具失败后应继续诊断、降级、替代路径或明确失败点。",
        "- 长链任务必须阶段化：Plan -> Act -> Observe -> Verify -> Replan/Continue -> Checkpoint -> Final。",
    ]
    hint = _safe(context_hint, 2400)
    if hint:
        lines.extend(["[execution_context_hint]", hint])
    return "\n".join(lines)


def parse_activation_form(raw_text: str) -> ActivationForm:
    data = _extract_json_object(raw_text)
    if not isinstance(data, dict):
        raise ValueError("ActivationForm 不是 JSON object。")
    mode = _normalize_enum(data.get("mode"), ALLOWED_MODES, "chat")
    work_type = _normalize_enum(data.get("work_type"), ALLOWED_WORK_TYPES, "none")
    depth = _normalize_enum(data.get("execution_depth"), ALLOWED_EXECUTION_DEPTHS, "single_turn")
    tools = _bool(data.get("tools_requested"))
    risk = _normalize_risk(data.get("risk_level"))
    final_contract = _normalize_enum(data.get("final_output_contract"), ALLOWED_FINAL_OUTPUT_CONTRACTS, "answer_only")
    required = tuple(_safe(x, 80) for x in _as_list(data.get("required_tool_classes")) if _safe(x, 80))[:16]
    if mode == "chat":
        work_type = "none"
        depth = "single_turn"
        tools = False
    if mode == "work" and work_type == "none":
        work_type = "mixed"
    return ActivationForm(
        mode=mode,
        work_type=work_type,
        execution_depth=depth,
        tools_requested=tools,
        required_tool_classes=required,
        risk_level=risk,
        need_quality_gate=_bool(data.get("need_quality_gate")) or tools,
        need_user_confirm=_bool(data.get("need_user_confirm")) or risk == "A5",
        expected_result=_safe(data.get("expected_result"), 500),
        final_output_contract=final_contract,
        reason=_safe(data.get("reason"), 400),
        raw=dict(data),
    )


def activation_failure_message(exc: Exception) -> str:
    return f"ActivationForm 未通过校验：{type(exc).__name__}: {_safe(exc, 220)}。"


def _extract_json_object(raw_text: str) -> Any:
    text = str(raw_text or "").strip()
    if not text:
        raise ValueError("空输出。")
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"\s*```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    start = text.find("{")
    if start < 0:
        raise ValueError("未找到 JSON object。")
    depth = 0
    in_str = False
    escape = False
    for index in range(start, len(text)):
        ch = text[index]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return json.loads(text[start:index + 1])
    raise ValueError("JSON object 未闭合。")


def _normalize_enum(value: Any, allowed: set[str], default: str) -> str:
    clean = str(value or "").strip().lower().replace("-", "_").replace(" ", "_")
    alias = {
        "聊天": "chat",
        "干活": "work",
        "工作": "work",
        "代码": "code",
        "文件": "file",
        "文档": "document",
        "长链": "long_chain",
        "single": "single_step",
        "multi": "multi_step",
    }.get(clean, clean)
    return alias if alias in allowed else default


def _normalize_risk(value: Any) -> str:
    text = str(value or "A0").strip().upper()
    if text in ALLOWED_RISK_LEVELS:
        return text
    m = re.search(r"A[0-5]", text)
    return m.group(0) if m else "A0"


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "需要", "是", "启用"}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str) and value.strip():
        return [x.strip() for x in value.split(",") if x.strip()]
    return []


def _safe(value: Any, limit: int) -> str:
    text = str(value or "").replace("\x00", "").strip()
    return text[: max(16, int(limit))]
