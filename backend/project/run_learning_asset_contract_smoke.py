from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def _compact(label: str, result) -> dict:
    return {
        "label": label,
        "plan_tools": [step.tool_name for step in result.plan],
        "statuses": [item.status.value for item in result.results],
        "ok": all(item.ok for item in result.results),
        "summaries": [item.output_summary[:240] for item in result.results],
    }


def _report_path() -> Path:
    report_dir = os.environ.get("TIANGONG_REPORT_DIR") or os.environ.get("LINYUANZHE_REPORT_DIR")
    if report_dir:
        return Path(report_dir) / "l6702_r16_learning_asset_contract_smoke_report.json"
    return Path(tempfile.mkdtemp(prefix="linyuanzhe_smoke_report_")) / "l6702_r16_learning_asset_contract_smoke_report.json"


def _report_label(path: Path) -> str:
    return f"<tmp>/{path.name}" if str(path).startswith(tempfile.gettempdir()) else path.name


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="learning_asset_contract_smoke_") as tmp:
        repo = Path(tmp)
        (repo / "src").mkdir()
        (repo / "src" / "demo.py").write_text("def ok():\n    return True\n", encoding="utf-8")
        runtime = RuntimeEntry()
        direct = runtime.execute_plan(
            [
                ToolInvocation("learning_asset_contract_guide", {}),
                ToolInvocation("synthesize_experience_candidates", {"notes": "未来所有自主学习和总结经验生产的 tool 和 skill 格式统一", "max_candidates": 8}),
                ToolInvocation("queue_skill_candidates", {"notes": "未来统一格式", "max_items": 8}),
                ToolInvocation("queue_tool_production_requests", {"notes": "未来统一格式", "max_items": 8}),
                ToolInvocation("learning_asset_contract_normalize", {"notes": "未来统一格式", "max_items": 16}),
                ToolInvocation("learning_asset_contract_validate", {}),
            ],
            workspace=repo,
            user_message="learning asset contract direct smoke",
            max_steps=10,
        )
        llm_cases = [
            ("guide", "asset-contract guide"),
            ("drill", "asset-contract drill 未来所有自主学习总结经验生产 tool skill 格式统一"),
            ("natural", "自主学习总结经验生产tool和skill格式统一"),
            ("converge", "learning-converge 统一未来经验 skill tool 格式"),
        ]
        runs = [_compact(label, runtime.run_text(command, workspace=repo, max_steps=20)) for label, command in llm_cases]
        align = runtime.execute_plan(
            [
                ToolInvocation("runtime_tool_alignment_check", {"include_cards": True}),
                ToolInvocation("runtime_llm_operational_drill", {}),
            ],
            workspace=repo,
            user_message="alignment after R16",
            max_steps=5,
        )
        direct_data = direct.results[-1].data if direct.results else {}
        alignment_data = align.results[0].data if align.results else {}
        drill_data = align.results[1].data if len(align.results) > 1 else {}
        payload = {
            "ok": all(item.ok for item in direct.results) and all(row["ok"] for row in runs) and all(item.ok for item in align.results),
            "direct_statuses": [item.status.value for item in direct.results],
            "contract_validate_status": direct_data.get("status"),
            "contract_count": direct_data.get("contract_count"),
            "contract_issue_count": direct_data.get("issue_count"),
            "llm_runs": runs,
            "tool_count": alignment_data.get("tool_count"),
            "usage_card_count": alignment_data.get("usage_card_count"),
            "all_registered_tools_classifier_allowed": alignment_data.get("all_registered_tools_classifier_allowed"),
            "alignment_issues": alignment_data.get("issues"),
            "drill_missing_tool_routes": drill_data.get("missing_tool_routes"),
            "drill_empty_routes": drill_data.get("empty_routes"),
        }
        out = _report_path()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": payload["ok"], "report": _report_label(out), "tool_count": payload["tool_count"], "contract_status": payload["contract_validate_status"]}, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] and payload["contract_validate_status"] == "pass" and payload["contract_issue_count"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
