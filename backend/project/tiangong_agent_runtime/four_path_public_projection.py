"""L6.43 四主路径公共投影。

把 Memory / Affective / Lifecycle / Execution/P0 支撑对象统一降噪为
Planner 可消费的摘要、ref、digest。该模块不读取文件、不调工具、不改预算、不写内核。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
import hashlib
import json
import re

from tiangong_kernel.l6_plugins.common._common import ensure_bool

L6_43_PUBLIC_PROJECTION_SCHEMA = "tiangong.l6_43.four_path_public_projection.v1"

SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer\s+|token|secret|password|credential|private[_-]?key)\s*[:=]?\s*[^\s,;]+"
)
PATH_PATTERN = re.compile(r"(?i)([a-z]:\\\\[^\s]+|/[^\s]+(?:/[^\s]+)+)")


def stable_digest(payload: Any, *, length: int = 24) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:length]


def sanitize_text(value: Any, *, limit: int = 700) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\x00", "").replace("\r", " ").replace("\n", " ").strip()
    text = SENSITIVE_PATTERN.sub("[redacted-sensitive]", text)
    text = PATH_PATTERN.sub("[redacted-path]", text)
    return text[: max(0, int(limit))]


def public_dict_of(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    public = getattr(value, "public_dict", None)
    if callable(public):
        result = public()
        return result if isinstance(result, dict) else {"summary": sanitize_text(result)}
    return {"summary": sanitize_text(value)}


def compact_public_payload(value: Any, *, limit: int = 900) -> dict[str, Any]:
    payload = public_dict_of(value)
    return _compact(payload, limit=limit)


def _compact(value: Any, *, limit: int) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in list(value.items())[:30]:
            clean_key = sanitize_text(key, limit=80) or "field"
            lowered = clean_key.lower()
            if any(marker in lowered for marker in ("api_key", "token", "secret", "password", "credential_value")):
                result[clean_key] = "[redacted-sensitive]"
            else:
                result[clean_key] = _compact(item, limit=limit)
        return result
    if isinstance(value, (list, tuple)):
        return [_compact(item, limit=limit) for item in list(value)[:12]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        if isinstance(value, str):
            return sanitize_text(value, limit=limit)
        return value
    return sanitize_text(value, limit=limit)


@dataclass(frozen=True)
class RedactedEvidenceRef:
    """证据只暴露 ref/digest/安全摘要，不给正文。"""

    evidence_ref: str
    source_path: str
    digest: str
    summary: str = ""
    redacted: bool = True
    evidence_ref_only: bool = True
    no_raw_body: bool = True

    def __post_init__(self) -> None:
        for field_name in ("redacted", "evidence_ref_only", "no_raw_body"):
            ensure_bool(getattr(self, field_name), f"RedactedEvidenceRef.{field_name}")
        if not self.redacted or not self.evidence_ref_only or not self.no_raw_body:
            raise ValueError("RedactedEvidenceRef must remain ref-only")
        if not sanitize_text(self.evidence_ref, limit=240):
            raise ValueError("RedactedEvidenceRef.evidence_ref must be non-empty")
        if not sanitize_text(self.digest, limit=80):
            raise ValueError("RedactedEvidenceRef.digest must be non-empty")

    def public_dict(self) -> dict[str, Any]:
        return {
            "evidence_ref": sanitize_text(self.evidence_ref, limit=240),
            "source_path": sanitize_text(self.source_path, limit=160),
            "digest": sanitize_text(self.digest, limit=80),
            "summary": sanitize_text(self.summary, limit=360),
            "redacted": self.redacted,
            "evidence_ref_only": self.evidence_ref_only,
            "no_raw_body": self.no_raw_body,
        }


@dataclass(frozen=True)
class FourPathPublicProjection:
    """四路径公共投影汇总。"""

    projection_id: str
    evidence_refs: tuple[RedactedEvidenceRef, ...] = field(default_factory=tuple)
    context_digest: str = ""
    projection_only: bool = True
    no_raw_prompt: bool = True
    no_plain_secret: bool = True
    no_full_evidence_body: bool = True
    no_execution_plan_body: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "projection_only",
            "no_raw_prompt",
            "no_plain_secret",
            "no_full_evidence_body",
            "no_execution_plan_body",
        ):
            ensure_bool(getattr(self, field_name), f"FourPathPublicProjection.{field_name}")
        if not (
            self.projection_only
            and self.no_raw_prompt
            and self.no_plain_secret
            and self.no_full_evidence_body
            and self.no_execution_plan_body
        ):
            raise ValueError("FourPathPublicProjection must remain public projection only")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_43_PUBLIC_PROJECTION_SCHEMA,
            "projection_id": sanitize_text(self.projection_id, limit=240),
            "context_digest": sanitize_text(self.context_digest, limit=80),
            "evidence_refs": [item.public_dict() for item in self.evidence_refs],
            "evidence_ref_count": len(self.evidence_refs),
            "projection_only": self.projection_only,
            "no_raw_prompt": self.no_raw_prompt,
            "no_plain_secret": self.no_plain_secret,
            "no_full_evidence_body": self.no_full_evidence_body,
            "no_execution_plan_body": self.no_execution_plan_body,
        }


def build_redacted_evidence_refs(sources: dict[str, Any], *, max_refs: int = 12) -> FourPathPublicProjection:
    refs: list[RedactedEvidenceRef] = []
    for source_name, source_value in sources.items():
        if source_value is None:
            continue
        payload = compact_public_payload(source_value, limit=360)
        digest = stable_digest(payload, length=24)
        explicit_ref = payload.get("route_id") or payload.get("bundle_id") or payload.get("envelope_id") or payload.get("report_digest") or payload.get("schema")
        evidence_ref = f"evidence:l6_43:{sanitize_text(source_name, limit=60)}:{sanitize_text(explicit_ref or digest, limit=120)}"
        summary = payload.get("planner_hint") or payload.get("summary") or payload.get("status_summary") or payload.get("schema") or source_name
        refs.append(
            RedactedEvidenceRef(
                evidence_ref=evidence_ref,
                source_path=f"four_path.{sanitize_text(source_name, limit=80)}",
                digest=digest,
                summary=sanitize_text(summary, limit=360),
            )
        )
        if len(refs) >= max_refs:
            break
    context_digest = stable_digest([item.public_dict() for item in refs], length=24)
    return FourPathPublicProjection(
        projection_id=f"four_path_projection:{context_digest}",
        evidence_refs=tuple(refs),
        context_digest=context_digest,
    )
