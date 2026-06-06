from __future__ import annotations

import argparse
import json

from tiangong_agent_shell.config_loader import load_model_config


def args(**kwargs: object) -> argparse.Namespace:
    defaults = {
        "config": None,
        "mock": False,
        "provider": None,
        "base_url": None,
        "api_key": None,
        "model": None,
        "timeout": None,
        "tool_mode": None,
    }
    defaults.update(kwargs)
    return argparse.Namespace(**defaults)


def test_cli_overrides_env_and_file(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "model.json"
    config_path.write_text(json.dumps({"provider": "openai_compatible", "model": "from-file"}), encoding="utf-8")
    monkeypatch.setenv("TIANGONG_MODEL", "from-env")
    cfg = load_model_config(args(config=str(config_path), model="from-cli"))
    assert cfg.model == "from-cli"


def test_env_overrides_file(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "model.json"
    config_path.write_text(json.dumps({"provider": "openai_compatible", "model": "from-file"}), encoding="utf-8")
    monkeypatch.setenv("TIANGONG_MODEL", "from-env")
    cfg = load_model_config(args(config=str(config_path)))
    assert cfg.model == "from-env"


def test_mock_forces_mock_provider() -> None:
    cfg = load_model_config(args(mock=True, provider="openai_compatible"))
    assert cfg.provider == "mock"
    assert cfg.model == "mock-model"
