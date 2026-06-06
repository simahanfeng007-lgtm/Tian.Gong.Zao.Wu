from __future__ import annotations

from pathlib import Path


def test_l4_math_adapter_sources_do_not_import_network_or_execution_modules() -> None:
    files = (
        Path("tiangong_kernel/l4_action_grounding/math_model_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/python_math_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/statistics_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/llm_judge_adapter.py"),
        Path("tiangong_kernel/l4_action_grounding/math_adapter_descriptor.py"),
    )
    forbidden = (
        "import socket",
        "import subprocess",
        "import requests",
        "from socket",
        "from subprocess",
        "from requests",
        "urllib",
        "http.client",
        "os.system",
        "eval(",
        "exec(",
        "open(",
        ".open(",
    )

    for file in files:
        source = file.read_text(encoding="utf-8")
        assert not any(token in source for token in forbidden), file
