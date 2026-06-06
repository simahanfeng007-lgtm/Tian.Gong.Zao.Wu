from pathlib import Path
import re


def test_l4_new_module_has_no_plain_secret_values():
    source = Path("tiangong_kernel/l4_action_grounding/model_provider_adapter.py").read_text(encoding="utf-8")
    assert not re.search(r"sk-[A-Za-z0-9]{8,}", source)
    assert not re.search(r"Bearer\s+[A-Za-z0-9_\-]{8,}", source)
    assert not re.search(r"(api[_-]?key|secret|token)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]", source, flags=re.IGNORECASE)
