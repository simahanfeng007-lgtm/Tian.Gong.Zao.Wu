"""L6.72.47 本机已知文件夹路径归一化。

目标：
- 桌面端使用 system_drive/user_home/custom_root 时，模型可能把“桌面”误写成
  ``Users/User/Desktop``、``C:/Users/User/Desktop`` 或 ``Desktop``。
- 这些路径在真实 Windows 上可能不是当前用户的可见桌面，导致“报告写入成功，用户看不到文件”。
- 本模块只做 Desktop/Downloads/Documents 这类已知文件夹别名归一化，不绕过
  WorkspaceGuard、QualityGate 或 RuntimeToolRegistry。
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Mapping


_HOST_HINT_ENV = {
    "desktop": "LINYUANZHE_DESKTOP_RELATIVE_PATH",
    "downloads": "LINYUANZHE_DOWNLOADS_RELATIVE_PATH",
    "documents": "LINYUANZHE_DOCUMENTS_RELATIVE_PATH",
}
_HOST_HINT_KEYS = {
    "desktop": "desktop_relative_path",
    "downloads": "downloads_relative_path",
    "documents": "documents_relative_path",
}
_FOLDER_ALIASES = {
    "desktop": {"desktop", "桌面"},
    "downloads": {"downloads", "download", "下载"},
    "documents": {"documents", "document", "my documents", "文档", "我的文档"},
}


@dataclass(frozen=True)
class HostPathNormalization:
    original_path: str
    normalized_path: str
    changed: bool = False
    folder_kind: str = ""
    reason: str = ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "original_path": self.original_path,
            "normalized_path": self.normalized_path,
            "changed": self.changed,
            "folder_kind": self.folder_kind,
            "reason": self.reason,
        }


def _clean_path_text(value: Any) -> str:
    return str(value or "").strip().strip('"\'“”‘’《》<>').replace("\\", "/")


def _safe_relative_path(value: Any) -> bool:
    text = _clean_path_text(value).strip("/")
    if not text or text.startswith("~") or re.match(r"^[A-Za-z]:", text):
        return False
    parts = [p for p in text.split("/") if p]
    return bool(parts) and ".." not in parts


def _extract_hint_from_text(text: str, hint_key: str) -> str:
    if not text:
        return ""
    match = re.search(rf"(?:^|\n)\s*-?\s*{re.escape(hint_key)}\s*=\s*([^\n\r]+)", text, flags=re.IGNORECASE)
    if not match:
        return ""
    value = _clean_path_text(match.group(1)).strip("/")
    if value.startswith("<") or not _safe_relative_path(value):
        return ""
    return value


def host_known_folder_hints(user_message: str = "") -> dict[str, str]:
    """Return relative Desktop/Downloads/Documents hints exported by the desktop bridge.

    Env vars are authoritative for subprocess tools; prompt hints are fallback for
    direct adapter/unit tests and for older bridge builds.
    """
    hints: dict[str, str] = {}
    for kind, env_key in _HOST_HINT_ENV.items():
        env_value = _clean_path_text(os.environ.get(env_key, "")).strip("/")
        if env_value and _safe_relative_path(env_value):
            hints[kind] = env_value
            continue
        text_value = _extract_hint_from_text(user_message, _HOST_HINT_KEYS[kind])
        if text_value:
            hints[kind] = text_value
    return hints


def _alias_kind(part: str) -> str:
    clean = _clean_path_text(part).strip("/").lower()
    for kind, names in _FOLDER_ALIASES.items():
        if clean in {name.lower() for name in names}:
            return kind
    return ""


def _parts_after_known_folder(path_text: str) -> tuple[str, list[str]]:
    """Detect known-folder alias and return (kind, suffix_parts)."""
    clean = _clean_path_text(path_text).strip()
    if not clean:
        return "", []
    # Drop drive prefix only for alias detection. WorkspaceGuard still validates
    # the final normalized relative path against the real access root.
    clean_no_drive = re.sub(r"^[A-Za-z]:/+", "", clean).lstrip("/")
    parts = [p for p in clean_no_drive.split("/") if p]
    if not parts:
        return "", []

    # Desktop/foo.txt, 桌面/foo.txt, Downloads/foo.txt ...
    first_kind = _alias_kind(parts[0])
    if first_kind:
        return first_kind, parts[1:]

    # Users/<anything>/Desktop/foo.txt is usually a model placeholder for the
    # current user's desktop.  Normalize it to the bridge-projected known folder.
    if len(parts) >= 3 and parts[0].lower() in {"users", "user", "用户"}:
        user_kind = _alias_kind(parts[2])
        if user_kind:
            return user_kind, parts[3:]

    # OneDrive/Desktop/foo.txt or OneDrive/桌面/foo.txt; if the actual hint is
    # OneDrive/桌面, map localized/English folder spellings to that exact hint.
    if len(parts) >= 2 and "onedrive" in parts[0].lower():
        one_kind = _alias_kind(parts[1])
        if one_kind:
            return one_kind, parts[2:]

    return "", []


def normalize_host_known_folder_path(path_value: Any, user_message: str = "") -> HostPathNormalization:
    original = _clean_path_text(path_value)
    if not original:
        return HostPathNormalization(original_path="", normalized_path="")
    hints = host_known_folder_hints(user_message)
    kind, suffix_parts = _parts_after_known_folder(original)
    if not kind or kind not in hints:
        return HostPathNormalization(original_path=original, normalized_path=original)
    base = hints[kind].strip("/")
    suffix = "/".join(part.strip("/") for part in suffix_parts if part.strip("/"))
    normalized = f"{base}/{suffix}" if suffix else base
    if not _safe_relative_path(normalized):
        return HostPathNormalization(original_path=original, normalized_path=original)

    original_rel = re.sub(r"^[A-Za-z]:/+", "", original).lstrip("/").rstrip("/")
    changed = original_rel.lower() != normalized.lower()
    return HostPathNormalization(
        original_path=original,
        normalized_path=normalized,
        changed=changed,
        folder_kind=kind,
        reason="known_folder_alias_to_bridge_relative_path" if changed else "already_bridge_relative_path",
    )


def normalize_argument_path(path_value: Any, user_message: str = "") -> tuple[str, HostPathNormalization]:
    info = normalize_host_known_folder_path(path_value, user_message=user_message)
    return info.normalized_path, info


def normalization_public_data(info: HostPathNormalization) -> dict[str, Any]:
    return info.public_dict() if isinstance(info, HostPathNormalization) else {}
