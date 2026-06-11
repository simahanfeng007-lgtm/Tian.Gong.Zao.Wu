from __future__ import annotations

"""FE01 STEP54 / L6.72.47 local desktop Runtime bridge.

This bridge is bundled for the desktop all-in-one package. It exposes the
frontend Runtime HTTP/SSE contract and delegates chat execution to the bundled
backend CLI entrypoint. It is deliberately labeled as a local desktop bridge,
not as the official TiangongWangguan real Runtime smoke target.
"""

import argparse
import base64
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlsplit, urlunsplit
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend" / "project"


def _default_reports_dir() -> Path:
    override = os.environ.get("LINYUANZHE_REPORT_DIR", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    if os.environ.get("LINYUANZHE_ALLOW_PACKAGE_REPORTS", "").strip().lower() in {"1", "true", "yes", "on"}:
        return ROOT / "reports"
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", "").strip()
        if base:
            return Path(base).expanduser() / "LinyuanzheDesktop" / "reports"
        return Path.home() / "AppData" / "Roaming" / "LinyuanzheDesktop" / "reports"
    base = os.environ.get("XDG_STATE_HOME", "").strip()
    if base:
        return Path(base).expanduser() / "linyuanzhe_desktop" / "reports"
    return Path(tempfile.gettempdir()) / "linyuanzhe_desktop_reports"


REPORTS = _default_reports_dir()
RUN_AGENT = BACKEND / "run_agent.py"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
try:
    from tiangong_agent_runtime.document_parser import parse_document as _document_parse_document
    from tiangong_agent_runtime.document_parser import should_route_to_document_parse as _should_route_to_document_parse
except Exception:
    _document_parse_document = None
    _should_route_to_document_parse = None
try:
    from tiangong_agent_runtime.document_context_store import (
        build_rewrite_plan as _document_build_rewrite_plan,
        query_document_context as _document_query_context,
        save_document_context as _document_save_context,
    )
except Exception:
    _document_build_rewrite_plan = None
    _document_query_context = None
    _document_save_context = None

PRODUCT_IDENTITY = {
    "schema": "tiangong.l6_51_1.product_identity.v1",
    "product_name": "天工造物 v2.0 - 临渊者",
    "unique_developer": "于泳翔",
    "angel_investor": "胖胖龙",
    "public": True,
    "runtime_semantics": "metadata_only",
    "frontend_permission": "read_only_display",
}

CONTROL_PATHS = {
    "/control/task/stop": "stop",
    "/control/task/reset": "reset",
    "/control/task/interrupt": "interrupt",
    "/runtime/reconnect": "reconnect",
}

SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"(?i)Bearer\s+[A-Za-z0-9_\-.]{8,}"),
    re.compile(r"(?i)mockkey_[A-Za-z0-9_\-]{8,}"),
)

DEEPSEEK_OFFICIAL_BASE_URL = "https://api.deepseek.com"
DEEPSEEK_DEFAULT_MODEL = "deepseek-v4-pro"
DEEPSEEK_MODEL_FALLBACKS = (
    "deepseek-v4-pro",
    "deepseek-v4-flash",
    "deepseek-chat",
    "deepseek-reasoner",
)


HOST_ACCESS_SCOPE_DEFAULT = "system_drive"
HOST_ACCESS_SCOPE_LABELS = {
    "project_workspace": "项目工作区",
    "user_home": "用户目录",
    "system_drive": "全电脑/系统盘",
    "custom_root": "自定义根目录",
}


def _normalize_host_access_scope(value: Any) -> str:
    raw = str(value or HOST_ACCESS_SCOPE_DEFAULT).strip()
    compact = raw.lower().replace("-", "_").replace(" ", "")
    underscored = raw.lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "workspace": "project_workspace",
        "project": "project_workspace",
        "project_workspace": "project_workspace",
        "sandbox": "project_workspace",
        "沙盘": "project_workspace",
        "工作区": "project_workspace",
        "项目工作区": "project_workspace",
        "项目目录": "project_workspace",
        "home": "user_home",
        "user": "user_home",
        "user_home": "user_home",
        "用户目录": "user_home",
        "用户主目录": "user_home",
        "desktop": "user_home",
        "full": "system_drive",
        "computer": "system_drive",
        "full_computer": "system_drive",
        "system": "system_drive",
        "drive": "system_drive",
        "all": "system_drive",
        "system_drive": "system_drive",
        "全电脑": "system_drive",
        "系统盘": "system_drive",
        "全电脑/系统盘": "system_drive",
        "全电脑／系统盘": "system_drive",
        "全电脑_/_系统盘": "system_drive",
        "custom": "custom_root",
        "custom_root": "custom_root",
        "自定义": "custom_root",
        "自定义根目录": "custom_root",
    }
    for key in (raw, compact, underscored):
        if key in aliases:
            return aliases[key]
        if key in HOST_ACCESS_SCOPE_LABELS:
            return key
    return HOST_ACCESS_SCOPE_DEFAULT

def _system_drive_root() -> Path:
    if platform.system() == "Windows":
        drive = os.environ.get("SystemDrive", "") or Path.home().anchor or "C:\\"
        if len(drive) == 2 and drive[1] == ":":
            drive += "\\"
        return Path(drive).expanduser().resolve()
    return Path(Path.home().anchor or "/").expanduser().resolve()


def _resolve_host_access_root(scope: str, raw_root: Any = "") -> Path:
    scope = _normalize_host_access_scope(scope)
    raw = str(raw_root or "").strip().strip('"').strip("'")
    if scope == "custom_root":
        if raw:
            try:
                resolved = Path(raw).expanduser().resolve()
                if resolved.exists() and resolved.is_dir():
                    return resolved
            except Exception:
                pass
        # Invalid custom_root must not widen to system_drive or user_home.
        # Project workspace is the narrow deterministic fallback.
        return BACKEND.resolve()
    candidates: list[Path] = []
    if scope == "project_workspace":
        candidates.append(BACKEND)
    elif scope == "user_home":
        candidates.append(Path.home())
    else:
        candidates.append(_system_drive_root())
        candidates.append(Path.home())
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
            if resolved.exists() and resolved.is_dir():
                return resolved
        except Exception:
            continue
    return BACKEND.resolve()

def _relative_to_root(path: Path, root: Path) -> str:
    try:
        return path.expanduser().resolve().relative_to(root.expanduser().resolve()).as_posix()
    except Exception:
        return ""



_WINDOWS_KNOWN_FOLDER_IDS = {
    "desktop": "B4BFCC3A-DB2C-424C-B029-7FE99A87C641",
    "downloads": "374DE290-123F-4565-9164-39C4925E467B",
    "documents": "FDD39AD0-238F-46AF-ADB4-6C85480369C7",
}

_WINDOWS_PROTECTED_ROOTS = {
    "windows",
    "program files",
    "program files (x86)",
    "programdata",
    "system volume information",
    "recovery",
    "$recycle.bin",
}


def _windows_known_folder_path(kind: str) -> Path | None:
    """Resolve Windows Known Folders, including OneDrive Known Folder Move.

    SHGetKnownFolderPath is the stable Windows shell source of truth for
    Desktop/Downloads/Documents.  The function is intentionally optional: on
    non-Windows hosts, or if shell resolution fails, callers fall back to
    environment-variable candidates.
    """
    if platform.system() != "Windows":
        return None
    folder_id = _WINDOWS_KNOWN_FOLDER_IDS.get(str(kind or "").strip().lower())
    if not folder_id:
        return None
    try:
        import ctypes
        import uuid as _uuid
        from ctypes import wintypes

        class GUID(ctypes.Structure):
            _fields_ = [
                ("Data1", wintypes.DWORD),
                ("Data2", wintypes.WORD),
                ("Data3", wintypes.WORD),
                ("Data4", ctypes.c_ubyte * 8),
            ]

            @classmethod
            def from_uuid(cls, value: _uuid.UUID) -> "GUID":
                data = value.bytes_le
                return cls(
                    int.from_bytes(data[0:4], "little"),
                    int.from_bytes(data[4:6], "little"),
                    int.from_bytes(data[6:8], "little"),
                    (ctypes.c_ubyte * 8).from_buffer_copy(data[8:16]),
                )

        shell32 = ctypes.windll.shell32
        ole32 = ctypes.windll.ole32
        shell32.SHGetKnownFolderPath.argtypes = [ctypes.POINTER(GUID), wintypes.DWORD, wintypes.HANDLE, ctypes.POINTER(wintypes.LPWSTR)]
        shell32.SHGetKnownFolderPath.restype = ctypes.c_long
        ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
        pointer = wintypes.LPWSTR()
        hr = shell32.SHGetKnownFolderPath(ctypes.byref(GUID.from_uuid(_uuid.UUID(folder_id))), 0, None, ctypes.byref(pointer))
        if hr != 0 or not pointer.value:
            return None
        try:
            return Path(pointer.value).expanduser()
        finally:
            ole32.CoTaskMemFree(pointer)
    except Exception:
        return None


def _dedupe_path_candidates(candidates: list[Path]) -> list[Path]:
    seen: set[str] = set()
    out: list[Path] = []
    for candidate in candidates:
        try:
            key = str(candidate.expanduser()).replace("\\", "/").rstrip("/").lower()
        except Exception:
            key = str(candidate).replace("\\", "/").rstrip("/").lower()
        if key and key not in seen:
            seen.add(key)
            out.append(candidate)
    return out


def _known_user_folder(kind: str) -> Path:
    """Resolve Desktop/Downloads/Documents with Windows/OneDrive/localized fallback.

    The bridge only exports relative path hints to the model.  It does not give
    the frontend authority to read or write files.  On Windows, Shell Known
    Folders handle OneDrive Known Folder Move.  On other hosts or shell failure,
    OneDrive/USERPROFILE/HOME candidates cover Chinese and English folder names.
    """
    kind_clean = str(kind or "").strip().lower()
    folder_names = {
        "desktop": ("桌面", "Desktop"),
        "downloads": ("下载", "Downloads"),
        "documents": ("文档", "Documents", "My Documents", "我的文档"),
    }.get(kind_clean, (kind_clean or "Desktop",))

    candidates: list[Path] = []
    known = _windows_known_folder_path(kind_clean)
    if known is not None:
        candidates.append(known)

    explicit_env = {
        "desktop": ("LINYUANZHE_DESKTOP_PATH", "DESKTOP"),
        "downloads": ("LINYUANZHE_DOWNLOADS_PATH", "DOWNLOADS"),
        "documents": ("LINYUANZHE_DOCUMENTS_PATH", "DOCUMENTS"),
    }.get(kind_clean, ())
    for key in explicit_env:
        raw = os.environ.get(key, "")
        if raw:
            candidates.append(Path(raw))

    # Prefer OneDrive bases before plain USERPROFILE to support Windows Known
    # Folder Move when SHGetKnownFolderPath is unavailable in tests/headless runs.
    base_keys = (
        "OneDrive",
        "OneDriveConsumer",
        "OneDriveCommercial",
        "USERPROFILE",
        "HOME",
    )
    bases: list[Path] = []
    for key in base_keys:
        raw = os.environ.get(key, "")
        if raw:
            bases.append(Path(raw))
    bases.append(Path.home())

    for base in bases:
        for name in folder_names:
            candidates.append(base / name)

    for candidate in _dedupe_path_candidates(candidates):
        try:
            resolved = candidate.expanduser().resolve()
            if resolved.exists() and resolved.is_dir():
                return resolved
        except Exception:
            continue
    fallback_name = folder_names[0] if folder_names else "Desktop"
    return (Path(os.environ.get("USERPROFILE", "") or str(Path.home())) / fallback_name).expanduser()


def _known_folder_projection(root: Path) -> dict[str, str]:
    projection: dict[str, str] = {}
    for kind in ("desktop", "downloads", "documents"):
        folder = _known_user_folder(kind)
        rel = _relative_to_root(folder, root)
        projection[f"{kind}_relative_path"] = rel or "<outside_access_scope>"
        projection[f"{kind}_path_digest"] = _digest(str(folder))
        projection[f"{kind}_folder_name"] = _safe_text(folder.name, 80)
    return projection


def _is_windows_protected_relative(path_text: str) -> bool:
    text = str(path_text or "").strip().replace("\\", "/")
    if not text:
        return False
    parts = [part.strip().lower() for part in text.split("/") if part.strip()]
    if not parts:
        return False
    if parts[0] in _WINDOWS_PROTECTED_ROOTS:
        return True
    return "system32" in parts or "syswow64" in parts


def _host_access_public_label(scope: str, root: Path) -> str:
    label = HOST_ACCESS_SCOPE_LABELS.get(_normalize_host_access_scope(scope), "全电脑/系统盘")
    if scope == "system_drive":
        return f"{label}（工具路径相对系统盘根目录）"
    if scope == "user_home":
        return f"{label}（工具路径相对当前用户目录）"
    if scope == "project_workspace":
        return f"{label}（工具路径相对项目目录）"
    return f"{label}（工具路径相对自定义根目录）"


def _host_access_context_hint(scope: str, root: Path) -> str:
    scope = _normalize_host_access_scope(scope)
    known = _known_folder_projection(root)
    parts = [
        "[桌面端主机文件访问提示]",
        f"- access_scope={scope}; label={HOST_ACCESS_SCOPE_LABELS.get(scope, scope)}",
        "- 所有工具 path 参数必须写成相对当前访问根的路径；禁止使用 C:\、/、~ 或 ../ 这类绝对/越界路径。",
        "- 用户说“桌面/下载/文档/我的文档”时，必须优先使用下方 relative_path；禁止臆造 Users/User/Desktop 这类占位路径。",
        "- OneDrive 桌面迁移已通过 Windows Known Folder / OneDrive fallback 处理；Desktop/桌面/Users/*/Desktop 会在 Runtime 侧归一到真实 known-folder relative_path。",
        "- 写入工具返回成功前必须完成物理落盘验真：atomic write + fsync + read-after-write + 父目录枚举。未验真不得向用户报告写入成功。",
        "- 默认先只读 list_dir / scan_project / read_file；写入、删除、覆盖等动作必须等待 Runtime/QualityGate 审批。",
        "- Windows 管理员目录包括 Windows、System32、Program Files、ProgramData、Recovery；写入/删除必须走审批且可能被系统权限拒绝。",
        "- 前端只能提交意图和审批决定，不能直接执行文件工具。",
        f"- host_access_root_digest={_digest(str(root))}",
        "- windows_known_folder_api_supported=true",
        "- one_drive_known_folder_move_supported=true",
        "- localized_folder_aliases=桌面,下载,文档,我的文档,Desktop,Downloads,Documents",
    ]
    parts.append(f"- desktop_relative_path={known.get('desktop_relative_path', '<outside_access_scope>')}")
    parts.append(f"- downloads_relative_path={known.get('downloads_relative_path', '<outside_access_scope>')}")
    parts.append(f"- documents_relative_path={known.get('documents_relative_path', '<outside_access_scope>')}")
    return "\n".join(parts)

def _looks_like_deepseek(provider: str, model: str, base_url: str) -> bool:
    blob = " ".join([provider or "", model or "", base_url or ""]).lower()
    return "deepseek" in blob or "api.deepseek.com" in blob


def _with_scheme(url: str) -> str:
    text = str(url or "").strip().strip('"').strip("'")
    if not text:
        return ""
    if "://" not in text:
        lowered = text.lower()
        scheme = "http://" if lowered.startswith(("localhost", "127.", "0.0.0.0")) else "https://"
        text = scheme + text
    return text


def _normalize_provider_base_url(provider: str, model: str, base_url: str) -> str:
    text = _with_scheme(base_url)
    is_deepseek = _looks_like_deepseek(provider, model, text)
    if not text:
        return DEEPSEEK_OFFICIAL_BASE_URL if is_deepseek else ""
    try:
        parsed = urlsplit(text)
    except Exception:
        return text.rstrip("/")
    path = (parsed.path or "").rstrip("/")
    lowered_path = path.lower()
    # 用户经常把完整 endpoint 填进 Base URL。OpenAI SDK 风格 Base URL
    # 应该是 endpoint 前缀，真正的 /chat/completions 由客户端拼接。
    if lowered_path.endswith("/chat/completions"):
        path = path[: -len("/chat/completions")].rstrip("/")
        lowered_path = path.lower()
    # DeepSeek 官方 OpenAI-compatible 示例使用 https://api.deepseek.com；
    # /v1 是常见误填，会导致部分 DeepSeek 路由 404。
    if is_deepseek and (parsed.netloc.lower() == "api.deepseek.com") and lowered_path in {"", "/", "/v1"}:
        path = ""
    rebuilt = urlunsplit((parsed.scheme or "https", parsed.netloc, path, "", ""))
    return rebuilt.rstrip("/")


def _normalize_provider_fields(provider: str, model: str, base_url: str) -> tuple[str, str, str]:
    provider_clean = str(provider or "openai_compatible").strip().lower() or "openai_compatible"
    if provider_clean == "custom":
        provider_clean = "openai_compatible"
    model_clean = str(model or "").strip()
    base_clean = str(base_url or "").strip()
    if _looks_like_deepseek(provider_clean, model_clean, base_clean):
        provider_clean = "deepseek"
        if not model_clean:
            model_clean = DEEPSEEK_DEFAULT_MODEL
    base_clean = _normalize_provider_base_url(provider_clean, model_clean, base_clean)
    if provider_clean == "deepseek" and not model_clean:
        model_clean = DEEPSEEK_DEFAULT_MODEL
    return provider_clean, model_clean, base_clean


def _provider_public_hint(provider: str, model: str, base_url: str) -> str:
    if _looks_like_deepseek(provider, model, base_url):
        return "DeepSeek OpenAI-compatible: Base URL 建议填写 https://api.deepseek.com；不要填写 /v1/chat/completions。模型优先 deepseek-v4-pro，可回退 deepseek-v4-flash。"
    return "OpenAI-compatible: Base URL 填写到版本前缀或服务商根地址，客户端会自动拼接 /chat/completions。"


def _unique(items: tuple[str, ...] | list[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out



WORK_MODE_TO_RUNTIME = {
    "chat": ("ordinary_chat", "rule_only", "normal_chat"),
    # L6.72.51：用户可见只有 chat/work。work 不代表 Runtime 硬判任务类型；
    # 它只启动 ActivationForm 填空链，work_type/execution_depth 由 LLM 填写。
    "work": ("tool_task", "model_suggest", "tool_plan"),
}


def _normalize_frontend_work_mode(value: Any) -> str:
    clean = str(value or "chat").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "聊天": "chat",
        "聊": "chat",
        "干活": "work",
        "干": "work",
        "工作": "work",
        "工": "work",
        "work_mode": "work",
        "execute": "work",
        "execution": "work",
        "task": "work",
        "代码": "work",
        "码": "work",
        "coding": "work",
        "code": "work",
        "dev": "work",
        "文件": "work",
        "文": "work",
        "files": "work",
        "file": "work",
        "document": "work",
        "long_chain": "work",
        "长链": "work",
        "链": "work",
        "long": "work",
        "chain": "work",
    }
    clean = aliases.get(clean, clean)
    return clean if clean in WORK_MODE_TO_RUNTIME else "chat"


_CASUAL_CHAT_EXACT = {
    "在", "在不", "在吗", "在嘛", "在么", "你在吗", "你在不", "还在吗", "还在不",
    "喂", "喂喂", "你好", "您好", "嗨", "哈喽", "hello", "hi", "hey",
    "test", "测试", "ping", "有人吗", "早", "早上好", "晚上好", "午安", "晚安",
    "什么情况", "刚刚什么情况", "刚才什么情况", "咋回事", "刚刚咋回事", "刚才咋回事",
    "怎么回事", "刚刚怎么回事", "刚才怎么回事", "啥情况", "刚刚啥情况", "刚才啥情况",
}
_CASUAL_CHAT_PATTERNS = (
    re.compile(r"^(你)?在[不吗嘛么]?[?？。！!]*$", re.IGNORECASE),
    re.compile(r"^(还)?在[不吗嘛么]?[?？。！!]*$", re.IGNORECASE),
    re.compile(r"^(喂+|你好|您好|嗨|哈喽|hello|hi|hey)[?？。！!]*$", re.IGNORECASE),
    re.compile(r"^(test|测试|ping)[?？。！!]*$", re.IGNORECASE),
    re.compile(r"^有人吗[?？。！!]*$", re.IGNORECASE),
    re.compile(r"^(刚刚|刚才)?(什么情况|啥情况|咋回事|怎么回事)[啊呀呢嘛么]?[?？。！!]*$", re.IGNORECASE),
)


def _is_casual_chat_message(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    compact = re.sub(r"\s+", "", text).strip("，,。.!！?？~～")
    if not compact:
        return False
    if compact.lower() in _CASUAL_CHAT_EXACT:
        return True
    if len(compact) > 16:
        return False
    return any(pattern.search(compact) for pattern in _CASUAL_CHAT_PATTERNS)


_DIALOGUE_ONLY_EXACT = {
    "你是谁", "你叫什么", "你叫什么名字", "介绍一下你", "介绍一下你自己", "你是什么",
    "你能做什么", "你会做什么", "你有什么功能", "你能干什么", "你是谁？", "你能做什么？",
}
_DIALOGUE_ONLY_PATTERNS = (
    re.compile(r"^(请)?(简单)?介绍一下你(自己)?[。.!！?？]*$", re.IGNORECASE),
    re.compile(r"^你(是谁|叫什么|是什么|能做什么|会做什么|能干什么|有什么功能)[啊呀呢嘛么]?[。.!！?？]*$", re.IGNORECASE),
)


def _is_dialogue_only_message(value: Any) -> bool:
    text = str(value or "").strip()
    if not text:
        return False
    compact = re.sub(r"\s+", "", text).strip("，,。.!！?？~～")
    if not compact:
        return False
    if _is_casual_chat_message(compact):
        return True
    if compact in _DIALOGUE_ONLY_EXACT or compact.lower() in {x.lower() for x in _DIALOGUE_ONLY_EXACT}:
        return True
    if len(compact) > 32:
        return False
    return any(pattern.search(compact) for pattern in _DIALOGUE_ONLY_PATTERNS)


def _local_dialogue_answer(value: Any, state: "BridgeState" | None = None) -> str:
    text = str(value or "").strip()
    if _is_casual_chat_message(text):
        return "在。"
    persona = _safe_text(getattr(state, "persona_name", "临渊者") if state is not None else "临渊者", 32) or "临渊者"
    return f"我是{persona}，天工造物 v2.0 的本地智能体外骨骼。普通聊天不会进入工具状态；需要我真实读取、写入、修复或打包时，再切换工作任务并说明目标。"


def _runtime_directives_from_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    work_payload = payload.get("work_mode") if isinstance(payload.get("work_mode"), Mapping) else {}
    raw_mode = (
        work_payload.get("effective_mode")
        or work_payload.get("mode")
        or payload.get("frontend_work_mode")
        or payload.get("work_mode")
        or "chat"
    )
    selected_mode = _normalize_frontend_work_mode(raw_mode)
    user_message = (
        payload.get("raw_user_text")
        or payload.get("text_raw")
        or payload.get("original_user_message")
        or payload.get("message")
        or payload.get("user_message")
        or ""
    )
    # L6.73.1：work 只表示“请求 LLM 填 ActivationForm”，不等于已经需要工具/长链。
    # 旧前端 work payload 里 tools_requested=True 仅表示“允许工具链”，不能让桥接层直接进入工具状态。
    # 真正是否调用工具、是否长链，仍由 ActivationForm 的 tools_requested / execution_depth 决定。
    has_work_payload = isinstance(work_payload, Mapping) and bool(work_payload)
    root_activation_signal = bool(payload.get("activation_requested") or payload.get("tools_requested") or payload.get("long_chain_requested"))
    if selected_mode == "chat" and not root_activation_signal:
        activation_signal = False
        explicit_tool_signal = False
        explicit_long_chain_signal = False
    elif has_work_payload:
        activation_signal = bool(
            work_payload.get("activation_requested")
            or work_payload.get("tools_requested")
            or work_payload.get("long_chain_requested")
        )
        # Frontend two-mode contract may set tools_requested=True for work. Treat it as
        # pre-activation permission only when llm_fills_activation_form=True.
        pre_activation_only = bool(work_payload.get("llm_fills_activation_form", True))
        explicit_long_chain_signal = bool(work_payload.get("long_chain_requested"))
        explicit_tool_signal = (bool(work_payload.get("tools_requested")) and not pre_activation_only) or explicit_long_chain_signal
    else:
        activation_signal = bool(payload.get("activation_requested") or payload.get("tools_requested") or payload.get("long_chain_requested"))
        explicit_long_chain_signal = bool(payload.get("long_chain_requested"))
        explicit_tool_signal = bool(payload.get("tools_requested")) or explicit_long_chain_signal
    activation_requested = bool(selected_mode == "work" or activation_signal)
    mode = "work" if activation_requested else "chat"
    task_mode, planner_mode, output_contract = WORK_MODE_TO_RUNTIME.get(mode, WORK_MODE_TO_RUNTIME["chat"])
    return {
        "frontend_work_mode": mode,
        "task_mode": task_mode,
        "planner_mode": planner_mode,
        "output_contract": output_contract,
        "planner_allowed": bool(activation_requested),
        "tools_requested": bool(explicit_tool_signal),
        "activation_requested": bool(activation_requested),
        "long_chain_requested": bool(explicit_long_chain_signal),
        "file_intent": False,
        "code_intent": False,
        "casual_chat_override": False,
        "llm_fills_activation_form": True,
        "user_message_digest": _digest(str(user_message)),
    }


def _normalize_requested_tool_mode(value: Any, current: str = "runtime_governed") -> str:
    clean = str(value or "").strip().lower().replace("-", "_")
    if clean in {"enabled", "enable", "tools", "tool", "runtime", "runtime_governed", "governed"}:
        return "runtime_governed"
    if clean in {"disabled", "off", "none"}:
        return "disabled"
    return current if current in {"runtime_governed", "disabled"} else "runtime_governed"

def _provider_config_path() -> Path:
    override = os.environ.get("LINYUANZHE_PROVIDER_CONFIG_FILE", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    system = platform.system()
    if system == "Windows":
        base = Path(os.environ.get("APPDATA", "") or (Path.home() / "AppData" / "Roaming"))
        return base / "LinyuanzheDesktop" / "provider_config.json"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "LinyuanzheDesktop" / "provider_config.json"
    base = Path(os.environ.get("XDG_CONFIG_HOME", "") or (Path.home() / ".config"))
    return base / "linyuanzhe_desktop" / "provider_config.json"


def _soul_baseline_path() -> Path:
    override = os.environ.get("TIANGONG_SOUL_BASELINE_PATH", "").strip()
    if override:
        return Path(override).expanduser().resolve()
    return _provider_config_path().with_name("soul_emotion_baseline.json")


def _read_provider_config() -> dict[str, Any]:
    path = _provider_config_path()
    try:
        if not path.exists():
            return {}
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_provider_config(data: Mapping[str, Any]) -> bool:
    path = _provider_config_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": "tiangong.l6_72_37.local_provider_config.v1",
            "provider": str(data.get("provider", "") or ""),
            "model": str(data.get("model", "") or ""),
            "base_url": str(data.get("base_url", "") or ""),
            "api_key": str(data.get("api_key", "") or ""),
            "tool_execution_mode": str(data.get("tool_execution_mode", "runtime_governed") or "runtime_governed"),
            "host_access_scope": _normalize_host_access_scope(data.get("host_access_scope", HOST_ACCESS_SCOPE_DEFAULT)),
            "host_access_root": str(data.get("host_access_root", "") or ""),
            "persona_name": str(data.get("persona_name", "临渊者") or "临渊者"),
            "persona_prompt": str(data.get("persona_prompt", "") or ""),
            "updated_at": datetime.now().isoformat(timespec="seconds"),
            "runtime_owned": True,
            "frontend_raw_secret_visible": False,
        }
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(path, 0o600)
        except Exception as exc:
            _ = exc
        return True
    except Exception:
        return False


def _digest(value: Any, length: int = 16) -> str:
    text = str(value or "")
    if not text:
        return ""
    return hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:length]


def _safe_text(value: Any, limit: int = 2000) -> str:
    text = str(value or "")
    for pattern in SENSITIVE_TEXT_PATTERNS:
        text = pattern.sub("<redacted>", text)
    return text[-limit:]


PROVIDER_ERROR_ACTIONS = {
    "gateway_unreachable": "检查 Tailscale / Base URL / 网关进程后，发送一条短消息复测",
    "auth_failed": "重新填写 API Key 后保存，再发送短消息复测",
    "model_not_found": "确认模型名与账号权限，必要时换成可用模型",
    "provider_timeout": "检查网络与网关负载，或提高 Runtime 超时后重试",
    "provider_rate_limited": "降低频率或更换额度后重试",
    "provider_server_error": "稍后重试；若持续出现，检查网关日志",
    "provider_runtime_error": "查看脱敏错误摘要，修正配置后发送短消息复测",
}


def _classify_provider_error(text: str, returncode: int, elapsed: str) -> str:
    blob = f"{text}\n{returncode}\n{elapsed}".lower()
    if returncode == 124 or "timeout" in blob or "timed out" in blob or "超时" in blob:
        return "provider_timeout"
    if any(x in blob for x in ("401", "403", "unauthorized", "forbidden", "invalid api key", "invalid_api_key", "authentication", "鉴权", "未授权")):
        return "auth_failed"
    if any(x in blob for x in ("404", "model not found", "model_not_found", "unknown model", "模型不存在", "not found")) and "model" in blob:
        return "model_not_found"
    if any(x in blob for x in ("429", "rate limit", "too many requests", "quota", "insufficient_quota", "限流", "额度")):
        return "provider_rate_limited"
    if any(x in blob for x in ("500", "502", "503", "504", "internal server error", "bad gateway", "service unavailable")):
        return "provider_server_error"
    if any(x in blob for x in ("connection refused", "connection reset", "network is unreachable", "name or service not known", "nodename nor servname", "gaierror", "max retries", "ssl", "tls", "cannot connect", "failed to establish")):
        return "gateway_unreachable"
    return "provider_runtime_error"


NON_PROVIDER_ERROR_KINDS = {
    "runtime_task_failed",
    "runtime_subprocess_error",
    "runtime_timeout",
    "tool_permission_error",
    "file_path_error",
    "windows_permission_error",
    "model_output_format_error",
    "runtime_tool_blocked",
    "a5_command_blocked",
    "document_parse_error",
    "physical_commit_verification_failed",
    "file_write_commit_error",
}

EXECUTION_ERROR_LABELS = {
    "runtime_task_failed": "Runtime 工具任务失败",
    "runtime_subprocess_error": "Runtime 子进程错误",
    "runtime_timeout": "Runtime 子进程超时",
    "tool_permission_error": "Tool 权限/工作区边界错误",
    "file_path_error": "文件路径错误",
    "windows_permission_error": "Windows 权限错误",
    "model_output_format_error": "模型输出格式错误",
    "document_parse_error": "文档解析错误",
    "physical_commit_verification_failed": "文件物理落盘验真失败",
    "file_write_commit_error": "文件写入提交错误",
    "a5_command_blocked": "A5 高危命令被阻断",
    "runtime_tool_blocked": "Runtime 工具被阻断",
    "gateway_unreachable": "Provider / API 网络错误",
    "auth_failed": "Provider / API 鉴权错误",
    "model_not_found": "Provider / API 模型名错误",
    "provider_timeout": "Provider / API 超时",
    "provider_rate_limited": "Provider / API 限流",
    "provider_server_error": "Provider / API 服务端错误",
    "provider_runtime_error": "Provider / API 调用错误",
}


def _classify_execution_error(text: str, returncode: int, elapsed: str) -> str:
    blob = f"{text}\n{returncode}\n{elapsed}".lower()
    compact_blob = re.sub(r"[^a-z0-9]+", "", blob)
    # L6.72.44 P0：safecommandrunner: blocked 是 Runtime 工具/边界阻断，
    # 不是模型输出格式错误，也不是 Provider/API 或 Windows 路径权限问题。
    if ("safecommandrunner" in compact_blob or "safe_command_runner" in blob) and "blocked" in blob:
        if "a5" in blob or "unsafe_a5_command" in blob or any(x in blob for x in ("rm -rf", "format ", "mkfs", "reg delete", "powershell -enc")):
            return "a5_command_blocked"
        return "runtime_tool_blocked"
    if any(x in blob for x in ("physical_commit_verification_failed", "物理落盘验真失败", "read-after-write", "落盘验真")):
        return "physical_commit_verification_failed"
    if ("document_parse" in blob or "文档解析" in blob) and any(x in blob for x in ("failed", "error", "exception", "失败", "错误")):
        return "document_parse_error"
    provider_markers = (
        "api key", "api_key", "base url", "base_url", "openai", "deepseek", "chat/completions", "unauthorized", "forbidden",
        "invalid_api_key", "invalid api key", "model not found", "rate limit", "quota", "http 401", "http 403",
        "http 404", "http 429", "模型接口", "provider",
    )
    if any(x in blob for x in provider_markers):
        return _classify_provider_error(text, returncode, elapsed)
    if returncode == 124 or "bridge_hard_timeout" in blob or "backend_timeout" in blob or "timed out" in blob or "超时" in blob:
        return "runtime_timeout"
    if any(x in blob for x in ("workspace_violation", "路径越出工作区", "outside workspace", "越界", "qualitygate blocked", "blocked by quality", "blocked_tool")):
        return "tool_permission_error"
    if "blocked" in blob and any(x in blob for x in ("tool", "runner", "runtime", "code-x", "codex", "工具", "阻断", "拦截")):
        return "runtime_tool_blocked"
    if any(x in blob for x in ("permission denied", "access is denied", "winerror 5", "winerror 1314", "errno 13", "requires elevation", "administrator privileges", "operation requires elevation", "windows_permission_required", "无权限", "权限不足", "拒绝访问", "需要管理员权限", "需要提升权限")):
        return "windows_permission_error"
    if any(x in blob for x in ("path_not_found", "file not found", "no such file", "not a directory", "目录不存在", "文件不存在", "找不到路径", "找不到文件", "winerror 2", "winerror 3")):
        return "file_path_error"
    if any(x in blob for x in ("invalid_json", "json decode", "plan_schema", "tool schema", "模型计划", "输出格式", "model output")):
        return "model_output_format_error"
    if any(x in blob for x in ("traceback", "subprocess", "module not found", "modulenotfounderror", "importerror", "syntaxerror", "runtimeerror")):
        return "runtime_subprocess_error"
    if _looks_like_runtime_task_output(text):
        return "runtime_task_failed"
    return "runtime_subprocess_error"


def _provider_error_action(code: str) -> str:
    return PROVIDER_ERROR_ACTIONS.get(code, PROVIDER_ERROR_ACTIONS["provider_runtime_error"])


class BridgeState:
    def __init__(self, *, backend_mode: str, timeout: float) -> None:
        self.backend_mode = backend_mode
        self.timeout = timeout
        persisted = _read_provider_config()
        raw_provider = (os.environ.get("TIANGONG_PROVIDER") or os.environ.get("LINYUANZHE_PROVIDER") or str(persisted.get("provider", "")) or "deepseek").strip() or "deepseek"
        raw_model = (os.environ.get("TIANGONG_MODEL") or os.environ.get("LINYUANZHE_MODEL") or str(persisted.get("model", "")) or DEEPSEEK_DEFAULT_MODEL).strip() or DEEPSEEK_DEFAULT_MODEL
        raw_provider_base = (os.environ.get("TIANGONG_BASE_URL") or os.environ.get("LINYUANZHE_PROVIDER_BASE") or str(persisted.get("base_url", ""))).strip()
        self.provider, self.model, self.provider_base = _normalize_provider_fields(raw_provider, raw_model, raw_provider_base)
        self.provider_key = (os.environ.get("TIANGONG_API_KEY") or os.environ.get("LINYUANZHE_PROVIDER_KEY") or str(persisted.get("api_key", ""))).strip()
        tool_mode = (os.environ.get("LINYUANZHE_TOOL_MODE") or str(persisted.get("tool_execution_mode", "runtime_governed"))).strip().lower()
        self.tool_execution_mode = tool_mode if tool_mode in {"runtime_governed", "disabled"} else "runtime_governed"
        self.persona_name = _safe_text(os.environ.get("LINYUANZHE_PERSONA_NAME") or persisted.get("persona_name", "临渊者"), 32) or "临渊者"
        self.persona_prompt = _safe_text(os.environ.get("LINYUANZHE_PERSONA_PROMPT") or persisted.get("persona_prompt", ""), 6000)
        raw_access_scope = os.environ.get("LINYUANZHE_HOST_ACCESS_SCOPE") or persisted.get("host_access_scope", HOST_ACCESS_SCOPE_DEFAULT)
        self.host_access_scope = _normalize_host_access_scope(raw_access_scope)
        raw_access_root = os.environ.get("LINYUANZHE_HOST_ACCESS_ROOT") or persisted.get("host_access_root", "")
        self.host_access_root = _resolve_host_access_root(self.host_access_scope, raw_access_root)
        self.provider_config_path = _provider_config_path()
        self.soul_baseline_path = _soul_baseline_path()
        self.provider_config_loaded = bool(persisted)
        self.provider_config_persisted = bool(persisted)
        self.started_at = datetime.now().isoformat(timespec="seconds")
        self.chat_history_file = Path(tempfile.gettempdir()) / f"linyuanzhe_chat_{uuid.uuid4().hex}.json"
        self.chat_count = 0
        self.last_audit_id = "audit_local_bridge_idle"
        self.sessions: list[dict[str, Any]] = []
        self.file_handoffs: list[dict[str, Any]] = []
        self.connector_records: list[dict[str, Any]] = []
        self.last_provider_check_state = "not_tested"
        self.last_provider_error_code = ""
        self.last_provider_error_message = ""
        self.last_provider_next_action = "发送一条短消息完成真实链路联调"
        self.last_provider_elapsed = ""
        self.last_provider_audit_id = ""
        self.last_bridge_diagnostic = ""
        self.last_bridge_error_kind = ""
        self.active_runs: dict[str, dict[str, Any]] = {}
        self.active_processes: dict[str, subprocess.Popen[str]] = {}
        self.active_lock = threading.RLock()
        self.last_run_id = ""
        self.last_run_state = "idle"
        self.last_run_diagnostic = ""
        self.pending_approvals: dict[str, dict[str, Any]] = {}
        self.last_document_context: dict[str, Any] | None = None
        self.last_document_context_id = ""

    def register_run(self, run_id: str, task_id: str, message: str, directives: Mapping[str, Any], audit_id: str) -> None:
        with self.active_lock:
            self.last_run_id = run_id
            self.last_run_state = "accepted"
            self.active_runs[run_id] = {
                "run_id": run_id,
                "task_id": task_id,
                "title": _safe_text(message, 120),
                "status": "accepted",
                "frontend_work_mode": _safe_text(directives.get("frontend_work_mode", "work"), 40),
                "planner_mode": _safe_text(directives.get("planner_mode", "model_suggest"), 40),
                "audit_id": audit_id,
                "created_at": datetime.now().isoformat(timespec="seconds"),
                "heartbeat_count": 0,
            }

    def update_run(self, run_id: str, **fields: Any) -> None:
        if not run_id:
            return
        with self.active_lock:
            rec = self.active_runs.setdefault(run_id, {"run_id": run_id})
            for key, value in fields.items():
                rec[key] = value
            if "status" in fields:
                self.last_run_state = _safe_text(fields.get("status"), 40)
            rec["updated_at"] = datetime.now().isoformat(timespec="seconds")

    def register_process(self, run_id: str, proc: subprocess.Popen[str]) -> None:
        if not run_id:
            return
        with self.active_lock:
            self.active_processes[run_id] = proc
            self.update_run(run_id, status="tool_running", pid=proc.pid)

    def unregister_process(self, run_id: str) -> None:
        if not run_id:
            return
        with self.active_lock:
            self.active_processes.pop(run_id, None)

    def request_stop_active_runs(self, action: str = "stop") -> int:
        killed = 0
        with self.active_lock:
            items = list(self.active_processes.items())
            for run_id, proc in items:
                try:
                    if proc.poll() is None:
                        proc.terminate()
                        killed += 1
                        self.update_run(run_id, status="cancelled", control_action=action, diagnostic_summary=f"用户请求 {action}，本地桥接已终止后端子进程。")
                except Exception as exc:
                    self.update_run(run_id, status="recoverable", diagnostic_summary=f"{action} 子进程终止失败：{_safe_text(exc, 160)}")
        return killed

    def request_reconnect(self) -> int:
        marked = 0
        with self.active_lock:
            for run_id, rec in list(self.active_runs.items()):
                if _safe_text(rec.get("status"), 40) in {"accepted", "tool_running", "recoverable", "failed"}:
                    self.update_run(run_id, status="reconnecting", diagnostic_summary="用户请求重连；本地桥接保留 run_id 并等待前端重新拉取状态。")
                    marked += 1
            if marked:
                self.last_run_state = "reconnecting"
        return marked

    def register_bridge_approval(self, *, run_id: str, audit_id: str, reason: str, impact_scope: str, risk_level: str = "A3") -> dict[str, Any]:
        ticket_id = f"confirm_{_digest(run_id + audit_id + reason)}"
        record = {
            "ticket_id": ticket_id,
            "run_id": run_id,
            "audit_id": audit_id,
            "title": "权限申请审批",
            "source": "Runtime / QualityGate",
            "tool_name": "RuntimeBackendSubprocess",
            "action_summary": _safe_text(reason, 260),
            "impact_scope": _safe_text(impact_scope, 260),
            "risk_level": risk_level,
            "frontend_decision": "",
            "status": "waiting_approval",
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        with self.active_lock:
            self.pending_approvals[ticket_id] = record
        return record

    def submit_bridge_approval(self, ticket_id: str, decision: str) -> dict[str, Any]:
        clean_ticket = _safe_text(ticket_id, 120)
        clean_decision = _safe_text(decision or "submitted", 40)
        with self.active_lock:
            record = self.pending_approvals.get(clean_ticket, {"ticket_id": clean_ticket})
            record["frontend_decision"] = clean_decision
            record["status"] = "approved" if clean_decision in {"approve_once", "approve_session", "approved", "allow"} else "rejected" if clean_decision in {"reject", "rejected", "deny"} else "submitted"
            record["updated_at"] = datetime.now().isoformat(timespec="seconds")
            self.pending_approvals[clean_ticket] = record
            if record.get("run_id"):
                self.update_run(str(record.get("run_id")), approval_status=record["status"], last_approval_decision=clean_decision)
        return dict(record)

    def reset_conversation_history(self) -> None:
        try:
            if self.chat_history_file.exists():
                self.chat_history_file.unlink()
        except Exception:
            pass
        self.chat_history_file = Path(tempfile.gettempdir()) / f"linyuanzhe_chat_{uuid.uuid4().hex}.json"

    @property
    def effective_backend_mode(self) -> str:
        # L6.72.9: cancel user-facing 演示模式. Auto/provider have only two
        # user-visible states: real provider is ready, or model interface is not
        # configured yet.
        if self.provider_key and self.provider_base:
            return "provider"
        return "not_configured"

    def record_provider_check(self, *, ok: bool, answer: str, returncode: int, elapsed: str, audit_id: str) -> None:
        if self.effective_backend_mode != "provider":
            return
        if self.last_bridge_error_kind in NON_PROVIDER_ERROR_KINDS:
            # 工具/工作区/Runtime 子进程失败不是模型服务联调失败，不能把用户带去错误的 Provider 修复路径。
            self.last_provider_elapsed = _safe_text(elapsed, 40)
            self.last_provider_audit_id = _safe_text(audit_id, 80)
            return
        self.last_provider_elapsed = _safe_text(elapsed, 40)
        self.last_provider_audit_id = _safe_text(audit_id, 80)
        if ok:
            self.last_provider_check_state = "passed"
            self.last_provider_error_code = ""
            self.last_provider_error_message = "最近一次真实模型服务联调通过。"
            self.last_provider_next_action = "返回会话继续任务"
            return
        classify_text = "\n".join(x for x in (answer, self.last_bridge_diagnostic) if x)
        code = _classify_provider_error(classify_text, returncode, elapsed)
        self.last_provider_check_state = "failed"
        self.last_provider_error_code = code
        self.last_provider_error_message = _safe_text(answer, 260)
        self.last_provider_next_action = _provider_error_action(code)

    def provider_projection(self) -> dict[str, Any]:
        base_configured = bool(self.provider_base)
        key_configured = bool(self.provider_key)
        missing_fields = []
        if not base_configured:
            missing_fields.append("base_url")
        if not key_configured:
            missing_fields.append("api_key")
        config_file_exists = self.provider_config_path.exists()
        effective_mode = self.effective_backend_mode
        if self.last_provider_check_state == "failed" and effective_mode == "provider":
            state = "error"
            readiness = "provider_check_failed"
            readiness_label = "模型服务联调失败"
            next_action = self.last_provider_next_action
            message = f"配置已保存，但最近一次真实模型服务联调失败：{self.last_provider_error_code or 'provider_runtime_error'}。"
        elif effective_mode == "provider" and not missing_fields:
            state = "ready"
            readiness = "ready"
            readiness_label = "真实模型就绪"
            next_action = "返回会话继续对话" if self.last_provider_check_state == "passed" else "发送一条短消息完成真实链路联调"
            message = "本地桌面桥接后端已就绪；真实模型配置由本机 Runtime 凭证文件托管。"
        else:
            state = "missing_credentials" if missing_fields else "not_configured"
            readiness = "missing_credentials" if missing_fields else "saved_waiting_runtime"
            readiness_label = "缺少模型接口配置" if missing_fields else "配置已保存，等待真实模型链路"
            next_action = "填写服务地址与接口密钥后保存" if missing_fields else "刷新快照或发送一条消息"
            message = "尚未配置模型接口。请进入【设置】页填写服务地址与接口密钥，点击【保存设置并启用真实模型】后即可开始真实对话。"
        return {
            "frontend_contract": "tiangong.l6_71_7.desktop_provider_projection.v1",
            "provider": self.provider,
            "model": self.model,
            "provider_hint": _provider_public_hint(self.provider, self.model, self.provider_base),
            "model_candidates": list(DEEPSEEK_MODEL_FALLBACKS) if _looks_like_deepseek(self.provider, self.model, self.provider_base) else [],
            "provider_model_binding": True,
            "custom_model_allowed": self.provider in {"openai", "openai_compatible", "custom", "local", "deepseek", "qwen", "zhipu"},
            "host_access_scope": self.host_access_scope,
            "host_access_label": _host_access_public_label(self.host_access_scope, self.host_access_root),
            "host_access_root_digest": _digest(str(self.host_access_root)),
            "host_access_root_name": _safe_text(self.host_access_root.name or str(self.host_access_root.anchor or "root"), 80),
            "known_user_folders": _known_folder_projection(self.host_access_root),
            "windows_known_folder_api_supported": True,
            "one_drive_known_folder_move_supported": True,
            "host_access_runtime_only": True,
            "base_url_normalized": bool(self.provider_base),
            "base_url_display": self.provider_base if self.provider_base else "",
            "provider_config_state": state,
            "provider_readiness": readiness,
            "readiness_label": readiness_label,
            "missing_fields": missing_fields,
            "next_action": next_action,
            "config_error_code": self.last_provider_error_code if self.last_provider_check_state == "failed" else "",
            "message": message,
            "audit_id": self.last_provider_audit_id or self.last_audit_id,
            "last_provider_check_state": self.last_provider_check_state,
            "last_provider_error_code": self.last_provider_error_code,
            "last_provider_error_message": self.last_provider_error_message,
            "last_bridge_diagnostic_digest": _digest(self.last_bridge_diagnostic) if self.last_bridge_diagnostic else "",
            "last_bridge_error_kind": self.last_bridge_error_kind,
            "last_provider_next_action": self.last_provider_next_action,
            "last_provider_elapsed": self.last_provider_elapsed,
            "last_provider_audit_id": self.last_provider_audit_id,
            "planner_mode": "rule_only",
            "tool_execution_mode": self.tool_execution_mode,
            "host_access_root": str(self.host_access_root) if self.host_access_scope == "custom_root" else "",
            "persona_name": self.persona_name,
            "persona_digest": _digest(self.persona_prompt) if self.persona_prompt else "",
            "soul_style_contract": "tiangong.l6_72_37.soul_longterm_style_sovereignty.v1",
            "soul_baseline_contract": "tiangong.l6_72_37.soul_emotion_baseline_state.v1",
            "soul_baseline_persisted": self.soul_baseline_path.exists(),
            "soul_baseline_digest": _digest(str(self.soul_baseline_path)),
            "style_source": "soul_only",
            "longterm_style_source": "soul_text_plus_soul_style_model_state_only",
            "non_soul_style_influence_allowed": False,
            "stream": True,
            "api_key_configured": key_configured,
            "api_key_digest": _digest(self.provider_key) if key_configured else "",
            "base_url_configured": base_configured,
            "base_url_digest": _digest(self.provider_base) if base_configured else "",
            "raw_base_url_persisted": True,
            "runtime_credential_persisted": bool(self.provider_config_persisted),
            "runtime_credential_store_digest": _digest(str(self.provider_config_path)) if (key_configured or base_configured) else "",
            "config_file_exists": config_file_exists,
            "config_file_state": "exists" if config_file_exists else "missing",
            "config_location_hint": "system_user_config_dir/LinyuanzheDesktop/provider_config.json",
            "config_path_digest": _digest(str(self.provider_config_path)),
            "local_bridge_can_persist": True,
            "raw_secret_visible_to_frontend": False,
            "local_desktop_bridge": True,
            "requested_backend_mode": self.backend_mode if self.backend_mode in {"auto", "provider"} else "auto",
            "effective_backend_mode": effective_mode,
            "official_real_runtime_smoke_target": False,
        }

    def update_provider_from_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        provider = str(payload.get("provider") or self.provider).strip()
        model = str(payload.get("model") or self.model).strip()
        base = str(payload.get("base_url") or payload.get("provider_base") or self.provider_base).strip()
        key = str(payload.get("api_key") or payload.get("provider_key") or self.provider_key).strip()
        tool_mode = str(payload.get("tool_execution_mode") or self.tool_execution_mode or "runtime_governed").strip().lower()
        self.tool_execution_mode = tool_mode if tool_mode in {"runtime_governed", "disabled"} else "runtime_governed"
        self.persona_name = _safe_text(payload.get("persona_name") or self.persona_name or "临渊者", 32) or "临渊者"
        if payload.get("persona_prompt") is not None:
            self.persona_prompt = _safe_text(payload.get("persona_prompt"), 6000)
        requested_scope = _normalize_host_access_scope(payload.get("host_access_scope") or self.host_access_scope)
        requested_root = payload.get("host_access_root") or ""
        self.host_access_scope = requested_scope
        self.host_access_root = _resolve_host_access_root(self.host_access_scope, requested_root)
        self.provider, self.model, self.provider_base = _normalize_provider_fields(provider, model, base)
        # API Key remains masked from the frontend. Base URL is normal Settings
        # configuration and may be echoed as base_url_display while the local
        # Runtime bridge owns persistence across desktop restarts.
        self.provider_key = key
        self.provider_config_persisted = _write_provider_config({
            "provider": self.provider,
            "model": self.model,
            "base_url": self.provider_base,
            "api_key": self.provider_key,
            "tool_execution_mode": self.tool_execution_mode,
            "host_access_scope": self.host_access_scope,
            "host_access_root": str(self.host_access_root) if self.host_access_scope == "custom_root" else "",
            "persona_name": self.persona_name,
            "persona_prompt": self.persona_prompt,
            "soul_style_contract": "tiangong.l6_72_37.soul_longterm_style_sovereignty.v1",
            "soul_baseline_contract": "tiangong.l6_72_37.soul_emotion_baseline_state.v1",
            "soul_baseline_path_digest": _digest(str(self.soul_baseline_path)),
            "style_source": "soul_only",
            "longterm_style_source": "soul_text_plus_soul_style_model_state_only",
            "non_soul_style_influence_allowed": False,
        })
        self.provider_config_loaded = self.provider_config_loaded or self.provider_config_persisted
        self.last_provider_check_state = "not_tested"
        self.last_provider_error_code = ""
        self.last_provider_error_message = ""
        self.last_provider_next_action = "发送一条短消息完成真实链路联调"
        self.last_provider_elapsed = ""
        self.last_provider_audit_id = ""
        self.last_bridge_diagnostic = ""
        self.last_bridge_error_kind = ""
        self.last_audit_id = f"audit_local_provider_{_digest(str(time.time()))}"
        projection = self.provider_projection()
        projection.update({
            "status": "accepted",
            "requires_restart": False,
            "runtime_memory_only": False,
            "runtime_credential_persisted": bool(self.provider_config_persisted),
            "no_frontend_secret_persistence": True,
        })
        return {"payload": projection, **projection}


STATE: BridgeState


def _json_dumps(payload: Mapping[str, Any] | list[Any]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def _safe_filename(value: Any, default: str = "attachment") -> str:
    name = Path(str(value or default).replace("\x00", "")).name.strip() or default
    name = re.sub(r"[<>:\"|?*\r\n]+", "_", name).strip(" .")
    return name[:160] or default


def _path_is_within(child: Path, root: Path) -> bool:
    try:
        child.resolve().relative_to(root.resolve())
        return True
    except Exception:
        return False


def _handoff_inbox_root(state: "BridgeState") -> Path:
    scope = getattr(state, "host_access_scope", HOST_ACCESS_SCOPE_DEFAULT)
    root = getattr(state, "host_access_root", _resolve_host_access_root(scope))
    # Project/custom workspace should receive a local relative inbox.  Full-computer/user-home
    # scopes use the user's home inbox, which remains inside the normal Windows system drive.
    if scope in {"project_workspace", "custom_root"}:
        return root / ".linyuanzhe" / "file_handoffs"
    return Path.home() / ".linyuanzhe" / "file_handoffs"


def _workspace_path_for_runtime(path: Path, state: "BridgeState") -> str:
    root = getattr(state, "host_access_root", _resolve_host_access_root(getattr(state, "host_access_scope", HOST_ACCESS_SCOPE_DEFAULT)))
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return str(path.resolve())


def _materialize_file_handoff(payload: Mapping[str, Any], state: "BridgeState") -> dict[str, Any]:
    """Copy a user-selected local file into a Runtime-readable handoff inbox.

    The frontend may know the selected path, but it must not execute file tools or expose
    raw paths in UI.  The local bridge is the Runtime boundary: it validates and copies the
    file into a governed inbox, then only passes the Runtime-readable path to backend context.
    """
    file_name = _safe_filename(payload.get("file_name", "attachment"))
    src_text = str(payload.get("runtime_handoff_path") or payload.get("local_path") or "").strip()
    result: dict[str, Any] = {"file_name": file_name, "runtime_handoff_path": "", "handoff_status": "metadata_only"}
    if not src_text or src_text == "<runtime-managed-handoff>":
        result["handoff_error"] = "missing_runtime_source_path"
        return result
    try:
        src = Path(src_text).expanduser().resolve()
    except Exception as exc:
        result["handoff_status"] = "failed"
        result["handoff_error"] = f"source_path_invalid:{type(exc).__name__}"
        return result
    try:
        if not src.exists() or not src.is_file():
            result["handoff_status"] = "failed"
            result["handoff_error"] = "source_file_not_found"
            return result
        max_size = 512 * 1024 * 1024
        size = src.stat().st_size
        if size > max_size:
            result["handoff_status"] = "failed"
            result["handoff_error"] = "source_file_too_large"
            return result
        inbox = _handoff_inbox_root(state) / datetime.now().strftime("%Y%m%d") / f"ft_{uuid.uuid4().hex[:10]}"
        inbox.mkdir(parents=True, exist_ok=True)
        target = inbox / file_name
        if target.exists():
            target = inbox / f"{target.stem}_{uuid.uuid4().hex[:6]}{target.suffix}"
        shutil.copy2(src, target)
        runtime_path = _workspace_path_for_runtime(target, state)
        result.update({
            "runtime_handoff_path": runtime_path,
            "handoff_status": "materialized",
            "runtime_path_digest": _digest(runtime_path),
            "source_path_digest": _digest(str(src)),
            "size_bytes": int(size),
        })
        return result
    except Exception as exc:  # noqa: BLE001 - upload endpoint should return Chinese failure, not crash
        result["handoff_status"] = "failed"
        result["handoff_error"] = f"materialize_failed:{type(exc).__name__}"
        return result


def _pythonpath() -> str:
    parts = [str(BACKEND)]
    current = os.environ.get("PYTHONPATH", "")
    if current:
        parts.append(current)
    return os.pathsep.join(parts)


def _redact_output(text: str, state: BridgeState) -> str:
    out = text or ""
    for raw in (state.provider_key, state.provider_base):
        if raw:
            out = out.replace(raw, "<redacted>")
    out = re.sub(r"(?i)Bearer\s+[A-Za-z0-9_\-.]{8,}", "Bearer <redacted>", out)
    out = re.sub(r"(?i)mockkey_[A-Za-z0-9_\-]{8,}", "mockkey_<redacted>", out)
    # The child Runtime may mention a local handoff path; keep the path available
    # inside the prompt, but do not echo raw filesystem locations back to UI.
    out = re.sub(r"[A-Za-z]:\\[^\n\r\t]+", "<local_path_redacted>", out)
    out = re.sub(r"/(?:home|Users|mnt|tmp|var|etc)/[^\n\r\t]+", "<local_path_redacted>", out)
    return out.strip()




def _looks_like_mojibake_or_binary_text(text: str) -> bool:
    value = str(text or "")
    if not value:
        return False
    sample = value[:4000]
    replacement = sample.count("\ufffd") + sample.count("�")
    box_like = sample.count("□") + sample.count("�")
    controls = sum(1 for ch in sample if ord(ch) < 32 and ch not in "\n\r\t")
    if replacement >= 3 or box_like >= 6 or controls >= 3:
        return True
    # Typical escaped/binary-ish payloads dumped from non-text files.
    if re.search(r"(?:\\x[0-9a-fA-F]{2}){4,}|PK\x03\x04|%PDF-|\x00", sample):
        return True
    printable = sum(1 for ch in sample if ch.isprintable() or ch in "\n\r\t")
    return len(sample) >= 120 and printable / max(1, len(sample)) < 0.86


def _tool_output_public_placeholder(kind: str = "read_file") -> str:
    tool = _safe_text(kind, 40) or "工具"
    return (
        f"{tool} 已返回结果，但原始内容包含不可直接展示的二进制/编码异常片段。\n"
        "为避免会话乱码，主会话已隐藏原始输出；诊断/审计仍保留脱敏摘要。\n"
        "如果要读取 Office/PDF/图片/未知编码文件，请使用文档解析能力或先转为 UTF-8 文本。"
    )


def _sanitize_tool_output_for_chat(text: str) -> str:
    value = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    if not value.strip():
        return value
    raw_tool_line = re.compile(
        r"^\s*[-•*]?\s*(readfile|read_file|list_dir|shell|run_shell|cmd|powershell|python3?|pytest|npm|node|cat|dir|ls|rg|grep)\s*[:：]\s*(ok|failed|error|timeout)\s*[|｜]\s*(.*)$",
        re.IGNORECASE,
    )
    kept: list[str] = []
    hidden = 0
    hidden_kind = "工具"
    for line in value.splitlines():
        safe_runner_match = re.match(
            r"^\s*[-•*]?\s*safe_command_runner\s*[:：]\s*(ok|failed|error|timeout)\s*[|｜]\s*(.*)$",
            line,
            re.IGNORECASE,
        )
        if safe_runner_match:
            hidden += 1
            hidden_kind = "safe_command_runner"
            status = (safe_runner_match.group(1) or "").lower()
            tail = safe_runner_match.group(2)
            if status == "ok" and not _looks_like_mojibake_or_binary_text(tail):
                kept.append(_safe_text(tail, 2200))
            elif tail:
                kept.append(_safe_text(tail, 260))
            continue
        if _is_internal_chat_leak_line(line):
            hidden += 1
            continue
        match = raw_tool_line.match(line)
        if match:
            hidden += 1
            hidden_kind = match.group(1)
            status = (match.group(2) or "").lower()
            tail = match.group(3)
            # 失败只保留中文化归因；成功读取文本附件时，把工具行转换成自然语言内容，
            # 不把 ``read_file: ok |`` 这类工具步骤原样写进会话。
            if re.search(r"文件不存在|目录不存在|path_not_found|not found|权限|permission|access is denied", tail, re.IGNORECASE):
                kept.append(_safe_text(tail, 260))
            elif status == "ok" and hidden_kind.lower() in {"read_file", "readfile", "cat"} and not _looks_like_mojibake_or_binary_text(tail):
                kept.append("文件内容：\n" + _safe_text(tail, 2200))
            elif status == "ok" and hidden_kind.lower() in {"list_dir", "dir", "ls"} and not _looks_like_mojibake_or_binary_text(tail):
                kept.append("目录内容：\n" + _safe_text(tail, 1600))
            continue
        if _looks_like_mojibake_or_binary_text(line):
            hidden += 1
            continue
        kept.append(line)
    cleaned = "\n".join(kept).strip()
    if _looks_like_mojibake_or_binary_text(cleaned):
        return _tool_output_public_placeholder(hidden_kind)
    if cleaned:
        return cleaned
    if hidden:
        return _tool_output_public_placeholder(hidden_kind)
    return value

def _runtime_tool_mode(state: BridgeState) -> str:
    return state.tool_execution_mode if state.tool_execution_mode in {"runtime_governed", "disabled"} else "runtime_governed"


def _compose_runtime_message(message: str, state: BridgeState, directives: Mapping[str, Any] | None = None) -> str:
    # L6.72.32：桌面端“全电脑工作”只把访问根语义给 Planner/Runtime，
    # 前端仍不直接读写本机路径；工具 path 仍必须为相对路径并经 WorkspaceGuard。
    base = str(message or "")
    directives = directives or {}
    if not directives.get("tools_requested"):
        return base
    scope = getattr(state, "host_access_scope", HOST_ACCESS_SCOPE_DEFAULT)
    root = getattr(state, "host_access_root", _resolve_host_access_root(scope))
    hint = _host_access_context_hint(scope, root)
    return base + "\n\n" + hint



INTERNAL_CHAT_LEAK_MARKERS = (
    "runstate=", "run_state=", "run_status=", "RuntimeBackendSubprocess",
    "safecommandrunner", "safe_command_runner", "safeCommandRunner",
    "buildshellsystemmount", "build_shell_system_mount", "return_analysis", "return_code",
    "model_output_shape", "plan_schema", "planner_mode", "tool_execution_mode",
    "adaptiveworkloop", "repaircontext", "repair_context", "failedwith_resume",
    "audit_", "local_envelope", "Runtime 子进程", "原始工具输出",
    "stderr", "stdout", "diagnostic", "debug", "traceback",
)

INTERNAL_CHAT_LEAK_PATTERNS = (
    re.compile(r"^\s*[-•*]?\s*(?:工具|Tool)\s*[:：]\s*(?:RuntimeBackendSubprocess|safe_?command_?runner|BuildShellSystemMount)\b", re.IGNORECASE),
    re.compile(r"\b(?:runstate|run_state|run_status|planner_mode|tool_execution_mode)\s*=", re.IGNORECASE),
    re.compile(r"\b(?:safecommandrunner|safe_command_runner|safeCommandRunner|buildshellsystemmount|build_shell_system_mount)\b", re.IGNORECASE),
    re.compile(r"^\s*[-•*]?\s*(?:stdout|stderr|raw_result|raw output|trace|debug|diagnostic)\s*[:：]", re.IGNORECASE),
    re.compile(r"^\s*[\[【]?(?:deterministic_fallback|adaptiveworkloopv1|工作链|计划器)[\]】]?", re.IGNORECASE),
    re.compile(r"^\s*(?:repaircontext|repair_context)\s*=", re.IGNORECASE),
)


def _is_internal_chat_leak_line(value: Any) -> bool:
    line = str(value or "").strip()
    if not line:
        return False
    lowered = line.lower()
    if any(marker.lower() in lowered for marker in INTERNAL_CHAT_LEAK_MARKERS):
        return True
    return any(pattern.search(line) for pattern in INTERNAL_CHAT_LEAK_PATTERNS)


def _strip_virtual_return_prefix(line: str) -> str:
    stripped = line.strip()
    # Runtime 虚拟返回工具属于审计/归因通道，不应原样暴露到聊天气泡。
    stripped = re.sub(
        r"^[-•]?\s*(?:return_analysis|return_code|model_chat)\s*[:：]\s*(?:ok|pass|success|succeeded)?\s*[|｜:：-]?\s*",
        "",
        stripped,
        flags=re.IGNORECASE,
    )
    return stripped


def _clean_user_facing_answer(text: str, user_message: str = "") -> str:
    raw_answer = str(text or "")
    casual = _is_casual_chat_message(user_message)
    if casual and re.search(r"return_analysis|User message appears incomplete|Awaiting complete task description|runstate=|safecommandrunner|RuntimeBackendSubprocess", raw_answer, re.IGNORECASE):
        return "在。"
    out = _sanitize_tool_output_for_chat(raw_answer)
    patterns = (
        r"[【\[]运行链[】\]]\s*未生成可执行计划[，,；;]\s*将(?:回退|退回)到普通模型对话[。.]?\s*",
        r"运行链[，,；;]\s*未生成可执行计划[，,；;]\s*将(?:回退|退回)到普通模型对话[。.]?\s*",
    )
    for pattern in patterns:
        out = re.sub(pattern, "", out)
    if casual and re.search(r"return_analysis|User message appears incomplete|Awaiting complete task description|runstate=|safecommandrunner|RuntimeBackendSubprocess", out, re.IGNORECASE):
        return "在。"
    internal_prefixes = (
        "- synthesize_experience_candidates:",
        "- queue_skill_candidates:",
        "- queue_tool_production_requests:",
        "- build_execution_exoskeleton:",
    )
    drop_prefixes = ("[计划器]", "【计划器】", "[运行链]", "【运行链】", "[长链]", "【长链】")
    drop_contains = (
        "Runtime is live and ready",
        "Affective state:",
        "Lifecycle, memory",
        "Awaiting user directive",
        "User message appears incomplete",
    )
    kept: list[str] = []
    removed_internal = 0
    for line in out.splitlines():
        stripped = line.strip()
        if not stripped:
            kept.append(line)
            continue
        if _is_internal_chat_leak_line(stripped):
            removed_internal += 1
            continue
        cleaned_line = _strip_virtual_return_prefix(stripped)
        if not cleaned_line:
            continue
        if stripped.startswith(internal_prefixes) or stripped.startswith(drop_prefixes):
            removed_internal += 1
            continue
        if any(marker.lower() in cleaned_line.lower() for marker in drop_contains):
            removed_internal += 1
            continue
        kept.append(cleaned_line if cleaned_line != stripped else line)
    out = "\n".join(kept).strip()
    if not out:
        if casual or removed_internal:
            return "刚刚有内部诊断信息被挡在显示层了。现在按普通聊天继续。"
        return "已收到。"
    return out



def _looks_like_runtime_task_output(text: str) -> bool:
    blob = str(text or "").lower()
    if not blob.strip():
        return False
    provider_markers = (
        "api key", "base url", "http 401", "http 403", "http 404", "http 429", "model not found",
        "unauthorized", "forbidden", "invalid api", "模型请求超时", "网络连接失败", "模型接口", "provider",
    )
    runtime_markers = (
        "[计划器]", "【计划器】", "workspace_violation", "路径越出工作区", "工具", "产物", "执行", "扫描", "目录", "文件", "blocked", "failed", "ok",
    )
    return any(marker.lower() in blob for marker in runtime_markers) and not any(marker.lower() in blob for marker in provider_markers)


def _format_runtime_task_failure(stdout_text: str, state: BridgeState, *, error_kind: str = "runtime_task_failed") -> str:
    visible = _clean_user_facing_answer(stdout_text or "", "")
    scope = getattr(state, "host_access_scope", HOST_ACCESS_SCOPE_DEFAULT)
    root = getattr(state, "host_access_root", _resolve_host_access_root(scope))
    scope_label = _host_access_public_label(scope, root)
    if not visible or visible == "已收到。":
        visible = "任务执行链返回失败，但没有生成可展示正文。"
    label = EXECUTION_ERROR_LABELS.get(error_kind, "Runtime 执行错误")
    lowered_visible = visible.lower()
    if error_kind == "file_path_error" and any(x in lowered_visible for x in ("runtime_local_path", "文件交接", "file_handoff", "附件")):
        next_action = "上传文件交接路径不可读；请重新选择文件上传，Runtime 会先复制到本地交接区，再用交接区路径读取。"
    elif error_kind == "runtime_tool_blocked":
        next_action = "Runtime/Code-X 工具已被安全规则阻断；如果是 docx/pdf/xlsx/pptx 文档读取，应走 document_parse，不要检查 Provider，也不要用 shell/read_file 硬读二进制。"
    elif error_kind == "a5_command_blocked":
        next_action = "命中 A5 高危命令边界；请改成只读解析、受控补丁或审批流程后重试。"
    elif error_kind == "document_parse_error":
        next_action = "文档解析失败已作为工具诊断处理；检查文件是否存在、格式是否受支持、解析依赖是否可用。这不是 Provider/API 问题。"
    elif error_kind in {"physical_commit_verification_failed", "file_write_commit_error"}:
        next_action = "写入工具没有通过真实落盘验真，不能按成功处理；请检查目标 known-folder relative_path、OneDrive 同步状态、磁盘权限/占用，并重试。"
    elif scope != "system_drive":
        next_action = "如要处理桌面/下载/全电脑文件，请在【设置】页把“电脑访问范围”设为“全电脑/系统盘”，再重试。"
    else:
        next_action = "当前已是全电脑/系统盘范围；请检查目标路径是否真实存在、是否被 Windows 权限拦截，或改成更明确的相对路径后重试。"
    return (
        f"{visible}\n\n"
        f"[错误分类] {label}。\n"
        f"[诊断] 已记录脱敏 Runtime 诊断；stderr 不会原样进入用户气泡。\n"
        f"[执行范围] 当前为：{scope_label}。\n"
        f"[下一步] {next_action}"
    )

_DOCUMENT_REQUEST_EXTENSIONS = {
    ".txt", ".md", ".markdown", ".csv", ".json", ".html", ".htm", ".py", ".js", ".ts", ".tsx", ".jsx", ".css",
    ".java", ".cpp", ".c", ".h", ".hpp", ".go", ".rs", ".rb", ".php", ".sql", ".yaml", ".yml", ".toml", ".xml",
    ".docx", ".pdf", ".xlsx", ".xlsm", ".pptx",
}
_DOCUMENT_READ_VERB_RE = re.compile(
    r"(读|读取|打开|查看|看一下|帮我看|帮我读|帮我总结|总结|分析|解析|内容|read|open|view|summari[sz]e|parse|inspect)",
    re.IGNORECASE,
)
_DOCUMENT_PATH_RE = re.compile(
    r"(?P<path>[A-Za-z]:[^\n，。；;]+?\.(?:txt|md|markdown|csv|json|html?|py|js|ts|tsx|jsx|css|java|cpp|c|h|hpp|go|rs|rb|php|sql|ya?ml|toml|xml|docx|pdf|xlsx|xlsm|pptx)|[~./\\]?[^\s，。；;《》\"'“”]+?\.(?:txt|md|markdown|csv|json|html?|py|js|ts|tsx|jsx|css|java|cpp|c|h|hpp|go|rs|rb|php|sql|ya?ml|toml|xml|docx|pdf|xlsx|xlsm|pptx))",
    re.IGNORECASE,
)
_QUOTED_DOCUMENT_PATH_RE = re.compile(
    r"[《<\"'“](?P<path>[^》>\"'”]+?\.(?:txt|md|markdown|csv|json|html?|py|js|ts|tsx|jsx|css|java|cpp|c|h|hpp|go|rs|rb|php|sql|ya?ml|toml|xml|docx|pdf|xlsx|xlsm|pptx))[》>\"'”]",
    re.IGNORECASE,
)
_FOLDER_ALIAS_RE = (
    ("desktop", re.compile(r"桌面|desktop", re.IGNORECASE)),
    ("downloads", re.compile(r"下载|downloads?", re.IGNORECASE)),
    ("documents", re.compile(r"我的文档|文档|documents?|my documents", re.IGNORECASE)),
)


def _document_request_folder_kind(message: str) -> str:
    for kind, pattern in _FOLDER_ALIAS_RE:
        if pattern.search(message or ""):
            return kind
    return ""


def _document_candidate_paths(token: str, message: str, state: BridgeState) -> list[Path]:
    token = str(token or "").strip().strip("'\"“”《》<>，,。.;；")
    if not token:
        return []
    root = getattr(state, "host_access_root", _resolve_host_access_root(getattr(state, "host_access_scope", HOST_ACCESS_SCOPE_DEFAULT)))
    token_path = Path(token).expanduser()
    kind = _document_request_folder_kind(message)
    candidates: list[Path] = []
    has_path_hint = bool(re.search(r"[\\/:]", token) or token.startswith("~") or token.startswith("."))
    if has_path_hint:
        candidates.append(token_path if token_path.is_absolute() else root / token_path)
    else:
        if kind:
            candidates.append(_known_user_folder(kind) / token)
        candidates.append(root / token)
        for fallback_kind in ("desktop", "downloads", "documents"):
            if fallback_kind != kind:
                candidates.append(_known_user_folder(fallback_kind) / token)
    return _dedupe_path_candidates(candidates)


def _document_path_within_access(candidate: Path, state: BridgeState) -> bool:
    try:
        root = getattr(state, "host_access_root", _resolve_host_access_root(getattr(state, "host_access_scope", HOST_ACCESS_SCOPE_DEFAULT))).resolve()
        resolved = candidate.expanduser().resolve(strict=False)
        resolved.relative_to(root)
        return True
    except Exception:
        return False


def _extract_document_request_path(message: str, state: BridgeState) -> Path | None:
    msg = str(message or "")
    if not msg or not _DOCUMENT_READ_VERB_RE.search(msg):
        return None
    tokens: list[str] = []
    for match in _QUOTED_DOCUMENT_PATH_RE.finditer(msg):
        tokens.append(match.group("path"))
    for match in _DOCUMENT_PATH_RE.finditer(msg):
        tokens.append(match.group("path"))
    for token in _unique(tokens):
        suffix = Path(token).suffix.lower()
        should_route = suffix in _DOCUMENT_REQUEST_EXTENSIONS
        if _should_route_to_document_parse is not None:
            try:
                should_route = bool(_should_route_to_document_parse(token))
            except Exception:
                should_route = suffix in _DOCUMENT_REQUEST_EXTENSIONS
        if not should_route:
            continue
        for candidate in _document_candidate_paths(token, msg, state):
            if _document_path_within_access(candidate, state):
                return candidate
    return None


def _maybe_parse_document_request(message: str, state: BridgeState) -> tuple[str, int, str] | None:
    if _document_parse_document is None:
        return None
    candidate = _extract_document_request_path(message, state)
    if candidate is None:
        return None
    try:
        result = _document_parse_document(candidate, max_chars=8000)
    except Exception as exc:
        state.last_bridge_error_kind = "document_parse_exception"
        state.last_bridge_diagnostic = f"document_parse_exception: {_safe_text(exc, 260)}"
        return (
            "【文档解析】\n"
            f"- 文件：{candidate.name}\n"
            f"- 路径摘要：{_digest(str(candidate))}\n"
            "- 结果：解析失败，但不会按 Provider/API 错误处理。\n"
            f"- 诊断：{_safe_text(exc, 180)}",
            0,
            "document_parse_exception",
        )
    if _document_save_context is not None:
        try:
            ctx, result = _document_save_context(BACKEND, result)
            state.last_document_context = ctx
            state.last_document_context_id = _safe_text(ctx.get("document_id"), 100)
        except Exception as exc:
            state.last_bridge_diagnostic = f"document_context_save_warning: {_safe_text(exc, 200)}"
    state.last_bridge_error_kind = ""
    state.last_bridge_diagnostic = _safe_text(result.get("diagnostic") or result.get("status") or "document_parse", 400)
    summary = _safe_text(result.get("human_readable_summary") or "文档解析完成，但未生成摘要。", 4000)
    return (summary, 0, _safe_text(result.get("parse_method") or "document_parse", 80))




_DOCUMENT_FOLLOWUP_RE = re.compile(r"刚才|上面|这份|该文档|这个文档|文档里|里面|引用|片段|页|工作表|sheet|幻灯片|slide|导出|保存|修改|改写|修订|润色|重写|替换|有没有|哪些|找|查", re.IGNORECASE)
_DOCUMENT_EXPORT_RE = re.compile(r"导出|保存|生成.*(?:md|txt|json|摘要)|export|save", re.IGNORECASE)
_DOCUMENT_REWRITE_RE = re.compile(r"修改|改写|修订|润色|重写|替换|修改计划|rewrite|revise|edit", re.IGNORECASE)


def _maybe_answer_document_followup(message: str, state: BridgeState) -> tuple[str, int, str] | None:
    ctx = getattr(state, "last_document_context", None)
    if not isinstance(ctx, dict) or not _DOCUMENT_FOLLOWUP_RE.search(message or ""):
        return None
    if _DOCUMENT_EXPORT_RE.search(message or ""):
        document_id = _safe_text(ctx.get("document_id"), 100)
        return (
            "【文档导出】\n"
            f"- 文档 ID：{document_id}\n"
            "- 当前处于纯聊天表面，未直接写文件。\n"
            "- 如需真实导出，请切换工作模式后发送：导出刚才文档摘要为 md/txt/json。\n"
            "- 边界：导出写入必须走 Runtime / QualityGate / Audit，不由聊天表面静默执行。",
            0,
            "document_export_requires_work_mode",
        )
    if _DOCUMENT_REWRITE_RE.search(message or "") and _document_build_rewrite_plan is not None:
        result = _document_build_rewrite_plan(ctx, message)
        return (_safe_text(result.get("answer_summary") or "文档修改计划已生成。", 4000), 0, "document_rewrite_plan")
    if _document_query_context is None:
        return None
    result = _document_query_context(ctx, message, top_k=6)
    return (_safe_text(result.get("answer_summary") or "文档追问完成。", 4000), 0, "document_query")


def _run_backend_subprocess(
    message: str,
    state: BridgeState,
    *,
    model_override: str | None = None,
    base_url_override: str | None = None,
    runtime_directives: Mapping[str, Any] | None = None,
    run_id: str = "",
) -> tuple[str, int, str]:
    if not RUN_AGENT.exists():
        return "后端入口不存在：backend/project/run_agent.py", 1, "missing_backend_entry"
    directives = dict(runtime_directives or _runtime_directives_from_payload({}))
    env = os.environ.copy()
    # Windows 桌面端默认代码页可能不是 UTF-8；子进程 stdout/stderr 若写中文会触发 UnicodeEncodeError。
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8:replace")
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.pop("PYTHONSTARTUP", None)
    env["PYTHONPATH"] = _pythonpath()
    env["TIANGONG_ENTRY_CHANNEL"] = "desktop_gui"
    env["TIANGONG_TASK_MODE"] = _safe_text(directives.get("task_mode", "ordinary_chat"), 40)
    # L6.72.51：工具是否真正执行由 LLM ActivationForm + Runtime 校验决定；
    # Bridge 不再因为前端是 chat 就把底层工具总线禁掉，否则 LLM 无法自主升级 work。
    runtime_tool_mode = _runtime_tool_mode(state)
    env["TIANGONG_TOOL_MODE"] = runtime_tool_mode
    env["TIANGONG_PROVIDER_READY"] = "1" if state.effective_backend_mode == "provider" else "0"
    env["TIANGONG_SOUL_NAME"] = _safe_text(state.persona_name, 32) or "临渊者"
    env["TIANGONG_SOUL_PROMPT"] = _safe_text(state.persona_prompt, 6000)
    env["TIANGONG_SOUL_BASELINE_PATH"] = str(getattr(state, "soul_baseline_path", _soul_baseline_path()))
    env["TIANGONG_STYLE_SOURCE"] = "soul_only"
    env["TIANGONG_SOUL_STYLE_SOVEREIGNTY"] = "1"
    env.pop("TIANGONG_RESPONSE_STYLE", None)
    env.pop("TIANGONG_LANGUAGE_POLICY", None)
    env["TIANGONG_PLANNER_MODE"] = _safe_text(directives.get("planner_mode") or os.environ.get("LINYUANZHE_PLANNER_MODE", "rule_only"), 40)
    env["TIANGONG_OUTPUT_CONTRACT"] = _safe_text(directives.get("output_contract", "normal_chat"), 40)
    env["LINYUANZHE_FRONTEND_WORK_MODE"] = _safe_text(directives.get("frontend_work_mode", "chat"), 40)
    env["LINYUANZHE_PLANNER_ALLOWED"] = "1" if directives.get("planner_allowed") else "0"
    env["LINYUANZHE_TOOLS_REQUESTED"] = "1" if directives.get("tools_requested") else "0"
    env["LINYUANZHE_LONG_CHAIN_REQUESTED"] = "1" if directives.get("long_chain_requested") else "0"
    host_scope = getattr(state, "host_access_scope", HOST_ACCESS_SCOPE_DEFAULT)
    host_root = getattr(state, "host_access_root", _resolve_host_access_root(host_scope))
    # Q18: the governed tool workspace can legitimately be a broad host root
    # such as "/" (system_drive on Linux/macOS) or a user-selected directory.
    # Runtime ledgers / prompt trace must not be written into that host root:
    # "/" can be read-only and user file trees should not receive .linyuanzhe
    # state just because the desktop bridge listed a folder.
    state_root = Path(tempfile.gettempdir()) / "linyuanzhe_desktop_runtime_state" / _digest(str(host_root))
    env["LINYUANZHE_STATE_DIR"] = str(state_root)
    env["TIANGONG_STATE_DIR"] = str(state_root)
    env["TIANGONG_PROMPT_TRACE_FILE"] = str(state_root / "prompt_trace" / "prompt_trace.jsonl")
    env["TIANGONG_PROMPT_TUNER_FILE"] = str(state_root / "prompt_trace" / "prompt_tuning_state.json")
    env["LINYUANZHE_HOST_ACCESS_SCOPE"] = host_scope
    env["LINYUANZHE_HOST_ACCESS_ROOT_DIGEST"] = _digest(str(host_root))
    # L6.72.47：把桌面/下载/文档的真实相对路径作为本地子进程 env 注入。
    # Runtime adapters 只用它做 path 参数归一，仍由 WorkspaceGuard 校验是否在 --workspace 内。
    known_projection = _known_folder_projection(host_root)
    for env_key, projection_key in (
        ("LINYUANZHE_DESKTOP_RELATIVE_PATH", "desktop_relative_path"),
        ("LINYUANZHE_DOWNLOADS_RELATIVE_PATH", "downloads_relative_path"),
        ("LINYUANZHE_DOCUMENTS_RELATIVE_PATH", "documents_relative_path"),
    ):
        projection_value = str(known_projection.get(projection_key, "") or "")
        if projection_value and not projection_value.startswith("<"):
            env[env_key] = projection_value
        else:
            env.pop(env_key, None)
    runtime_message = _compose_runtime_message(message, state, directives)
    cmd = [
        sys.executable,
        "-S",
        str(RUN_AGENT),
        "--once",
        runtime_message,
        "--workspace",
        str(host_root),
        "--tool-mode",
        runtime_tool_mode,
        "--planner-mode",
        _safe_text(directives.get("planner_mode") or os.environ.get("LINYUANZHE_PLANNER_MODE", "rule_only"), 40),
    ]
    if state.effective_backend_mode != "provider" and not directives.get("activation_requested"):
        return (
            "尚未配置模型接口。请进入【设置】页填写服务地址与接口密钥，点击【保存设置并启用真实模型】后即可开始真实对话。",
            0,
            "provider_not_configured",
        )
    if state.effective_backend_mode == "provider":
        env["TIANGONG_PROVIDER"] = state.provider
        env["TIANGONG_MODEL"] = model_override or state.model
        env["TIANGONG_BASE_URL"] = base_url_override or state.provider_base
        env["TIANGONG_API_KEY"] = state.provider_key
    else:
        env.pop("TIANGONG_API_KEY", None)
        env.pop("LINYUANZHE_PROVIDER_KEY", None)
    env["TIANGONG_CONVERSATION_FILE"] = str(state.chat_history_file)
    env["LINYUANZHE_DESKTOP_BRIDGE"] = "1"
    env["LINYUANZHE_PERSONA_NAME"] = _safe_text(state.persona_name, 32) or "临渊者"
    env["LINYUANZHE_PERSONA_PROMPT"] = _safe_text(state.persona_prompt, 6000)
    env["LINYUANZHE_STYLE_SOURCE"] = "soul_only"
    if state.file_handoffs:
        recent = state.file_handoffs[-3:]
        attachment_lines = []
        for idx, item in enumerate(recent, start=1):
            path = str(item.get("runtime_handoff_path", "") or "").strip()
            name = _safe_text(item.get("file_name", "attachment"), 160)
            if path:
                attachment_lines.append(f"附件{idx}: {name} | runtime_local_path={path}")
            else:
                attachment_lines.append(f"附件{idx}: {name} | sha256_digest={item.get('sha256_digest', '')}")
        if attachment_lines:
            cmd[cmd.index("--once") + 1] = runtime_message + "\n\n[Runtime本地文件交接]\n" + "\n".join(attachment_lines)
    started = time.time()
    proc: subprocess.Popen[str] | None = None
    base_timeout = max(15, int(state.timeout))
    if directives.get("long_chain_requested"):
        child_timeout = max(base_timeout, 300)
    elif directives.get("activation_requested") or directives.get("tools_requested"):
        child_timeout = max(base_timeout, 120)
    else:
        child_timeout = base_timeout
    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(BACKEND),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        if run_id:
            state.register_process(run_id, proc)
        stdout_raw, stderr_raw = proc.communicate(timeout=child_timeout)
    except subprocess.TimeoutExpired:
        if proc is not None:
            try:
                proc.terminate()
                stdout_raw, stderr_raw = proc.communicate(timeout=3)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
                stdout_raw, stderr_raw = "", ""
        if run_id:
            state.update_run(run_id, status="recoverable", diagnostic_summary="本地后端执行超过超时上限，已终止子进程。")
            state.unregister_process(run_id)
        state.last_bridge_error_kind = "runtime_timeout"
        return "本地后端执行超时。", 124, "backend_timeout"
    finally:
        if run_id:
            state.unregister_process(run_id)
    elapsed = int((time.time() - started) * 1000)
    stdout_text = _redact_output(stdout_raw or "", state).strip()
    stderr_text = _redact_output(stderr_raw or "", state).strip()
    state.last_bridge_diagnostic = ""
    state.last_bridge_error_kind = ""
    if proc.returncode == 0:
        text = stdout_text or "本地后端已返回空响应。"
    else:
        diagnostic = "\n".join(x for x in (stdout_text, stderr_text) if x).strip()
        state.last_bridge_diagnostic = diagnostic
        state.last_bridge_error_kind = _classify_execution_error(diagnostic or stdout_text, int(proc.returncode), f"{elapsed}ms")
        if state.last_bridge_error_kind in NON_PROVIDER_ERROR_KINDS:
            text = _format_runtime_task_failure(stdout_text or diagnostic, state, error_kind=state.last_bridge_error_kind)
        else:
            label = EXECUTION_ERROR_LABELS.get(state.last_bridge_error_kind, "Provider / API 调用错误")
            text = (
                f"本地后端执行失败，returncode={proc.returncode}。\n"
                f"[错误分类] {label}。\n"
                "已记录脱敏诊断；用户回复通道不会展示 stderr/运行链日志。"
                "只有 Provider/API 调用失败才需要检查模型服务配置。"
            )
    return text, int(proc.returncode), f"{elapsed}ms"


def _should_retry_provider_config(answer: str, returncode: int) -> bool:
    if returncode == 0:
        return False
    blob = (answer or "").lower()
    return any(
        marker in blob
        for marker in (
            "base url 或模型名可能错误",
            "model not found",
            "model_not_found",
            "unknown model",
            "http 404",
            " 404",
        )
    )


def _provider_failure_detail(answer: str, state: BridgeState) -> str:
    return (
        f"{answer}\n\n"
        "[Provider诊断]\n"
        f"- provider={_safe_text(state.provider, 40)}\n"
        f"- model={_safe_text(state.model, 80)}\n"
        f"- base_url_configured={bool(state.provider_base)}；base_url_digest={_digest(state.provider_base) if state.provider_base else 'none'}\n"
        f"- hint={_provider_public_hint(state.provider, state.model, state.provider_base)}\n"
        "- 设置页可点击 DeepSeek V4 模板后保存，再发送短消息复测。"
    )


def _run_backend_once(message: str, state: BridgeState, *, runtime_directives: Mapping[str, Any] | None = None, run_id: str = "") -> tuple[str, int, str]:
    # Normalize once more immediately before execution so persisted old configs and
    # hand-edited provider_config.json cannot keep the desktop bridge in a bad route.
    state.provider, state.model, state.provider_base = _normalize_provider_fields(state.provider, state.model, state.provider_base)
    directives = dict(runtime_directives or _runtime_directives_from_payload({}))
    # 沙盘/工作模式下，普通身份/寒暄类对话不能被前端 work 偏好推进工具状态。
    # 没有真实 Provider 时直接走本地安全答复；有 Provider 时仍优先让模型处理。
    if state.effective_backend_mode != "provider" and _is_dialogue_only_message(message):
        state.last_bridge_error_kind = ""
        state.last_bridge_diagnostic = "local_dialogue_only_fallback"
        return _local_dialogue_answer(message, state), 0, "local_dialogue"
    answer, returncode, elapsed = _run_backend_subprocess(message, state, runtime_directives=directives, run_id=run_id)
    answer = _clean_user_facing_answer(answer, message)
    if returncode != 0 and _is_dialogue_only_message(message):
        diagnostic = "\n".join(x for x in (answer, state.last_bridge_diagnostic, state.last_bridge_error_kind) if x).lower()
        if any(marker in diagnostic for marker in ("activationform", "unicodeencodeerror", "provider", "api", "模型接口", "请求编码")):
            state.last_bridge_error_kind = ""
            state.last_bridge_diagnostic = "dialogue_only_activation_failure_fallback"
            return _local_dialogue_answer(message, state), 0, "local_dialogue"
    if returncode == 0 or state.effective_backend_mode != "provider":
        return answer, returncode, elapsed
    if state.last_bridge_error_kind in NON_PROVIDER_ERROR_KINDS:
        return answer, returncode, elapsed
    retry_probe_text = "\n".join(x for x in (answer, state.last_bridge_diagnostic, state.last_bridge_error_kind) if x)
    retry_allowed = _should_retry_provider_config(retry_probe_text, returncode) or state.last_bridge_error_kind in {"model_not_found", "provider_runtime_error"}
    if not (_looks_like_deepseek(state.provider, state.model, state.provider_base) and retry_allowed):
        return _provider_failure_detail(answer, state), returncode, elapsed

    base_candidates = _unique([state.provider_base, DEEPSEEK_OFFICIAL_BASE_URL])
    model_candidates = _unique([state.model, *DEEPSEEK_MODEL_FALLBACKS])
    tried: set[tuple[str, str]] = {(state.provider_base, state.model)}
    failures: list[str] = []
    for base_candidate in base_candidates:
        normalized_base = _normalize_provider_base_url("deepseek", state.model, base_candidate)
        for model_candidate in model_candidates:
            key = (normalized_base, model_candidate)
            if key in tried:
                continue
            tried.add(key)
            retry_answer, retry_code, retry_elapsed = _run_backend_subprocess(
                message,
                state,
                model_override=model_candidate,
                base_url_override=normalized_base,
                runtime_directives=directives,
                run_id=run_id,
            )
            if retry_code == 0:
                state.model = model_candidate
                state.provider_base = normalized_base
                state.provider_config_persisted = _write_provider_config({
                    "provider": state.provider,
                    "model": state.model,
                    "base_url": state.provider_base,
                    "api_key": state.provider_key,
                    "tool_execution_mode": state.tool_execution_mode,
                    "persona_name": state.persona_name,
                    "persona_prompt": state.persona_prompt,
                    "soul_style_contract": "tiangong.l6_72_37.soul_longterm_style_sovereignty.v1",
                    "soul_baseline_contract": "tiangong.l6_72_37.soul_emotion_baseline_state.v1",
                    "soul_baseline_path_digest": _digest(str(state.soul_baseline_path)),
                    "style_source": "soul_only",
                    "longterm_style_source": "soul_text_plus_soul_style_model_state_only",
                    "non_soul_style_influence_allowed": False,
                })
                prefix = (
                    "[Provider自动修正] 已切换到可用候选配置。"
                    f"provider={state.provider}；model={state.model}；"
                    f"base_url_digest={_digest(state.provider_base)}。\n"
                )
                return _clean_user_facing_answer(prefix + retry_answer, message), 0, f"{elapsed}+{retry_elapsed}"
            failures.append(f"{model_candidate}:{retry_code}")

    detail = _provider_failure_detail(answer, state)
    if failures:
        detail += "\n- fallback_tried=" + ",".join(failures[:8])
    return detail, returncode, elapsed


class LinyuanzheBridgeHandler(BaseHTTPRequestHandler):
    server_version = "LinyuanzheLocalDesktopBridge/0.72.32"

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: D401 - stdlib signature
        # Keep stdout clean and avoid accidental request-body logging.
        return

    def _send_json(self, payload: Mapping[str, Any] | list[Any], *, status: int = 200) -> None:
        raw = _json_dumps(payload)
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Linyuanzhe-Bridge-Kind", "local-desktop-bridge")
        self.end_headers()
        self.wfile.write(raw)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0") or "0")
        except ValueError:
            length = 0
        if length <= 0:
            return {}
        raw = self.rfile.read(min(length, 1024 * 1024))
        try:
            parsed = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {"value": parsed}

    def do_GET(self) -> None:  # noqa: N802 - stdlib handler API
        path = self.path.split("?", 1)[0]
        if path == "/health/runtime":
            self._send_json({
                "payload": {
                    "runtime_status": "local_desktop_bridge_ready",
                    "status": "ok",
                    "runtime_kind": "local_desktop_bridge",
                    "official_real_runtime_smoke_target": False,
                    "bridge_version": "FE01 STEP68 / L6.73.8",
                    "backend_entry": "backend/project/run_agent.py",
                    "backend_mode": STATE.effective_backend_mode,
                    "current_task_status": "READY",
                    "current_stage": "本地桥接后端已启动，等待桌面端任务。",
                    "status_bar": {
                        "runtime_status": "local_bridge_ready",
                        "provider_model": STATE.model,
                        "budget_pool": "desktop_local",
                        "budget_used_ratio": "0.00",
                        "gate_status": "A0 local envelope",
                        "audit_id": STATE.last_audit_id,
                        "memory_mode": "frontend_no_direct_write",
                        "tools_allowed": 158 if STATE.tool_execution_mode == "runtime_governed" else 0,
                        "tool_execution_mode": STATE.tool_execution_mode,
                        "latency_ms": 0,
                    },
                }
            })
            return
        if path == "/metadata/product":
            self._send_json({**PRODUCT_IDENTITY, "endpoint": path, "local_desktop_bridge": True})
            return
        if path == "/settings/provider":
            self._send_json(STATE.provider_projection())
            return
        if path == "/workspace/policy":
            self._send_json({
                "workspace_contract": "tiangong.l6_65.workspace_policy.v1",
                "workspace_state": "local_bridge_projection",
                "route_to_runtime_only": True,
                "host_access_scope": STATE.host_access_scope,
                "host_access_label": _host_access_public_label(STATE.host_access_scope, STATE.host_access_root),
                "host_access_root_digest": _digest(str(STATE.host_access_root)),
                "active_workspace_root_digest": _digest(str(STATE.host_access_root)),
                "known_user_folders": _known_folder_projection(STATE.host_access_root),
                "windows_known_folder_api_supported": True,
                "one_drive_known_folder_move_supported": True,
                "windows_protected_roots": sorted(_WINDOWS_PROTECTED_ROOTS),
                "frontend_may_read_paths": False,
                "frontend_may_copy_files": False,
                "frontend_may_write_memory": False,
                "frontend_may_write_audit": False,
                "frontend_may_apply_rollback": False,
                "policy": {
                    "workspace_authorization_required": True,
                    "quality_gate_required": True,
                    "runtime_authority_required": True,
                },
            })
            return
        if path == "/connectors/registry":
            self._send_json({
                "connector_registry_contract": "tiangong.l6_66.connector_registry.v1",
                "connector_registry_state": "local_bridge_projection",
                "connector_registry_projection": {
                    "registry_id_digest": _digest("local-bridge-connector-registry"),
                    "registry_state": "ready",
                    "default_mode": "disabled",
                    "connector_count": len(STATE.connector_records),
                    "enabled_count": 0,
                    "read_only_count": len(STATE.connector_records),
                    "quarantined_count": 0,
                    "pending_review_count": len([x for x in STATE.connector_records if x.get("status") == "accepted"]),
                    "allow_market_install": False,
                    "allow_unsigned_connector": False,
                    "runtime_authority_required": True,
                    "quality_gate_required": True,
                    "workspace_authorization_required": True,
                    "frontend_may_install_connector": False,
                    "frontend_may_execute_connector": False,
                    "frontend_may_store_connector_secret": False,
                },
                "connector_manifests": [
                    {
                        "display_name": rec.get("display_name", ""),
                        "kind": rec.get("kind", "mcp_server"),
                        "status": rec.get("status", "accepted"),
                        "manifest_digest": rec.get("manifest_digest", ""),
                        "trust_level": "unknown",
                        "default_mode": "disabled",
                        "requested_scopes": rec.get("requested_scopes", ["read_public_metadata"]),
                    }
                    for rec in STATE.connector_records[-20:]
                ],
                "connector_registration_records": list(reversed(STATE.connector_records[-20:])),
            })
            return
        if path == "/sessions/list":
            self._send_json({
                "session_manager_contract": "tiangong.l6_67.session_manager.v1",
                "session_manager_state": "local_bridge_ready",
                "task_sessions": list(reversed(STATE.sessions[-20:])),
                "session_stats": {
                    "total": len(STATE.sessions),
                    "running": len([s for s in STATE.sessions if s.get("status") == "running" or s.get("active")]),
                    "waiting_confirmation": len([s for s in STATE.sessions if s.get("status") == "waiting_confirmation" or s.get("waiting_confirmation")]),
                    "blocked": len([s for s in STATE.sessions if s.get("status") == "blocked" or s.get("blocked")]),
                    "recoverable": len([s for s in STATE.sessions if s.get("recoverable")]),
                    "completed": len([s for s in STATE.sessions if s.get("status") == "completed"]),
                    "failed": len([s for s in STATE.sessions if s.get("status") == "failed"]),
                    "queued": len([s for s in STATE.sessions if s.get("status") == "queued"]),
                    "total_count": len(STATE.sessions),
                    "completed_count": len([s for s in STATE.sessions if s.get("status") == "completed"]),
                },
                "session_last_message": "本地桌面桥接 Session 投影已读取。",
            })
            return
        if path in {"/runs/status", "/v1/runs/status"}:
            with STATE.active_lock:
                runs = list(STATE.active_runs.values())[-20:]
            self._send_json({
                "run_workbench_contract": "tiangong.l6_72_32.real_host_execution_acceptance.v1",
                "status": "ok",
                "active_run_id": STATE.last_run_id,
                "last_run_state": STATE.last_run_state,
                "runs": runs,
                "frontend_executes_tools": False,
            })
            return
        if path == "/installer/manifest":
            self._send_json({
                "installer_rc_contract": "tiangong.l6_70_1.desktop_bundle_manifest.v1",
                "installer_manifest": {
                    "version_label": "FE01 STEP68 / L6.73.8 文档解析与任务流程开关修复包",
                    "unique_developer": "于泳翔",
                    "angel_investor": "胖胖龙",
                    "startup_self_check_state": "pass",
                    "rollback_ready": True,
                    "offline_repair_available": True,
                    "final_installer_allowed": False,
                    "windows_installer_artifact_emitted": False,
                    "local_desktop_bundle_ready": True,
                },
                "installer_last_message": "这是解压即用桌面包，不是正式 exe/msi 安装器。",
            })
            return
        if path == "/installer/startup/self-check":
            self._send_json({
                "contract_version": "tiangong.l6_70_1.desktop_startup_self_check.v1",
                "ok": True,
                "checks": [
                    {"check_id": "backend_entry", "name": "后端 run_agent 入口", "status": "pass", "message": str(RUN_AGENT.relative_to(ROOT))},
                    {"check_id": "bridge", "name": "本地桥接服务", "status": "pass", "message": "ready"},
                    {"check_id": "frontend_boundary", "name": "前端边界", "status": "pass", "message": "runtime envelope only"},
                ],
            })
            return
        self._send_json({"error": "not_found", "path": path}, status=404)

    def _begin_sse(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("X-Linyuanzhe-Bridge-Kind", "local-desktop-bridge")
        self.end_headers()

    def _write_sse_event(self, item: Mapping[str, Any]) -> bool:
        try:
            raw = json.dumps(dict(item), ensure_ascii=False)
            self.wfile.write(f"event: {item.get('event','message')}\n".encode("utf-8"))
            self.wfile.write(f"data: {raw}\n\n".encode("utf-8"))
            self.wfile.flush()
            return True
        except (BrokenPipeError, ConnectionResetError, OSError):
            return False

    def _send_sse_events(self, events: list[dict[str, Any]]) -> None:
        self._begin_sse()
        for item in events:
            if not self._write_sse_event(item):
                return
            time.sleep(0.02)

    def do_POST(self) -> None:  # noqa: N802 - stdlib handler API
        path = self.path.split("?", 1)[0]
        payload = self._read_json()
        if path == "/chat/stream-events":
            if payload.get("tool_execution_mode"):
                STATE.tool_execution_mode = _normalize_requested_tool_mode(payload.get("tool_execution_mode"), STATE.tool_execution_mode)
            if payload.get("persona_name"):
                STATE.persona_name = _safe_text(payload.get("persona_name"), 32) or STATE.persona_name
            if payload.get("persona_prompt") is not None:
                STATE.persona_prompt = _safe_text(payload.get("persona_prompt"), 6000)
            runtime_directives = _runtime_directives_from_payload(payload)
            task_flow_requested = bool(runtime_directives.get("long_chain_requested"))
            message = str(
                payload.get("raw_user_text")
                or payload.get("text_raw")
                or payload.get("original_user_message")
                or payload.get("message")
                or payload.get("user_message")
                or ""
            ).strip()
            if "<redacted>" in message.lower():
                candidates = payload.get("host_path_candidates") if isinstance(payload.get("host_path_candidates"), list) else []
                fallback_path = str(payload.get("original_path") or (candidates[0] if candidates else "")).strip()
                if fallback_path and "<redacted>" not in fallback_path.lower():
                    message = fallback_path
                else:
                    message = "path_redaction_leak_detected: 前端显示脱敏值进入了 Runtime 原始参数，已阻断执行。"
                    runtime_directives["long_chain_requested"] = False
                    runtime_directives["tools_requested"] = False
                    runtime_directives["planner_allowed"] = False
            if not message:
                message = "继续"
            STATE.chat_count += 1
            run_id = f"local_run_{uuid.uuid4().hex[:12]}" if task_flow_requested else ""
            task_id = f"local_task_{STATE.chat_count:04d}" if task_flow_requested else ""
            audit_id = f"audit_local_{uuid.uuid4().hex[:10]}"
            STATE.last_audit_id = audit_id
            if task_flow_requested:
                STATE.register_run(run_id, task_id, message, runtime_directives, audit_id)
            now = lambda: datetime.now().isoformat(timespec="seconds")
            seq = 1
            self._begin_sse()

            def emit(event: str, payload_obj: Mapping[str, Any]) -> bool:
                nonlocal seq
                item = {
                    "event": event,
                    "seq": seq,
                    "run_id": run_id,
                    "task_id": task_id,
                    "timestamp": now(),
                    "payload": dict(payload_obj),
                }
                seq += 1
                return self._write_sse_event(item)

            if task_flow_requested:
                if not emit("run_started", {
                    "runtime_status": "active",
                    "provider_model": STATE.model,
                    "backend_mode": STATE.effective_backend_mode,
                    "persona_name": STATE.persona_name,
                    "style_source": "soul_only",
                    "non_soul_style_influence_allowed": False,
                    "tool_execution_mode": STATE.tool_execution_mode,
                    "frontend_work_mode": runtime_directives.get("frontend_work_mode"),
                    "task_mode": runtime_directives.get("task_mode"),
                    "planner_mode": runtime_directives.get("planner_mode"),
                }):
                    return
                if not emit("run_accepted", {
                    "state": "accepted",
                    "phase": "Runtime 已接收任务；任务工作台已建立 run_id/task_id。",
                    "frontend_work_mode": runtime_directives.get("frontend_work_mode"),
                    "planner_mode": runtime_directives.get("planner_mode"),
                    "diagnostic_summary": "submit->accepted 完成，开始规划/执行。",
                }):
                    return
                if not emit("planner_started", {
                    "planner_mode": runtime_directives.get("planner_mode", "rule_only"),
                    "current_stage": "本地桥接已接收任务，正在进入执行链",
                    "frontend_work_mode": runtime_directives.get("frontend_work_mode"),
                }):
                    return
                if runtime_directives.get("tools_requested"):
                    if not emit("planner_plan", {
                        "steps": [
                            {"name": "接收前端工作模式", "status": "ok", "risk_level": "A0"},
                            {"name": "进入 Runtime/Planner/ToolMode", "status": "running", "risk_level": "A0"},
                            {"name": "后端执行并回传结果", "status": "queued", "risk_level": "A0"},
                        ],
                        "frontend_work_mode": runtime_directives.get("frontend_work_mode"),
                    }):
                        return
                if not emit("quality_gate", {
                    "risk_level": "A0",
                    "decision": "allowed",
                    "audit_ref": audit_id,
                    "route_to_runtime_only": True,
                    "quality_gate_required": bool(runtime_directives.get("tools_requested")),
                }):
                    return
                if runtime_directives.get("tools_requested"):
                    STATE.update_run(run_id, status="tool_running", current_tool_name="RuntimeBackendSubprocess")
                    if not emit("tool_started", {
                        "step_id": "local_backend_runtime_task",
                        "tool_name": "RuntimeBackendSubprocess",
                        "status": "running",
                        "audit_ref": audit_id,
                        "frontend_work_mode": runtime_directives.get("frontend_work_mode"),
                    }):
                        return
                    if not emit("tool_progress", {
                        "step_id": "local_backend_runtime_task",
                        "tool_name": "RuntimeBackendSubprocess",
                        "status": "running",
                        "phase": "Runtime 子进程已启动，等待 Planner/ToolMode 返回。",
                        "progress_percent": 45,
                        "audit_ref": audit_id,
                    }):
                        return
            result_box: dict[str, Any] = {}

            def worker() -> None:
                try:
                    # L6.72.51：文档系统不得在 bridge 层用规则抢路由。
                    # 只有 LLM ActivationForm 填 work_type=document 后，后端 Planner 才装配文档工具。
                    result_box["value"] = _run_backend_once(message, STATE, runtime_directives=runtime_directives, run_id=run_id)
                except Exception as exc:  # defensive bridge boundary
                    result_box["value"] = (f"本地桥接执行异常：{_safe_text(exc, 260)}", 1, "bridge_exception")

            t = threading.Thread(target=worker, name="linyuanzhe-local-backend-worker", daemon=True)
            t.start()
            heartbeat_started = time.time()
            heartbeat_interval = 5.0
            hard_deadline = time.time() + (max(300, int(STATE.timeout) + 240) if runtime_directives.get("long_chain_requested") else (max(180, int(STATE.timeout) + 120) if runtime_directives.get("tools_requested") else max(30, int(STATE.timeout) + 60)))
            progress = 45 if runtime_directives.get("tools_requested") else 20
            while t.is_alive():
                t.join(timeout=heartbeat_interval)
                if not t.is_alive():
                    break
                progress = min(85, progress + 3)
                if not task_flow_requested:
                    continue
                elapsed_ms = int((time.time() - heartbeat_started) * 1000)
                STATE.update_run(run_id, status="tool_running", heartbeat_count=STATE.active_runs.get(run_id, {}).get("heartbeat_count", 0) + 1, elapsed_ms=elapsed_ms)
                if not emit("heartbeat", {
                    "status": "RUNNING",
                    "phase": "后端执行中；前端保持长连接，不再因短等待直接超时",
                    "progress_percent": progress,
                    "elapsed_ms": elapsed_ms,
                    "heartbeat": True,
                    "frontend_work_mode": runtime_directives.get("frontend_work_mode"),
                    "task_mode": runtime_directives.get("task_mode"),
                    "current_tool_name": "RuntimeBackendSubprocess",
                }):
                    return
                if runtime_directives.get("tools_requested") and not emit("tool_progress", {
                    "step_id": "local_backend_runtime_task",
                    "tool_name": "RuntimeBackendSubprocess",
                    "status": "running",
                    "phase": "Runtime 子进程仍在执行，保持工作连接。",
                    "progress_percent": progress,
                    "elapsed_ms": elapsed_ms,
                    "audit_ref": audit_id,
                }):
                    return
                if time.time() > hard_deadline:
                    result_box["value"] = ("本地后端执行超过桌面桥接硬上限，已收口为超时。", 124, "bridge_hard_timeout")
                    break
            answer, returncode, elapsed = result_box.get("value", ("本地后端未返回结果。", 1, "missing_worker_result"))
            answer = _safe_text(answer, 4000)
            ok = int(returncode) == 0
            STATE.record_provider_check(ok=ok, answer=answer, returncode=int(returncode), elapsed=str(elapsed), audit_id=audit_id)
            if int(returncode) in {130, -15, -9}:
                terminal_status = "cancelled"
            else:
                terminal_status = "ok" if ok else "failed"
            status = terminal_status
            if task_flow_requested:
                STATE.update_run(run_id, status="completed" if ok else ("cancelled" if terminal_status == "cancelled" else "failed"), diagnostic_summary="后端执行完成" if ok else _safe_text(STATE.last_bridge_diagnostic or answer, 260))
            session = {
                "session_id": run_id,
                "title": _safe_text(message, 80),
                "status": "completed" if ok else "blocked",
                "current_stage": "本地桥接后端执行完成" if ok else "本地桥接后端执行失败",
                "progress_percent": 100 if ok else 70,
                "active": False,
                "blocked": not ok,
                "recoverable": not ok,
                "audit_id": audit_id,
                "tags": ["local_bridge", STATE.effective_backend_mode, str(runtime_directives.get("frontend_work_mode"))],
            }
            if task_flow_requested:
                STATE.sessions.append(session)
            if task_flow_requested and runtime_directives.get("tools_requested"):
                if not emit("tool_progress", {
                    "step_id": "local_backend_runtime_task",
                    "tool_name": "RuntimeBackendSubprocess",
                    "status": status,
                    "phase": "Runtime 子进程执行完成，正在回传结果。" if ok else "Runtime 子进程执行失败，正在回传分类诊断。",
                    "progress_percent": 100 if ok else 70,
                    "error_kind": STATE.last_bridge_error_kind,
                    "audit_ref": audit_id,
                }):
                    return
                if STATE.last_bridge_error_kind in {"tool_permission_error", "windows_permission_error"}:
                    approval = STATE.register_bridge_approval(
                        run_id=run_id,
                        audit_id=audit_id,
                        reason=EXECUTION_ERROR_LABELS.get(STATE.last_bridge_error_kind, "权限边界需要确认"),
                        impact_scope=_safe_text(STATE.last_bridge_diagnostic or answer, 260),
                        risk_level="A4" if STATE.last_bridge_error_kind == "windows_permission_error" else "A3",
                    )
                    STATE.update_run(run_id, status="waiting_approval", pending_ticket_id=approval.get("ticket_id", ""))
                    if not emit("approval_required", {
                        "step_id": "local_backend_runtime_task",
                        "tool_name": "RuntimeBackendSubprocess",
                        "status": "waiting_approval",
                        "ticket_id": approval.get("ticket_id", ""),
                        "title": approval.get("title", "权限申请审批"),
                        "source": approval.get("source", "Runtime / QualityGate"),
                        "action_summary": approval.get("action_summary", "权限边界需要确认"),
                        "impact_scope": approval.get("impact_scope", "未提供影响范围"),
                        "risk_level": approval.get("risk_level", "A3"),
                        "reason": approval.get("action_summary", "权限边界需要确认"),
                        "audit_ref": audit_id,
                        "frontend_executes_tools": False,
                    }):
                        return
                if not emit("tool_result", {
                    "step_id": "local_backend_runtime_task",
                    "tool_name": "RuntimeBackendSubprocess",
                    "status": status,
                    "audit_ref": audit_id,
                    "output_summary": "后端执行完成" if ok else "后端执行失败或超时",
                    "error_kind": STATE.last_bridge_error_kind,
                    "elapsed": elapsed,
                }):
                    return
            visible_answer = _sanitize_tool_output_for_chat(_clean_user_facing_answer(answer, message))
            answer_chunks = [visible_answer[i : i + 360] for i in range(0, len(visible_answer), 360)] or ["本地后端已返回空响应。"]
            for chunk in answer_chunks:
                if not emit("assistant_delta", {"content": chunk, "label": STATE.persona_name}):
                    return
                time.sleep(0.01)
            if task_flow_requested:
                if not emit("audit_event", {"audit_id": audit_id, "event": "local_bridge_backend_once", "status": status, "elapsed": elapsed, "frontend_work_mode": runtime_directives.get("frontend_work_mode")}):
                    return
            if not emit("assistant_final", {"content": "", "status": status, "label": STATE.persona_name}):
                return
            emit("run_terminal", {"status": status, "audit_id": audit_id, "assistant_final_before_terminal": True})
            return
        if path == "/settings/provider":
            self._send_json(STATE.update_provider_from_payload(payload))
            return
        if path in CONTROL_PATHS:
            action = CONTROL_PATHS[path]
            killed = 0
            if action in {"stop", "interrupt"}:
                killed = STATE.request_stop_active_runs(action)
            if action == "reset":
                killed = STATE.request_stop_active_runs(action)
                STATE.reset_conversation_history()
                STATE.chat_count = 0
            reconnected_runs = STATE.request_reconnect() if action == "reconnect" else 0
            self._send_json({
                "control_contract": "tiangong.l6_72_35.runtime_control_windows_native_gui.v1",
                "status": "accepted",
                "action": action,
                "killed_processes": killed,
                "reconnected_runs": reconnected_runs,
                "message": f"{action} 请求已由本地桥接接收；对话历史已按请求复位。" if action == "reset" else (f"重连请求已由本地桥接接收；已标记可续接任务 {reconnected_runs} 个。" if action == "reconnect" else f"{action} 请求已由本地桥接接收；已请求终止活动后端子进程 {killed} 个。"),
                "route_to_runtime_only": True,
                "conversation_history_cleared": action == "reset",
                "last_run_state": STATE.last_run_state,
                "audit_id": f"audit_control_{_digest(str(time.time()))}",
            })
            return
        if path in {"/conversation/clear", "/chat/clear"}:
            STATE.reset_conversation_history()
            STATE.chat_count = 0
            self._send_json({
                "conversation_contract": "tiangong.l6_72_10.desktop_conversation_reset.v1",
                "status": "accepted",
                "message": "桌面端对话历史已清空；审计、记忆和任务记录未删除。",
                "conversation_history_cleared": True,
                "audit_id": f"audit_conversation_clear_{_digest(str(time.time()))}",
            })
            return
        if path == "/confirmations/submit":
            ticket_id = _safe_text(payload.get("ticket_id", ""), 120)
            decision = _safe_text(payload.get("decision", "submitted"), 40)
            approval_record = STATE.submit_bridge_approval(ticket_id, decision)
            self._send_json({
                "confirmation_contract": "tiangong.l6_72_35.action_guard_bridge_closure.v1",
                "status": approval_record.get("status", "submitted"),
                "ticket_id": ticket_id,
                "decision": decision,
                "message": "确认请求已闭环记录到本地桥接信封；正式工具放行仍属于 Runtime/QualityGate，前端不直接执行。",
                "approval_closed": True,
                "frontend_executes_tools": False,
                "route_to_runtime_only": True,
                "audit_id": f"audit_confirm_{_digest(str(time.time()))}",
            })
            return
        if path == "/files/transfer/request":
            # L6.73.6: public JSON payload must not expose raw host paths.
            # The localhost-only bridge may receive the raw path through private
            # request headers and inject it before materialization.
            private_path = self.headers.get("X-Linyuanzhe-Local-Handoff-Path", "")
            private_path_b64 = self.headers.get("X-Linyuanzhe-Local-Handoff-Path-B64", "")
            if private_path_b64 and not private_path:
                try:
                    private_path = base64.urlsafe_b64decode(private_path_b64.encode("ascii")).decode("utf-8", errors="surrogatepass")
                except Exception:
                    private_path = ""
            private_token = self.headers.get("X-Linyuanzhe-Local-Handoff-Token", "")
            if private_path and not payload.get("runtime_handoff_path"):
                payload["runtime_handoff_path"] = private_path
            if private_token and not payload.get("handoff_token"):
                payload["handoff_token"] = private_token
            materialized = _materialize_file_handoff(payload, STATE)
            file_name = _safe_text(materialized.get("file_name") or payload.get("file_name", "attachment"), 160)
            handoff_status = _safe_text(materialized.get("handoff_status", "metadata_only"), 80)
            # 只有真实复制到 Runtime 交接区的附件才算上传成功；
            # 元数据占位不能进入最近附件队列，否则下一轮会按文件名/摘要误读并触发 path_not_found。
            accepted = handoff_status == "materialized"
            record = {
                "transfer_id": f"ft_{_digest(str(time.time()))}",
                "direction": payload.get("direction", "upload"),
                "file_name": file_name,
                "size_bytes": int(materialized.get("size_bytes") or payload.get("size_bytes", 0) or 0),
                "sha256_digest": _digest(payload.get("sha256", "")),
                "mime_type": payload.get("mime_type", "application/octet-stream"),
                "purpose": payload.get("purpose", "user_attachment"),
                "status": "accepted" if accepted else "failed_recoverable",
                "handoff_status": handoff_status,
                "message": (
                    "文件已复制到本地 Runtime 交接区；后续读取会使用交接区路径。"
                    if handoff_status == "materialized"
                    else ("文件元数据已记录，但未收到可读取的本地源路径；请重新选择文件上传。" if handoff_status == "metadata_only" else "文件交接失败；请确认文件存在且没有被系统权限拦截。")
                ),
                "audit_id": f"audit_file_{_digest(str(time.time()))}",
                "route_to_runtime_only": True,
                "no_frontend_path_exposure": True,
                "runtime_path_digest": materialized.get("runtime_path_digest", ""),
                "handoff_error": materialized.get("handoff_error", ""),
            }
            if accepted:
                STATE.file_handoffs.append({**record, "runtime_handoff_path": materialized.get("runtime_handoff_path", "")})
            self._send_json({
                "file_transfer_contract": "tiangong.l6_64.file_transfer_request.v1",
                "status": record["status"],
                "payload": record,
                **record,
            })
            return
        if path == "/workspace/file/authorize":
            record = {
                "authorization_id": f"auth_{_digest(str(time.time()))}",
                "file_name": _safe_text(payload.get("file_name", "workspace_target"), 160),
                "mode": payload.get("mode", "read"),
                "scope": payload.get("scope", "user_selected_file"),
                "purpose": payload.get("purpose", "user_attachment"),
                "status": "accepted",
                "message": "文件授权请求已进入本地运行时桥接；写入/读取仍由运行时工具链执行。",
                "audit_id": f"audit_auth_{_digest(str(time.time()))}",
                "path_digest": payload.get("local_path_digest", ""),
                "runtime_workspace_digest": _digest("local_runtime_workspace"),
                "route_to_runtime_only": True,
                "raw_path_visible": False,
            }
            self._send_json({
                "workspace_contract": "tiangong.l6_65.file_authorization.v1",
                "status": "accepted",
                "payload": record,
                **record,
            })
            return
        if path == "/files/download/claim":
            self._send_json({"status": "accepted", "route_to_runtime_only": True, "download_claim_ref": f"claim_{_digest(str(time.time()))}"})
            return
        if path in {"/connectors/register/request", "/connectors/quarantine/request"}:
            record = {
                "request_id": f"connector_{_digest(str(time.time()))}",
                "display_name": _safe_text(payload.get("display_name", payload.get("name", "未命名连接器")), 160),
                "kind": payload.get("kind", "mcp_server"),
                "status": "accepted",
                "message": "连接器注册请求已进入本地运行时桥接；默认禁用，只读待审。",
                "audit_id": f"audit_connector_{_digest(str(time.time()))}",
                "manifest_digest": payload.get("manifest_digest", _digest(payload)),
                "source_digest": payload.get("source_digest", ""),
                "trust_level": "unknown",
                "default_mode": "disabled",
                "requested_scopes": payload.get("requested_scopes", ["read_public_metadata"]),
                "route_to_runtime_only": True,
                "quarantined": False,
            }
            STATE.connector_records.append(record)
            self._send_json({
                "connector_registry_contract": "tiangong.l6_66.connector_request.v1",
                "status": "accepted",
                "payload": record,
                **record,
            })
            return
        if path == "/sessions/resume":
            self._send_json({"session_manager_contract": "tiangong.l6_67.session_resume.v1", "status": "accepted", "route_to_runtime_only": True, "message": "恢复请求已进入本地桥接信封；请返回会话继续输入，正式恢复由运行时决定。"})
            return
        if path == "/sessions/search":
            query = str(payload.get("query") or "").strip().lower()
            matches = [s for s in STATE.sessions if not query or query in str(s.get("title", "")).lower()]
            self._send_json({"session_manager_contract": "tiangong.l6_67.session_search.v1", "status": "ok", "read_only_projection": True, "task_sessions": list(reversed(matches[-20:]))})
            return
        if path in {"/self-iteration/confirm", "/self_iteration/confirm", "/self-iteration/confirm/request"}:
            self._send_json({
                "self_iteration_contract": "tiangong.l6_42.self_iteration_confirm.v1",
                "status": "accepted",
                "candidate_id": payload.get("candidate_id", ""),
                "decision": payload.get("decision", "confirmed"),
                "route_to_runtime_only": True,
                "no_frontend_self_iteration_apply": True,
                "message": "自我迭代确认已进入本地运行时桥接；不由前端直接合入。",
                "audit_id": f"audit_iter_{_digest(str(time.time()))}",
            })
            return
        if path in {"/installer/update/check", "/installer/repair/request", "/installer/rollback/plan"}:
            self._send_json({"installer_rc_contract": "tiangong.l6_68.installer_request.v1", "status": "dry_run", "route_to_runtime_only": True, "final_installer_allowed": False})
            return
        self._send_json({"error": "not_found", "path": path}, status=404)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="临渊者 FE01 STEP68 / L6.73.8 本地桌面运行时桥接服务")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--backend-mode", choices=["auto", "provider"], default="provider" if os.environ.get("LINYUANZHE_BACKEND_MODE") == "provider" else "auto")
    parser.add_argument("--timeout", type=float, default=float(os.environ.get("LINYUANZHE_BACKEND_TIMEOUT", "900") or 900))
    args = parser.parse_args(argv)

    global STATE
    STATE = BridgeState(backend_mode=args.backend_mode, timeout=args.timeout)
    REPORTS.mkdir(parents=True, exist_ok=True)

    server = ThreadingHTTPServer((args.host, args.port), LinyuanzheBridgeHandler)
    host, port = server.server_address[:2]
    url = f"http://{host}:{port}"
    print(f"LINYUANZHE_LOCAL_RUNTIME_URL={url}", flush=True)
    try:
        server.serve_forever(poll_interval=0.2)
    except KeyboardInterrupt:
        return 130
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
