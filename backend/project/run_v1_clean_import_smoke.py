from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def make_sample_repo(root: Path) -> None:
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / ".tiangong" / "conversations").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "runtime_feedback").mkdir(parents=True, exist_ok=True)
    (root / ".linyuanzhe" / "skills" / "文档经验").mkdir(parents=True, exist_ok=True)
    (root / "docs" / "note.md").write_text("# 学习精通\n\n文档提取和经验搜索材料。\n", encoding="utf-8")
    (root / ".tiangong" / "conversations" / "history.jsonl").write_text(
        json.dumps({"role": "user", "content": "之前讨论过文档提取和学习精通"}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / "artifacts" / "runtime_feedback" / "renwu_liuhen.jsonl").write_text(
        json.dumps({"status": "completed", "goal": "文档提取", "steps": [{"tool_name": "document_text_extract"}]}, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (root / ".linyuanzhe" / "skills" / "文档经验" / "SKILL.md").write_text("# 文档经验\n\n先只读提取，再降级搜索。\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="v1_clean_import_smoke_") as tmp:
        repo = Path(tmp)
        make_sample_repo(repo)
        runtime = RuntimeEntry()
        plan = [
            ToolInvocation("v1_clean_import_status", {}),
            ToolInvocation("v1_clean_import_audit", {}),
            ToolInvocation("v1_clean_import_guide", {}),
            ToolInvocation("workspace_text_search", {"query": "学习精通"}),
            ToolInvocation("conversation_history_search", {"query": "文档提取"}),
            ToolInvocation("task_pattern_search", {"query": "文档提取"}),
            ToolInvocation("experience_mentor_search", {"query": "文档"}),
            ToolInvocation("document_text_extract", {"path": "docs/note.md"}),
            ToolInvocation("learning_master_plan", {"goal": "学习一个软件并沉淀为长期能力"}),
            ToolInvocation("tool_skill_blueprint", {"goal": "生成一个只读文档摘要工具"}),
        ]
        result = runtime.execute_plan(plan, workspace=repo, user_message="v1 clean import smoke", max_steps=20)
        payload = {
            "ok": all(item.ok for item in result.results),
            "tool_count": len(runtime.registry.names()),
            "v1_clean_tools_present": all(name in runtime.registry.names() for name in ["v1_clean_import_audit", "workspace_text_search", "learning_master_plan", "tool_skill_blueprint"]),
            "results": [
                {"tool_name": item.tool_name, "status": item.status.value, "summary": item.output_summary[:300], "error_code": item.error_code}
                for item in result.results
            ],
        }
        out = Path("reports") / "l6702_r14_v1_clean_import_smoke_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": payload["ok"], "report": str(out), "tool_count": payload["tool_count"]}, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
