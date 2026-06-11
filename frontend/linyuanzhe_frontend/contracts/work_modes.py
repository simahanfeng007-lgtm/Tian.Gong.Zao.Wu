from __future__ import annotations

"""Frontend two-mode contract for L6.72.51.

Only two user-visible modes remain: chat and work.  The frontend does not infer
code/file/document/long_chain.  It submits the user's explicit preference to
Runtime; Runtime then sends ActivationFormSpec through PromptIntegrator, and LLM
fills the real mode/work_type/execution_depth/tools_requested fields.

Q22 note:
"工作" is an execution *preference*, not a command to force every message through
the tool runtime.  Short social turns, identity questions, product capability
questions, and error/explanation questions are dialogue-only unless the user asks
for a concrete read/write/run/repair/package action.
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

_CASUAL_CHAT_EXACT = {
    "在", "在吗", "在么", "你好", "您好", "hello", "hi", "hey", "ping", "测试",
    "忙呢", "忙吗", "忙嘛", "忙不忙", "你忙吗", "你忙呢", "在忙吗", "还忙吗",
    "在干嘛", "干嘛呢", "你在干嘛", "忙啥呢", "忙什么呢", "有人吗",
    "早", "早上好", "晚上好", "午安", "晚安",
}
_CASUAL_CHAT_PATTERNS = [
    r"^(你)?在[不吗嘛么]?[?？。！!]*$",
    r"^(还)?在[不吗嘛么]?[?？。！!]*$",
    r"^(喂+|你好|您好|嗨|哈喽|hello|hi|hey)[?？。！!]*$",
    r"^(test|测试|ping)[?？。！!]*$",
    r"^有人吗[?？。！!]*$",
    r"^(你|还)?(在)?忙(呢|吗|嘛|么|不忙)?[?？。！!]*$",
    r"^(你)?在(干嘛|干啥)(呢)?[?？。！!]*$",
    r"^(干嘛|干啥)(呢)?[?？。！!]*$",
    r"^忙(啥|什么)(呢)?[?？。！!]*$",
    r"^(刚刚|刚才)?(什么情况|啥情况|咋回事|怎么回事)[啊呀呢嘛么]?[?？。！!]*$",
]

_DIALOGUE_ONLY_EXACT = {
    "你是谁", "你叫什么", "你叫什么名字", "介绍一下你", "介绍一下你自己", "你是什么",
    "你能做什么", "你会做什么", "你有什么功能", "你能干什么",
    "这是什么问题", "这是什么情况", "这是什么意思", "什么意思", "啥意思",
    "现在这个能做长链工作了", "这个能做长链工作了", "能做长链工作了吗",
}
_DIALOGUE_ANALYSIS_PATTERNS = [
    r"^(请问)?(你)?(是谁|叫什么|是什么|能做什么|会做什么|能干什么|有什么功能)[啊呀呢嘛么]?[?？。！!]*$",
    r"^(为什么|为啥|咋|怎么会|怎么)(会)?(这样|这样子|这样啊).{0,80}[?？。！!]*$",
    r"^.{0,40}(为什么|为啥|咋回事|怎么回事|什么情况|啥情况).{0,60}[?？。！!]*$",
    r"^.{0,40}(是什么问题|是什么原因|什么意思|啥意思|哪里错了|哪里不对|正常吗).{0,50}[?？。！!]*$",
    r"^.{0,40}(是不是|是否|有没有|能不能|能否|可以吗|可不可以).{0,80}[?？。！!]*$",
    r"^(帮我|请|麻烦)?(解释|说明|讲讲|说说|分析)(一下)?(这个|这段|上面|刚才|刚刚)?.{0,60}(报错|错误|回复|现象|问题|截图|提示|原因)?[?？。！!]*$",
    r"^.{0,40}(无法|不能|不会|没法).{0,60}(吗|嘛|么|呢|是不是|是否|为什么|怎么回事|原因)[?？。！!]*$",
]

_HOST_PATH_RE = re.compile(
    r"(?:[A-Za-z]:\\|/(?:Users|home|mnt|Volumes|var|tmp|opt|etc|workspace)/)",
    re.IGNORECASE,
)
_FILE_TARGET_RE = re.compile(
    r"(?<![\w-])[\w\u4e00-\u9fff ._-]+\.(?:py|js|ts|tsx|jsx|java|go|rs|cpp|c|h|hpp|cs|php|rb|swift|kt|m|mm|sh|bat|cmd|ps1|md|txt|json|yaml|yml|toml|ini|cfg|csv|xlsx?|docx?|pptx?|pdf|zip|7z|rar|tar|gz|log)(?![\w-])",
    re.IGNORECASE,
)
_CODE_FENCE_RE = re.compile(r"```|~~~")
_EXECUTION_PATTERNS = [
    r"(请|帮我|麻烦|替我|给我|开始|直接|马上|继续|现在)(检查|扫描|质检|修复|修改|改一下|改成|重构|优化|补丁|写入|创建|新建|生成|删除|移除|重命名|移动|复制|读取|打开|运行|执行|测试|复测|验证|打包|压缩|解压|安装|部署|发布|回滚|接入|配置|连接)",
    r"^(检查|扫描|质检|修复|修改|改一下|改成|重构|优化|补丁|写入|创建|新建|生成|删除|移除|重命名|移动|复制|读取|打开|运行|执行|测试|复测|验证|打包|压缩|解压|安装|部署|发布|回滚|接入|配置|连接)",
    r"(定位\s*bug|修\s*bug|fix\s+bug|repair|patch|hotfix|smoke|verifier|回归|fresh\s*extract)",
    r"(跑一下|跑一遍|执行一下|启动一下|测一下|复测一下|打包一下|修一下|改一下|写一个|建一个|生成一个)",
    r"(把|将).{0,40}(写入|改成|移动|复制|删除|打包|压缩|解压|发布|部署|上传|导出)",
]


def _compact_text(value: Any) -> str:
    return re.sub(r"\s+", "", str(value or "")).strip("，,。.!！?？~～")


def is_casual_chat_message(text: Any) -> bool:
    """保留给旧 UI smoke 的只读辅助函数；不参与代码/文件模式自动识别。"""
    message = str(text or "").strip()
    compact = _compact_text(message)
    if not compact:
        return False
    if compact.lower() in _CASUAL_CHAT_EXACT:
        return True
    if len(compact) > 16:
        return False
    return any(re.search(pattern, compact, flags=re.IGNORECASE) for pattern in _CASUAL_CHAT_PATTERNS)


def _looks_like_execution_request(text: Any) -> bool:
    message = str(text or "").strip()
    compact = _compact_text(message)
    lowered = message.lower()
    if not compact:
        return False
    if any(re.search(pattern, compact, flags=re.IGNORECASE) for pattern in _EXECUTION_PATTERNS):
        return True
    # A path/file/code block alone is not enough; pair it with an execution verb.
    target_present = bool(_HOST_PATH_RE.search(message) or _FILE_TARGET_RE.search(message) or _CODE_FENCE_RE.search(message))
    if target_present and any(marker in compact for marker in (
        "读取", "打开", "修复", "修改", "写入", "创建", "生成", "删除", "运行", "执行",
        "测试", "复测", "验证", "打包", "压缩", "解压", "安装", "部署", "发布", "回滚",
        "检查", "扫描", "质检", "导出", "保存",
    )):
        return True
    if any(token in lowered for token in ("pytest", "npm run", "pip install", "python ", "powershell", "cmd.exe", "git commit", "git checkout")):
        return True
    return False


def is_dialogue_or_analysis_message(text: Any) -> bool:
    """True when a message should stay in chat even if the UI selector is 工作.

    This intentionally covers more than "hi/忙呢": product capability questions,
    "why did this happen?", "what does this error mean?", and user-facing bug
    reports should be answered conversationally unless they include a concrete
    execution request.
    """
    message = str(text or "").strip()
    compact = _compact_text(message)
    if not compact:
        return False
    if is_casual_chat_message(message):
        return True
    if _looks_like_execution_request(message):
        return False
    if compact in _DIALOGUE_ONLY_EXACT or compact.lower() in {x.lower() for x in _DIALOGUE_ONLY_EXACT}:
        return True
    if len(compact) <= 140 and any(re.search(pattern, compact, flags=re.IGNORECASE) for pattern in _DIALOGUE_ANALYSIS_PATTERNS):
        return True
    # Short question-like turns are dialogue unless they look like an operation.
    if len(compact) <= 90 and (("？" in message) or ("?" in message)):
        if any(marker in compact for marker in ("为什么", "为啥", "怎么", "咋", "什么", "啥", "是否", "是不是", "有没有", "能不能", "能否", "可以", "正常吗", "问题", "错误", "报错", "意思", "原因", "网关", "微信", "飞书", "长链")):
            return True
    return False


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


def resolve_submit_work_mode(selected_mode: Any, text: Any) -> Dict[str, Any]:
    selected = normalize_work_mode(selected_mode)
    dialogue_override = bool(selected == "work" and is_dialogue_or_analysis_message(text))
    casual_chat_override = bool(selected == "work" and is_casual_chat_message(text))
    effective = "chat" if dialogue_override else selected
    spec = work_mode_spec(effective)
    override_reason = "casual_chat" if casual_chat_override else ("dialogue_or_analysis" if dialogue_override else "")
    return {
        "contract": WORK_MODE_CONTRACT_VERSION,
        "selected_mode": selected,
        "inferred_mode": "llm_decides",
        "effective_mode": effective,
        "mode": effective,
        "label": spec.label,
        "description": spec.description,
        "auto_promoted": False,
        # Kept for Q21/legacy callers.  In Q22 this means "safe chat override",
        # including casual turns and non-executing analysis questions.
        "casual_chat_override": dialogue_override,
        "dialogue_only_override": dialogue_override,
        "dialogue_analysis_override": bool(dialogue_override and not casual_chat_override),
        "override_reason": override_reason,
        "planner_allowed": bool(spec.planner_allowed),
        "tools_requested": bool(spec.tools_requested),
        "activation_requested": bool(spec.activation_requested),
        "tool_mode_requested": "runtime_governed" if spec.activation_requested else "disabled",
        "long_chain_requested": False,
        "task_flow_requested": False,
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
    for key in ("casual_chat_override", "dialogue_only_override", "dialogue_analysis_override"):
        if key in value:
            payload[key] = bool(value.get(key))
    if "override_reason" in value:
        payload["override_reason"] = str(value.get("override_reason") or "")[:80]
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
