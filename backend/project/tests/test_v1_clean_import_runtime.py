from __future__ import annotations

import json
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def _sample_repo(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir()
    (tmp_path / ".tiangong" / "conversations").mkdir(parents=True)
    (tmp_path / "artifacts" / "runtime_feedback").mkdir(parents=True)
    (tmp_path / ".linyuanzhe" / "skills" / "修复经验").mkdir(parents=True)
    (tmp_path / "docs" / "note.md").write_text("# 天工搜索\n\n这里记录 Code-X 与 学习精通 的材料。\n", encoding="utf-8")
    (tmp_path / ".tiangong" / "conversations" / "history.jsonl").write_text(
        json.dumps({"role": "user", "content": "上次讨论学习精通和文档提取"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (tmp_path / "artifacts" / "runtime_feedback" / "renwu_liuhen.jsonl").write_text(
        json.dumps({"status": "completed", "goal": "修复文档提取", "steps": [{"tool_name": "document_text_extract"}]}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (tmp_path / ".linyuanzhe" / "skills" / "修复经验" / "SKILL.md").write_text("# 修复经验\n\n文档提取失败时先降级读取，再交接证据。\n", encoding="utf-8")
    return tmp_path


def test_v1_clean_import_tools_registered() -> None:
    runtime = RuntimeEntry()
    names = set(runtime.registry.names())
    required = {
        "v1_clean_import_status",
        "v1_clean_import_audit",
        "v1_clean_import_guide",
        "workspace_text_search",
        "conversation_history_search",
        "task_pattern_search",
        "experience_mentor_search",
        "document_text_extract",
        "web_readability_extract",
        "learning_master_plan",
        "tool_skill_blueprint",
    }
    assert required.issubset(names)


def test_v1_clean_import_chain_smoke(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)
    runtime = RuntimeEntry()
    result = runtime.execute_plan([
        ToolInvocation("v1_clean_import_status", {}),
        ToolInvocation("v1_clean_import_audit", {}),
        ToolInvocation("v1_clean_import_guide", {"domain": "all"}),
        ToolInvocation("workspace_text_search", {"query": "学习精通"}),
        ToolInvocation("conversation_history_search", {"query": "文档提取"}),
        ToolInvocation("task_pattern_search", {"query": "文档提取"}),
        ToolInvocation("experience_mentor_search", {"query": "文档"}),
        ToolInvocation("document_text_extract", {"path": "docs/note.md"}),
        ToolInvocation("learning_master_plan", {"goal": "学习一个软件并沉淀为长期能力"}),
        ToolInvocation("tool_skill_blueprint", {"goal": "生成一个只读文档摘要工具"}),
    ], workspace=repo, user_message="v1 clean import smoke", max_steps=20)
    assert [item.status.value for item in result.results] == ["ok"] * len(result.results)
    assert result.results[1].data["result"]["no_pollution_assertions"]["import_v1"] is False
    assert result.results[3].data["result"]["hit_count"] >= 1
    assert result.results[7].data["result"]["path"] == "docs/note.md"


def test_v1_clean_import_planbridge_triggers(tmp_path: Path) -> None:
    repo = _sample_repo(tmp_path)
    runtime = RuntimeEntry()
    audit = runtime.run_text("v1-import audit", workspace=repo, max_steps=3)
    assert audit.plan[0].tool_name == "v1_clean_import_audit"
    assert audit.results[0].status.value == "ok"
    search = runtime.run_text("v1-import search 学习精通", workspace=repo, max_steps=3)
    assert search.plan[0].tool_name == "workspace_text_search"
    assert search.results[0].data["result"]["hit_count"] >= 1
    learning = runtime.run_text("v1-import learning 学习一个 CLI 并沉淀为 Skill", workspace=repo, max_steps=3)
    assert learning.plan[0].tool_name == "learning_master_plan"
    assert learning.results[0].data["result"]["depth"] == "L5"
