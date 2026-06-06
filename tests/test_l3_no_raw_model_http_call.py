from pathlib import Path


def test_l3_new_module_has_no_raw_model_http_call():
    source = Path("tiangong_kernel/l3_orchestration/model_invocation_flow.py").read_text(encoding="utf-8")
    forbidden = ("api.openai.com", "api.deepseek.com", "api.z.ai", "api.minimax", "requests.", "httpx.", "urllib.request")
    assert all(token not in source for token in forbidden)
