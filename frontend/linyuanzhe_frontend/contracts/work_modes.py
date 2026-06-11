from __future__ import annotations

"""Frontend two-mode contract for L6.72.51.

Only two user-visible modes remain: chat and work.  The frontend does not infer
code/file/document/long_chain.  It submits the user's explicit preference to
Runtime; Runtime then sends ActivationFormSpec through PromptIntegrator, and LLM
fills the real mode/work_type/execution_depth/tools_requested fields.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping
import re

WORK_MODE_CONTRACT_VERSION = "tiangong.l6_72_51.two_mode_activation.v1"


@dataclass(frozen=True)
class WorkModeSpec:
    value: str
    label: str
    short_label: str
    description: str
    send_button: str
    planner_allowed: bool
    tools_requested: bool
    activation_requested: bool = False


WORK_MODE_SPECS: tuple[WorkModeSpec, ...] = (
    WorkModeSpec(
        value="chat",
        label="聊天",
        short_label="聊",
        description="普通交流、解释、讨论、规划；不主动启动工具执行链。",
        send_button="发送",
        planner_allowed=False,
        tools_requested=False,
        activation_requested=False,
    ),
    WorkModeSpec(
        value="work",
        label="工作",
        short_label="工",
        description="真实执行入口；Runtime 只发填空题材料，LLM 填 ActivationForm 后再激活工具/长链。",
        send_button="开始工作",
        planner_allowed=True,
        tools_requested=True,
        activation_requested=True,
    ),
)

_WORK_MODE_BY_VALUE = {item.value: item for item in WORK_MODE_SPECS}
_WORK_MODE_BY_LABEL = {item.label: item for item in WORK_MODE_SPECS}
_WORK_MODE_BY_LABEL.update({item.short_label: item for item in WORK_MODE_SPECS})

_LEGACY_TO_WORK = {
    "干活": "work",
    "干": "work",
    "代码": "work",
    "码": "work",
    "文件": "work",
    "文": "work",
    "长链": "work",
    "链": "work",
    "code": "work",
    "file": "work",
    "document": "work",
    "long_chain": "work",
    "long-chain": "work",
    "longchain": "work",
    "coding": "work",
    "dev": "work",
    "execute": "work",
    "execution": "work",
    "working": "work",
    "task": "work",
    "work_mode": "work",
    "聊天": "chat",
    "聊": "chat",
}

_CASUAL_CHAT_EXACT = {"在", "在吗", "在么", "你好", "您好", "hello", "hi", "hey", "ping", "测试"}
_CASUAL_CHAT_PATTERNS = [
    r"^(你)?在[不吗嘛么]?[?？。！!]*$",
    r"^(喂+|你好|您好|嗨|哈喽|hello|hi|hey)[?？。！!]*$",
    r"^(test|测试|ping)[?？。！!]*$",
    r"^(刚刚|刚才)?(什么情况|啥情况|咋回事|怎么回事)[啊呀呢嘛么]?[?？。！!]*$",
]


def is_casual_chat_message(text: Any) -> bool:
    """保留给旧 UI smoke 的只读辅助函数；不参与模式自动识别。"""
    message = str(text or "").strip()
    compact = re.sub(r"\s+", "", message).strip("，,。.!！?？~～")
    if not compact:
        return False
    if compact.lower() in _CASUAL_CHAT_EXACT:
        return True
    if len(compact) > 16:
        return False
    return any(re.search(pattern, compact, flags=re.IGNORECASE) for pattern in _CASUAL_CHAT_PATTERNS)


def normalize_work_mode(value: Any) -> str:
    raw = str(value or "").strip()
    if raw in _WORK_MODE_BY_VALUE:
        return raw
    if raw in _WORK_MODE_BY_LABEL:
        return _WORK_MODE_BY_LABEL[raw].value
    lowered = raw.lower().replace("-", "_").replace(" ", "_")
    alias = _LEGACY_TO_WORK.get(raw) or _LEGACY_TO_WORK.get(lowered)
    return alias if alias in _WORK_MODE_BY_VALUE else "chat"


def work_mode_spec(value: Any) -> WorkModeSpec:
    return _WORK_MODE_BY_VALUE[normalize_work_mode(value)]


def work_mode_labels() -> List[str]:
    return [item.label for item in WORK_MODE_SPECS]


def work_mode_label(value: Any) -> str:
    return work_mode_spec(value).label


def work_mode_value(label_or_value: Any) -> str:
    return normalize_work_mode(label_or_value)


def infer_work_mode_from_text(text: Any) -> str:  # noqa: ARG001 - compatibility only
    """L6.72.51 起不再按关键词识别模式。真实裁决由 LLM 填 ActivationForm。"""
    return "chat"


def resolve_submit_work_mode(selected_mode: Any, text: Any) -> Dict[str, Any]:  # noqa: ARG001
    selected = normalize_work_mode(selected_mode)
    spec = work_mode_spec(selected)
    return {
        "contract": WORK_MODE_CONTRACT_VERSION,
        "selected_mode": selected,
        "inferred_mode": "llm_decides",
        "effective_mode": selected,
        "mode": selected,
        "label": spec.label,
        "description": spec.description,
        "auto_promoted": False,
        "casual_chat_override": False,
        "planner_allowed": bool(spec.planner_allowed),
        "tools_requested": bool(spec.tools_requested),
        "activation_requested": bool(spec.activation_requested),
        "tool_mode_requested": "runtime_governed" if spec.activation_requested else "disabled",
        "long_chain_requested": False,
        "file_intent": False,
        "code_intent": False,
        "quality_gate_required": bool(spec.activation_requested),
        "confirmation_popup_expected": bool(spec.activation_requested),
        "frontend_only": True,
        "no_frontend_tool_execution": True,
        "no_frontend_memory_write": True,
        "no_frontend_rollback_apply": True,
        "llm_fills_activation_form": True,
    }


def sanitize_work_mode_payload(value: Any) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        return resolve_submit_work_mode("chat", "")
    raw_input_mode = value.get("effective_mode") or value.get("mode") or value.get("selected_mode")
    mode = normalize_work_mode(raw_input_mode)
    raw_input_mode_text = str(raw_input_mode or "").strip().lower()
    payload = dict(resolve_submit_work_mode(mode, ""))
    payload["contract"] = WORK_MODE_CONTRACT_VERSION
    # 兼容旧 payload，但不允许旧 code/file/long_chain 恢复为用户模式。
    for key in ("selected_mode", "effective_mode", "mode"):
        if key in value:
            payload[key] = normalize_work_mode(value.get(key))
    payload["label"] = work_mode_label(payload.get("effective_mode") or payload.get("mode"))
    spec = work_mode_spec(payload.get("effective_mode") or payload.get("mode"))
    payload["planner_allowed"] = bool(spec.planner_allowed)
    payload["tools_requested"] = bool(spec.tools_requested)
    payload["activation_requested"] = bool(spec.activation_requested)
    payload["tool_mode_requested"] = "runtime_governed" if spec.activation_requested else "disabled"
    # Work 模式默认只请求 ActivationForm，不默认打开长链；
    # 但调用方显式标记 long_chain/task_flow 时必须保留，否则断链续接与长链工作台无法启动。
    canonical_work_mode = raw_input_mode_text in {"work", "工作"}
    explicit_long_chain = bool(value.get("long_chain_requested")) and canonical_work_mode
    explicit_task_flow = bool(value.get("task_flow_requested")) and canonical_work_mode
    payload["long_chain_requested"] = explicit_long_chain
    payload["task_flow_requested"] = explicit_task_flow or explicit_long_chain
    payload["file_intent"] = False
    payload["code_intent"] = False
    payload["quality_gate_required"] = bool(spec.activation_requested)
    payload["confirmation_popup_expected"] = bool(spec.activation_requested)
    payload["frontend_only"] = True
    payload["no_frontend_tool_execution"] = True
    payload["no_frontend_memory_write"] = True
    payload["no_frontend_rollback_apply"] = True
    payload["llm_fills_activation_form"] = True
    return payload
