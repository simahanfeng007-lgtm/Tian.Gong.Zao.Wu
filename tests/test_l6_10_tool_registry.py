from __future__ import annotations

from tiangong_agent_runtime.runtime_entry import build_default_registry


def test_default_registry_contains_only_first_batch_tools() -> None:
    registry = build_default_registry()
    assert registry.names() == [
        "create_zip_package",
        "list_dir",
        "model_chat",
        "read_file",
        "return_analysis",
        "return_code",
        "run_python_quality_check",
        "write_workspace_file",
    ]
    assert registry.get("terminal_shell") is None
