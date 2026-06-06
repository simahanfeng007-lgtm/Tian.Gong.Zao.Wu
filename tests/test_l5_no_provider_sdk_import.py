from pathlib import Path


def test_l5_model_capability_patch_has_no_provider_sdk_import():
    source = Path("tiangong_kernel/l5_plugin_host/model_capability_invariants.py").read_text(encoding="utf-8")
    forbidden = ("import openai", "import anthropic", "google.genai", "import dashscope", "import zhipuai", "import minimax", "import deepseek")
    assert all(token not in source for token in forbidden)
