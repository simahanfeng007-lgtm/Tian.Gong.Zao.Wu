from __future__ import annotations

import json
import shutil
import tempfile
from pathlib import Path

from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation



def _public_tmp(path: Path) -> str:
    value = str(path)
    tmp_root = tempfile.gettempdir()
    if value.startswith(tmp_root):
        return f"<tmp>/{Path(value).name}"
    return Path(value).name

def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    workspace = Path(tempfile.mkdtemp(prefix="l67245_doc_context_"))
    try:
        sample = workspace / "sample_project_note.md"
        sample.write_text(
            "# 临渊者文档追问样本\n\n"
            "执行力第一，但执行力不是自治夺权。\n\n"
            "文档解析以后必须支持追问、引用、导出与修改计划。\n\n"
            "A5 Only 治理保持不变，A0-A4 不得恢复过度限制。\n",
            encoding="utf-8",
        )
        rt = RuntimeEntry()
        parse_result = rt.execute_plan(
            [ToolInvocation("document_parse", {"path": sample.name})],
            workspace=workspace,
            user_message="解析这个文档",
        )
        _assert(parse_result.results and parse_result.results[0].ok, "document_parse failed")
        parse_data = parse_result.results[0].data
        _assert(parse_data.get("document_id"), "document_id missing")
        _assert(parse_data.get("raw_bytes_hidden") is True, "raw_bytes_hidden not preserved")
        _assert("content_preview" not in parse_data, "content_preview leaked into tool data")
        _assert("可追问" in parse_result.results[0].output_summary, "follow-up summary not exposed")

        query_result = rt.execute_plan(
            [ToolInvocation("document_query", {"query": "A5 Only 治理是什么？", "top_k": 4})],
            workspace=workspace,
            user_message="A5 Only 治理是什么？",
        )
        _assert(query_result.results and query_result.results[0].ok, "document_query failed")
        _assert("A5" in query_result.results[0].output_summary, "document_query did not hit expected content")
        _assert(query_result.results[0].data.get("matches"), "document_query matches missing")
        _assert(query_result.results[0].data.get("raw_bytes_hidden") is True, "query raw boundary missing")

        export_result = rt.execute_plan(
            [ToolInvocation("document_export", {"format": "md", "target": "exports/sample_summary.md"})],
            workspace=workspace,
            user_message="导出刚才文档摘要",
        )
        _assert(export_result.results and export_result.results[0].ok, "document_export failed")
        exported = workspace / "exports" / "sample_summary.md"
        _assert(exported.exists(), "export artifact missing")
        exported_text = exported.read_text(encoding="utf-8")
        _assert("原始二进制" in exported_text and "文档 ID" in exported_text, "export content missing boundary/id")

        rewrite_result = rt.execute_plan(
            [ToolInvocation("document_rewrite_plan", {"instruction": "把执行力第一这段改得更清晰"})],
            workspace=workspace,
            user_message="把执行力第一这段改得更清晰",
        )
        _assert(rewrite_result.results and rewrite_result.results[0].ok, "document_rewrite_plan failed")
        _assert("不直接写入" in rewrite_result.results[0].output_summary, "rewrite plan boundary missing")

        alias_plan = validate_and_build_plan({"steps": [{"tool_name": "documentQuery", "arguments": {"query": "执行力", "top_k": 2}}]})
        _assert(alias_plan[0].tool_name == "document_query", "documentQuery alias not normalized")
        export_plan = validate_and_build_plan({"steps": [{"tool_name": "documentExport", "arguments": {"format": "json"}}]})
        _assert(export_plan[0].tool_name == "document_export", "documentExport alias not normalized")
        rewrite_plan = validate_and_build_plan({"steps": [{"tool_name": "documentRewritePlan", "arguments": {"instruction": "润色"}}]})
        _assert(rewrite_plan[0].tool_name == "document_rewrite_plan", "documentRewritePlan alias not normalized")

        bridge = PlanBridge()
        followup = bridge.build_plan("刚才那个文档里 A5 Only 是什么意思？")
        _assert(followup and followup[0].tool_name == "document_query", "PlanBridge follow-up query not routed")
        export_followup = bridge.build_plan("导出刚才文档摘要为 md")
        _assert(export_followup and export_followup[0].tool_name == "document_export", "PlanBridge export not routed")
        rewrite_followup = bridge.build_plan("把刚才文档里的执行力第一改写得更清晰")
        _assert(rewrite_followup and rewrite_followup[0].tool_name == "document_rewrite_plan", "PlanBridge rewrite not routed")
        chat_plan = bridge.build_plan("你会做什么")
        _assert(chat_plan == [], "normal chat should not trigger document/task plan")

        rc = RiskClassifier()
        _assert(rc.classify(ToolInvocation("document_query", {"query": "x"}))[0].value == "A1", "document_query risk not A1")
        _assert(rc.classify(ToolInvocation("document_rewrite_plan", {"instruction": "x"}))[0].value == "A2", "document_rewrite_plan risk not A2")
        _assert(rc.classify(ToolInvocation("document_export", {"format": "md"}))[0].value == "A3", "document_export risk not A3")

        print(json.dumps({
            "status": "passed",
            "workspace": _public_tmp(workspace),
            "document_id": parse_data.get("document_id"),
            "export": _public_tmp(exported),
            "checks": [
                "document_parse_context_saved",
                "document_query_citations",
                "document_export_artifact",
                "document_rewrite_plan_boundary",
                "plan_schema_aliases",
                "plan_bridge_followups",
                "normal_chat_no_task_trigger",
                "risk_levels",
            ],
        }, ensure_ascii=False, indent=2))
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    main()
