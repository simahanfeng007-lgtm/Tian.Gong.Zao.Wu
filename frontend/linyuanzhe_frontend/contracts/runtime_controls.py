from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, Mapping

from .runtime_snapshot import safe_text


CONTROL_CONTRACT_VERSION = "tiangong.l6_64.frontend_runtime_controls.v2"
TASK_STOP_ENDPOINT = "/control/task/stop"
TASK_RESET_ENDPOINT = "/control/task/reset"
TASK_INTERRUPT_ENDPOINT = "/control/task/interrupt"
ALLOWED_CONTROL_ENDPOINTS = (TASK_STOP_ENDPOINT, TASK_RESET_ENDPOINT, TASK_INTERRUPT_ENDPOINT)


@dataclass(frozen=True)
class RuntimeControlRequest:
    """Display-side request envelope for Runtime task controls.

    The desktop frontend never stops or interrupts tools, mutates memory, rolls back, or resets
    Runtime locally. It may only send a control request to the official Runtime
    gateway and display the resulting PublicProjection.
    """

    action: str
    run_id: str = ""
    task_id: str = ""
    reason: str = "user_requested"
    frontend_contract: str = CONTROL_CONTRACT_VERSION
    no_frontend_tool_execution: bool = True
    no_frontend_memory_write: bool = True
    no_frontend_rollback_apply: bool = True

    def to_payload(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RuntimeControlResult:
    action: str
    status: str
    message: str = ""
    audit_id: str = ""
    frontend_only_fallback: bool = False

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any], *, action: str) -> "RuntimeControlResult":
        payload = data.get("payload", data)
        if not isinstance(payload, Mapping):
            payload = {"message": payload}
        return cls(
            action=safe_text(payload.get("action", action), 32),
            status=safe_text(payload.get("status", payload.get("state", "requested")), 64),
            message=safe_text(payload.get("message", ""), 240),
            audit_id=safe_text(payload.get("audit_id", payload.get("audit_ref", "")), 80),
            frontend_only_fallback=bool(payload.get("frontend_only_fallback", False)),
        )
