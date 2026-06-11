"""组合根：在入口层装配依赖。"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry

from .config_loader import ModelConfig
from .model_client_mock import MockModelClient
from .model_client_openai_compatible import OpenAICompatibleModelClient
from .providers.openai_adapter import OpenAINativeAdapter
from .providers.anthropic_adapter import AnthropicNativeAdapter
from .providers.gemini_adapter import GeminiNativeAdapter
from .model_client_port import ModelClientPort
from .session_state import SessionState
from .tool_bridge import ToolBridge


@dataclass
class AgentShellContext:
    config: ModelConfig
    session: SessionState
    model_client: ModelClientPort
    tool_bridge: ToolBridge
    kernel_importable: bool
    runtime: RuntimeEntry
    workspace: Path
    max_steps: int
    last_runtime_result: object | None = None
    last_prompt_trace_event: object | None = None
    last_prompt_trace_outcome: object | None = None
    prompt_trace_buffer: list[dict] = field(default_factory=list)


def build_agent_context(
    config: ModelConfig,
    *,
    workspace: str | Path | None = None,
    max_steps: int = 20,
) -> AgentShellContext:
    workspace_path = Path(workspace or ".").expanduser().resolve()
    tool_bridge = ToolBridge(config.tool_execution_mode)
    workspace_writable = _check_workspace_access(workspace_path)
    tool_bridge.register_capability("write_file", workspace_writable)
    tool_bridge.register_capability("write_workspace_file", workspace_writable)
    return AgentShellContext(
        config=config,
        session=SessionState.create(config),
        model_client=select_model_client(config),
        tool_bridge=tool_bridge,
        kernel_importable=probe_kernel_importable(),
        runtime=RuntimeEntry(),
        workspace=workspace_path,
        max_steps=max_steps,
    )


def _check_workspace_access(workspace: Path) -> bool:
    try:
        return workspace.exists() and workspace.is_dir() and os.access(workspace, os.W_OK)
    except OSError:
        return False


def select_model_client(config: ModelConfig) -> ModelClientPort:
    provider = str(config.provider or "openai_compatible").strip().lower()
    if provider == "mock":
        return MockModelClient()
    if provider in {"openai"}:
        return OpenAINativeAdapter()
    if provider in {"anthropic", "claude", "fable"}:
        return AnthropicNativeAdapter()
    if provider in {"gemini", "google"}:
        return GeminiNativeAdapter()
    if provider in {"openai_compatible", "deepseek", "qwen", "dashscope", "glm", "zhipu", "minimax", "mimo"}:
        return OpenAICompatibleModelClient()
    return OpenAICompatibleModelClient()


def probe_kernel_importable() -> bool:
    try:
        import tiangong_kernel  # noqa: F401
    except Exception:  # noqa: BLE001 - status probe should not fail startup
        return False
    return True
