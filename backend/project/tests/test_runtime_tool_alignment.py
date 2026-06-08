from __future__ import annotations

import json
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def _sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "tests").mkdir()
    (tmp_path / ".linyuanzhe" / "skills" / "样例经验").mkdir(parents=True)
    (tmp_path / "docs" / "note.md").write_text("# 学习精通\n\n文档提取和经验搜索材料。\n", encoding="utf-8")
    (tmp_path / "src" / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (tmp_path / "tests" / "test_calc.py").write_text("from src.calc import add\n\ndef test_add():\n    assert add(1, 2) == 3\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text("[tool.pytest.ini_options]\npythonpath=['.']\n", encoding="utf-8")
    (tmp_path / ".linyuanzhe" / "skills" / "样例经验" / "SKILL.md").write_text("# 样例经验\n\n先搜索，再提取，再交接。\n", encoding="utf-8")
    return tmp_path


def test_runtime_tool_alignment_registered_and_complete(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)
    runtime = RuntimeEntry()
    names = set(runtime.registry.names())
    assert "runtime_tool_alignment_check" in names
    assert "runtime_llm_operational_drill" in names
    result = runtime.execute_plan([
        ToolInvocation("runtime_tool_alignment_check", {"include_cards": True}),
        ToolInvocation("runtime_llm_operational_drill", {}),
    ], workspace=repo, user_message="runtime tool alignment", max_steps=5)
    assert [item.status.value for item in result.results] == ["ok", "ok"]
    alignment = result.results[0].data
    assert alignment["all_tools_have_usage_cards"] is True
    assert alignment["all_registered_tools_classifier_allowed"] is True
    assert alignment["tool_count"] == len(runtime.registry.names())
    assert alignment["usage_card_count"] == alignment["tool_count"]
    assert "skill.runtime_tool_alignment_workflow" in alignment["skill_sources"]
    drill = result.results[1].data
    assert drill["status"] == "ok"
    assert not drill["missing_tool_routes"]
    assert not drill["empty_routes"]


def test_runtime_tool_alignment_planbridge_triggers(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)
    runtime = RuntimeEntry()
    align = runtime.run_text("runtime-tools align", workspace=repo, max_steps=3)
    assert align.plan[0].tool_name == "runtime_tool_alignment_check"
    assert align.results[0].status.value == "ok"
    drill = runtime.run_text("runtime-tools drill", workspace=repo, max_steps=3)
    assert drill.plan[0].tool_name == "runtime_llm_operational_drill"
    assert drill.results[0].status.value == "ok"
    raw = runtime.run_text('runtime-tools tool return_analysis {"analysis":"ok"}', workspace=repo, max_steps=3)
    assert raw.plan[0].tool_name == "return_analysis"
    assert raw.results[0].status.value == "ok"
