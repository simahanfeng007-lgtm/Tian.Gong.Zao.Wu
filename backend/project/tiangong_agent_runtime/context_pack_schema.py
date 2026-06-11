"""L6.72.56/L6.72.57 ContextWindowManager 上下文包 schema。"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

SCHEMA_VERSION = "tiangong.l6_72_56.context_window_pack.v1"
PACK_ORDER = (
    "MissionPack",
    "StatePack",
    "EvidencePack",
    "ErrorPack",
    "ToolPack",
    "PlaybookPack",
    "ConstraintPack",
)


def safe_text(value: Any, limit: int = 800) -> str:
    text = redact_text(str(value or "")).replace("\x00", "")
    text = re.sub(r"(?i)\b(raw[_-]?prompt|messages?)\b\s*[:=]\s*([^\s,;]+)", lambda m: f"{m.group(1)}=[redacted]", text)
    return text[: max(1, int(limit))]


def json_safe(value: Any, *, depth: int = 4, string_limit: int = 1200) -> Any:
    if depth <= 0:
        return safe_text(value, 160)
    if value is None or isinstance(value, (bool, int, float)):
        return value
    if isinstance(value, str):
        return safe_text(value, string_limit)
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in list(value.items())[:80]:
            key_text = safe_text(key, 80).lower()
            if key_text in {"api_key", "apikey", "authorization", "token", "secret", "password", "credential", "raw_prompt", "messages"}:
                out[safe_text(key, 80)] = "[redacted]"
            else:
                out[safe_text(key, 80)] = json_safe(item, depth=depth - 1, string_limit=string_limit)
        return out
    if isinstance(value, (list, tuple, set)):
        return [json_safe(item, depth=depth - 1, string_limit=string_limit) for item in list(value)[:120]]
    if hasattr(value, "public_dict"):
        try:
            return json_safe(value.public_dict(), depth=depth - 1, string_limit=string_limit)
        except Exception:  # noqa: BLE001
            return safe_text(value, 240)
    return safe_text(value, 240)


@dataclass(frozen=True)
class ContextPack:
    name: str
    title: str
    priority: int
    payload: dict[str, Any] = field(default_factory=dict)
    max_chars: int = 1200

    def public_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": safe_text(self.title, 120),
            "priority": self.priority,
            "max_chars": int(self.max_chars),
            "payload": json_safe(self.payload, string_limit=min(1200, max(120, int(self.max_chars)))),
        }

    def prompt_text(self) -> str:
        payload = json.dumps(self.public_dict()["payload"], ensure_ascii=False, sort_keys=True)
        text = f"[{self.name} / {self.title}]\n{payload}"
        return safe_text(text, self.max_chars)


@dataclass(frozen=True)
class ContextWindowBundle:
    model_tier: str
    model_role: str
    stage: str
    max_context_chars: int
    packs: tuple[ContextPack, ...] = tuple()
    budget: dict[str, Any] = field(default_factory=dict)
    context_overflow_recovered: bool = False
    notes: tuple[str, ...] = tuple()

    @property
    def bundle_id(self) -> str:
        raw = json.dumps(
            {
                "schema": SCHEMA_VERSION,
                "tier": self.model_tier,
                "role": self.model_role,
                "stage": self.stage,
                "packs": [pack.public_dict() for pack in self.packs],
                "budget": json_safe(self.budget),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return "cwp_" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    @property
    def pack_names(self) -> tuple[str, ...]:
        return tuple(pack.name for pack in self.packs)

    @property
    def total_chars(self) -> int:
        return sum(len(pack.prompt_text()) for pack in self.packs)

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "bundle_id": self.bundle_id,
            "model_tier": self.model_tier,
            "model_role": self.model_role,
            "stage": self.stage,
            "max_context_chars": int(self.max_context_chars),
            "total_chars": self.total_chars,
            "pack_names": list(self.pack_names),
            "packs": [pack.public_dict() for pack in self.packs],
            "budget": json_safe(self.budget),
            "context_overflow_recovered": bool(self.context_overflow_recovered),
            "notes": [safe_text(note, 220) for note in self.notes],
            "storage_boundary": {
                "no_api_key": True,
                "no_raw_prompt": True,
                "no_full_file_content": True,
                "summary_and_refs_only": True,
                "conversation_display": False,
            },
        }

    def prompt_card(self, *, max_chars: int | None = None) -> str:
        limit = max(600, int(max_chars or self.max_context_chars or 2000))
        header = [
            "[ContextWindowManager / L6.72.56 / 上下文裁剪包]",
            f"bundle_id={self.bundle_id}; stage={safe_text(self.stage, 40)}; model_tier={self.model_tier}; model_role={self.model_role}; max_context_chars={limit}",
            "该包只含任务摘要、状态、证据引用、错误摘要、候选工具、playbook 阶段和约束；禁止包含 API Key/raw prompt/完整敏感文件正文。",
        ]
        body: list[str] = []
        for pack in sorted(self.packs, key=lambda item: (item.priority, PACK_ORDER.index(item.name) if item.name in PACK_ORDER else 99)):
            candidate = pack.prompt_text()
            if len("\n\n".join(header + body + [candidate])) <= limit:
                body.append(candidate)
            else:
                remaining = max(0, limit - len("\n\n".join(header + body)) - 20)
                if remaining > 160:
                    body.append(candidate[:remaining] + "\n[truncated_by_context_window_manager]")
                break
        return safe_text("\n\n".join(header + body), limit)

    def compact_for_retry(self, *, reason: str = "context_overflow", max_chars: int = 1800) -> "ContextWindowBundle":
        keep = [pack for pack in self.packs if pack.name in {"MissionPack", "StatePack", "ErrorPack", "ToolPack", "ConstraintPack"}]
        compacted: list[ContextPack] = []
        for pack in keep:
            reduced_payload = json_safe(pack.payload, string_limit=360)
            compacted.append(
                ContextPack(
                    name=pack.name,
                    title=pack.title + " / compact_retry",
                    priority=pack.priority,
                    payload=reduced_payload if isinstance(reduced_payload, dict) else {"summary": reduced_payload},
                    max_chars=max(260, min(pack.max_chars, max_chars // max(1, len(keep)))),
                )
            )
        return ContextWindowBundle(
            model_tier=self.model_tier,
            model_role=self.model_role,
            stage=f"{self.stage}_compact_retry",
            max_context_chars=max_chars,
            packs=tuple(compacted),
            budget={**json_safe(self.budget), "retry_reason": safe_text(reason, 80), "compact_retry": True},
            context_overflow_recovered=True,
            notes=tuple(list(self.notes) + ["context_overflow_compact_retry"]),
        )
