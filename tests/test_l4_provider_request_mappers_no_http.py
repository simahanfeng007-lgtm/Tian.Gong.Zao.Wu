from pathlib import Path
from tiangong_kernel.l4_action_grounding.model_provider_adapter import DeepSeekV4RequestMapper


def test_l4_request_mapper_returns_fake_mapping_only():
    mapped = DeepSeekV4RequestMapper().map_request(object())
    assert mapped["provider_specific_http_not_sent"] is True
    source = Path("tiangong_kernel/l4_action_grounding/model_provider_adapter.py").read_text(encoding="utf-8")
    assert "requests." not in source and "httpx." not in source and "urllib.request" not in source
