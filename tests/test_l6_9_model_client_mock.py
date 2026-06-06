from __future__ import annotations

from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.model_client_mock import MockModelClient


def test_mock_model_echoes_last_user_message() -> None:
    cfg = ModelConfig(provider="mock", model="mock-model")
    client = MockModelClient()
    result = client.chat(
        [
            {"role": "system", "content": "s"},
            {"role": "user", "content": "第一句"},
            {"role": "assistant", "content": "ok"},
            {"role": "user", "content": "第二句"},
        ],
        cfg,
    )
    assert result.content == "[MOCK] 已收到：第二句"
    assert result.provider == "mock"
