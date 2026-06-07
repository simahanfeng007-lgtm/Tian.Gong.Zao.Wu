"""运行回合上下文。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
from time import time
from uuid import uuid4

from tiangong_agent_shell.tool_bridge import ToolExecutionMode, normalize_tool_mode

from .execution_policy import ExecutionPolicy


@dataclass
class TurnContext:
    user_message: str
    workspace: Path
    tool_mode: ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED
    max_steps: int = 20
    session_id: str = field(default_factory=lambda: f"sess_{uuid4().hex[:12]}")
    turn_id: str = field(default_factory=lambda: f"turn_{uuid4().hex[:12]}")
    created_at: float = field(default_factory=time)
    policy: ExecutionPolicy = field(default_factory=ExecutionPolicy.default)
    model_config: Any | None = None
    model_client: Any | None = None
    messages: list[dict[str, str]] = field(default_factory=list)

    @classmethod
    def create(
        cls,
        user_message: str,
        workspace: str | Path | None = None,
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 20,
        model_config: Any | None = None,
        model_client: Any | None = None,
        messages: list[dict[str, str]] | None = None,
    ) -> "TurnContext":
        ws = Path(workspace or ".").expanduser().resolve()
        ws.mkdir(parents=True, exist_ok=True)
        return cls(
            user_message=user_message,
            workspace=ws,
            tool_mode=normalize_tool_mode(tool_mode),
            max_steps=max_steps,
            model_config=model_config,
            model_client=model_client,
            messages=list(messages or []),
        )
