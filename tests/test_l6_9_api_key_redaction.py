from __future__ import annotations

from tiangong_agent_shell.config_loader import ModelConfig
from tiangong_agent_shell.safe_logging import has_unredacted_secret, redact_secret, redact_text


def test_redact_secret_masks_long_key() -> None:
    secret = "sk-1234567890abcdef"
    masked = redact_secret(secret)
    assert secret not in masked
    assert masked.startswith("<已配置:digest:")
    assert not masked.startswith("sk-")
    assert not masked.endswith("cdef")


def test_redact_text_removes_secret() -> None:
    secret = "sk-1234567890abcdef"
    text = redact_text(f"Authorization: Bearer {secret}", [secret])
    assert not has_unredacted_secret(text, secret)
    assert "<已配置:digest:" in text


def test_config_sanitized_dict_masks_api_key() -> None:
    secret = "sk-1234567890abcdef"
    cfg = ModelConfig(api_key=secret)
    data = cfg.sanitized_dict()
    assert data["api_key"] != secret
    assert secret not in str(data)
