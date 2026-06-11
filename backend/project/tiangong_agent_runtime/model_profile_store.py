"""L6.72.53 模型画像持久化存储。

只写安全画像，不写 API Key，不触网，不改变执行路径。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

from .model_capability_adapter import ModelExecutionPolicy, ModelProfile




def _state_root(workspace: str | Path, root_name: str) -> Path:
    override = os.environ.get("LINYUANZHE_STATE_DIR") or os.environ.get("TIANGONG_STATE_DIR")
    if override:
        return Path(override).expanduser().resolve() / root_name.replace(".linyuanzhe/", "")
    return Path(workspace).expanduser().resolve() / root_name

def _safe_component(text: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_", "."} else "_" for ch in str(text or "unknown"))
    return (cleaned.strip("._") or "unknown")[:80]


class ModelProfileStore:
    def __init__(self, root_name: str = ".linyuanzhe/model_profiles") -> None:
        self.root_name = root_name
        self.last_profile_ref: str = ""
        self.last_error: str = ""

    def save(self, workspace: str | Path, profile: ModelProfile, policy: ModelExecutionPolicy | None = None) -> str:
        try:
            root = _state_root(workspace, self.root_name)
            root.mkdir(parents=True, exist_ok=True)
            filename = f"{_safe_component(profile.provider_id)}__{_safe_component(profile.model_id)}__{profile.profile_id}.json"
            target = root / filename
            payload: dict[str, Any] = {
                "schema": "tiangong.l6_72_53.model_profile_record.v1",
                "profile": profile.public_dict(),
                "policy": policy.public_dict() if policy is not None else None,
                "storage_boundary": {
                    "no_api_key": True,
                    "no_raw_prompt": True,
                    "no_tool_result_body": True,
                    "passive_only": True,
                },
            }
            target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            self.last_profile_ref = str(target)
            self.last_error = ""
            return str(target)
        except Exception as exc:  # noqa: BLE001 - passive store must not break Runtime
            self.last_error = redact_text(f"{type(exc).__name__}: {exc}")[:300]
            return ""

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_72_53.model_profile_store.v1",
            "last_profile_ref": self.last_profile_ref,
            "last_error": self.last_error,
            "passive_only": True,
        }
