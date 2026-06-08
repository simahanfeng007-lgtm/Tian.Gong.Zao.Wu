from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def make_sample_repo(root: Path) -> None:
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "docs").mkdir(parents=True, exist_ok=True)
    (root / ".tiangong" / "conversations").mkdir(parents=True, exist_ok=True)
    (root / "artifacts" / "runtime_feedback").mkdir(parents=True, exist_ok=True)
    (root / ".linyuanzhe" / "skills" / "文档经验").mkdir(parents=True, exist_ok=True)
    (root / "src" / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (root / "tests" / "test_calc.py").write_text("from src.calc import add\n\ndef test_add():\n    assert add(1, 2) == 3\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\npythonpath=['.']\n", encoding="utf-8")
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


def _compact_run(label: str, result) -> dict:
    return {
        "label": label,
        "plan_tools": [step.tool_name for step in result.plan],
        "statuses": [item.status.value for item in result.results],
        "ok": all(item.ok for item in result.results),
        "summaries": [item.output_summary[:240] for item in result.results],
        "errors": [item.error_code for item in result.results if item.error_code],
    }


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="runtime_tool_alignment_smoke_") as tmp:
        repo = Path(tmp)
        make_sample_repo(repo)
        runtime = RuntimeEntry()
        direct = runtime.execute_plan(
            [
                ToolInvocation("runtime_tool_alignment_check", {"include_cards": True}),
                ToolInvocation("runtime_llm_operational_drill", {}),
            ],
            workspace=repo,
            user_message="runtime tool alignment direct smoke",
            max_steps=5,
        )
        direct_payload = {
            "ok": all(item.ok for item in direct.results),
            "tool_count": direct.results[0].data.get("tool_count") if direct.results else 0,
            "usage_card_count": direct.results[0].data.get("usage_card_count") if direct.results else 0,
            "alignment_issues": direct.results[0].data.get("issues") if direct.results else [],
            "drill_summary": direct.results[1].data.get("summary") if len(direct.results) > 1 else "",
            "drill_missing": direct.results[1].data.get("missing_tool_routes") if len(direct.results) > 1 else [],
            "drill_empty": direct.results[1].data.get("empty_routes") if len(direct.results) > 1 else [],
        }
        llm_cases = [
            ("runtime_align", "runtime-tools align"),
            ("runtime_drill", "runtime-tools drill"),
            ("runtime_raw_tool", 'runtime-tools tool return_analysis {"content":"alignment smoke"}'),
            ("core_scan", "scan ."),
            ("core_diagnose", "diagnose ."),
            ("core_compileall", "compileall ."),
            ("core_zip", "zip . dist/alignment_delivery.zip"),
            ("codex_status", "code-x status"),
            ("codex_skill", "code-x skill bug_fix"),
            ("codex_readiness", "code-x readiness"),
            ("codex_repo_map", "code-x repo-map ."),
            ("codex_fix_front_chain", "code-x fix add function failure"),
            ("codex_smoke", "code-x smoke ."),
            ("v1_status", "v1-import status"),
            ("v1_guide", "v1-import guide all"),
            ("v1_search", "v1-import search 学习精通"),
            ("v1_document", "v1-import document docs/note.md"),
            ("v1_learning", "v1-import learning 学习一个 CLI 并沉淀为 Skill"),
            ("v1_tool_skill", "v1-import tool-skill 生成一个只读文档摘要工具"),
            ("asset_contract", "asset-contract drill 未来所有自主学习总结经验生产 tool skill 格式统一"),
            ("asset_sandbox", "asset-sandbox drill pytest missing tests"),
            ("asset_adapter_guide", "asset-adapter guide"),
            ("asset_adapter_templates", "asset-adapter templates"),
            ("asset_adapter_smoke", "asset-adapter smoke all"),
        ]
        runs = []
        for label, command in llm_cases:
            result = runtime.run_text(command, workspace=repo, max_steps=20)
            runs.append(_compact_run(label, result))
        payload = {
            "ok": direct_payload["ok"] and all(row["ok"] for row in runs),
            "direct_alignment": direct_payload,
            "llm_operational_runs": runs,
            "all_llm_runs_ok": all(row["ok"] for row in runs),
            "zip_created": (repo / "dist" / "alignment_delivery.zip").exists(),
            "audit_event_count": len(runtime.audit.events),
        }
        out = Path("reports") / "l6702_r15_runtime_tool_alignment_smoke_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": payload["ok"], "report": str(out), "tool_count": direct_payload["tool_count"], "usage_cards": direct_payload["usage_card_count"]}, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
