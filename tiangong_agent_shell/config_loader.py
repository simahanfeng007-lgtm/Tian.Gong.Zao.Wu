"""L6.9 外壳配置加载。

优先级：CLI 参数 > 环境变量 > 配置文件 > 默认值。
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .errors import ConfigError
from .safe_logging import sanitize_mapping
from tiangong_agent_runtime.planner_mode import PlannerMode, normalize_planner_mode

from .tool_bridge import ToolExecutionMode, normalize_tool_mode


@dataclass(frozen=True)
class ModelConfig:
    provider: str = "openai_compatible"
    base_url: str = ""
    api_key: str = ""
    model: str = ""
    timeout: float = 60.0
    stream: bool = False
    tool_execution_mode: ToolExecutionMode = ToolExecutionMode.DISABLED
    planner_mode: PlannerMode = PlannerMode.RULE_ONLY

    def sanitized_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["tool_execution_mode"] = self.tool_execution_mode.value
        data["planner_mode"] = self.planner_mode.value
        return sanitize_mapping(data)

    @property
    def has_real_api_key(self) -> bool:
        return bool(self.api_key) and self.api_key not in {
            "PLEASE_SET_YOUR_API_KEY",
            "YOUR_API_KEY",
            "example",
        }


ENV_MAP = {
    "provider": "TIANGONG_PROVIDER",
    "base_url": "TIANGONG_BASE_URL",
    "api_key": "TIANGONG_API_KEY",
    "model": "TIANGONG_MODEL",
    "timeout": "TIANGONG_TIMEOUT",
    "tool_execution_mode": "TIANGONG_TOOL_MODE",
    "planner_mode": "TIANGONG_PLANNER_MODE",
}

# L6.50/L6.51：DeepSeek Provider 使用受控配置别名进入统一 ModelConfig。
# 这些环境变量只在配置层解析，不允许前端、测试脚本或临时工具裸调 Provider SDK。
ENV_ALIASES = {
    "provider": ("DEEPSEEK_PROVIDER",),
    "base_url": ("DEEPSEEK_BASE_URL",),
    "api_key": ("DEEPSEEK_API_KEY",),
    "model": ("DEEPSEEK_MODEL",),
    "timeout": ("DEEPSEEK_TIMEOUT",),
}


def load_model_config(args: Any | None = None) -> ModelConfig:
    """从 CLI/env/file/default 合成模型配置。"""
    args = args or object()
    data: dict[str, Any] = {
        "provider": "openai_compatible",
        "base_url": "",
        "api_key": "",
        "model": "",
        "timeout": 60.0,
        "stream": False,
        "tool_execution_mode": ToolExecutionMode.DISABLED.value,
        "planner_mode": PlannerMode.RULE_ONLY.value,
    }

    config_path = getattr(args, "config", None)
    if config_path:
        data.update(_read_config_file(Path(config_path)))

    for key, env_name in ENV_MAP.items():
        value = os.getenv(env_name)
        if value not in (None, ""):
            data[key] = value

    # Provider-specific aliases have lower priority than TIANGONG_* canonical envs
    # but higher priority than config-file defaults.
    for key, alias_names in ENV_ALIASES.items():
        if data.get(key) not in (None, "", "openai_compatible") and key == "provider":
            continue
        if data.get(key) not in (None, "") and key != "provider":
            continue
        for alias_name in alias_names:
            value = os.getenv(alias_name)
            if value not in (None, ""):
                data[key] = value
                break

    cli_map = {
        "provider": getattr(args, "provider", None),
        "base_url": getattr(args, "base_url", None),
        "api_key": getattr(args, "api_key", None),
        "model": getattr(args, "model", None),
        "timeout": getattr(args, "timeout", None),
        "tool_execution_mode": getattr(args, "tool_mode", None),
        "planner_mode": getattr(args, "planner_mode", None),
    }
    for key, value in cli_map.items():
        if value not in (None, ""):
            data[key] = value

    if getattr(args, "mock", False):
        data.update(
            {
                "provider": "mock",
                "base_url": "",
                "api_key": "",
                "model": data.get("model") or "mock-model",
                "stream": False,
                "tool_execution_mode": data.get("tool_execution_mode") or "disabled",
            }
        )

    return _coerce_model_config(data)


def _read_config_file(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"配置文件不存在：{path}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"配置文件不是合法 JSON：{path}", detail=str(exc)) from exc
    except OSError as exc:
        raise ConfigError(f"配置文件读取失败：{path}", detail=str(exc)) from exc


def _coerce_model_config(data: dict[str, Any]) -> ModelConfig:
    provider = str(data.get("provider") or "openai_compatible").strip().lower()
    base_url = str(data.get("base_url") or "").strip()
    api_key = str(data.get("api_key") or "").strip()
    model = str(data.get("model") or "").strip()
    try:
        timeout = float(data.get("timeout", 60.0))
    except (TypeError, ValueError) as exc:
        raise ConfigError("timeout 必须是数字。", detail=str(exc)) from exc
    stream = bool(data.get("stream", False))
    tool_mode = normalize_tool_mode(data.get("tool_execution_mode"))
    planner_mode = normalize_planner_mode(data.get("planner_mode"))
    return ModelConfig(
        provider=provider,
        base_url=base_url,
        api_key=api_key,
        model=model,
        timeout=timeout,
        stream=stream,
        tool_execution_mode=tool_mode,
        planner_mode=planner_mode,
    )
