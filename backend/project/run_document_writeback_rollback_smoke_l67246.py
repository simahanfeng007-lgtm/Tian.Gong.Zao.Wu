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
    workspace = Path(tempfile.mkdtemp(prefix="l67246_doc_writeback_"))
    try:
        sample = workspace / "sample_note.md"
        sample.write_text(
            "# 临渊者文档写回样本\n\n"
            "执行力第一，但执行力不是自治夺权。\n\n"
            "A5 Only 治理保持不变。\n",
            encoding="utf-8",
        )
        rt = RuntimeEntry()
        parse_result = rt.execute_plan(
            [ToolInvocation("document_parse", {"path": sample.name})],
            workspace=workspace,
            user_message="解析这个文档",
        )
        _assert(parse_result.results and parse_result.results[0].ok, "document_parse failed")

        dry = rt.execute_plan(
            [ToolInvocation("document_apply_rewrite", {"path": sample.name, "old_text": "执行力第一", "new_text": "执行优先", "dry_run": True})],
            workspace=workspace,
            user_message="预演写回",
        )
        _assert(dry.results and dry.results[0].ok, "document_apply_rewrite dry_run failed")
        _assert(dry.results[0].data.get("dry_run") is True, "dry_run data missing")

        write_result = rt.execute_plan(
            [ToolInvocation("document_apply_rewrite", {"path": sample.name, "old_text": "执行力第一", "new_text": "执行优先"})],
            workspace=workspace,
            user_message="把文档里的执行力第一改成执行优先，生成修订副本",
        )
        _assert(write_result.results and write_result.results[0].ok, "document_apply_rewrite failed")
        data = write_result.results[0].data
        _assert(data.get("operation_id", "").startswith("docwrite_"), "operation_id missing")
        target = workspace / data["target"]
        manifest = workspace / data["manifest"]
        _assert(target.exists(), "rewrite target missing")
        _assert(manifest.exists(), "writeback manifest missing")
        _assert("执行优先" in target.read_text(encoding="utf-8"), "replacement not applied")
        _assert("执行力第一" in sample.read_text(encoding="utf-8"), "default copy mode must not overwrite source")
        _assert("# 临渊者文档写回样本" not in write_result.results[0].output_summary and "A5 Only 治理" not in write_result.results[0].output_summary, "document body leaked to summary")

        rollback = rt.execute_plan(
            [ToolInvocation("document_rollback", {"operation_id": data["operation_id"]})],
            workspace=workspace,
            user_message="回滚刚才文档写回",
        )
        _assert(rollback.results and rollback.results[0].ok, "document_rollback failed")
        _assert(not target.exists(), "rollback should delete generated copy when no previous target existed")

        pdf = workspace / "sample.pdf"
        pdf.write_bytes(b"%PDF-1.4\n% guarded fake pdf\n")
        pdf_result = rt.execute_plan(
            [ToolInvocation("document_apply_rewrite", {"path": pdf.name, "old_text": "A", "new_text": "B"})],
            workspace=workspace,
            user_message="修改 pdf",
        )
        _assert(pdf_result.results and pdf_result.results[0].status.value == "blocked", "pdf writeback should be blocked with clear diagnostic")
        _assert(pdf_result.results[0].error_code == "pdf_writeback_unsupported", "pdf error code mismatch")

        alias_plan = validate_and_build_plan({"steps": [{"tool_name": "documentWriteback", "arguments": {"path": "sample_note.md", "old_text": "A", "new_text": "B"}}]})
        _assert(alias_plan[0].tool_name == "document_apply_rewrite", "documentWriteback alias not normalized")
        rollback_plan = validate_and_build_plan({"steps": [{"tool_name": "documentRollback", "arguments": {"operation_id": "docwrite_12345678"}}]})
        _assert(rollback_plan[0].tool_name == "document_rollback", "documentRollback alias not normalized")

        bridge = PlanBridge()
        apply_plan = bridge.build_plan("把刚才文档里的执行力第一改成执行优先并写回")
        _assert(apply_plan and apply_plan[0].tool_name == "document_apply_rewrite", "PlanBridge explicit rewrite should route to document_apply_rewrite")
        rb_plan = bridge.build_plan("回滚文档写回 docwrite_1234567890abcdef")
        _assert(rb_plan and rb_plan[0].tool_name == "document_rollback", "PlanBridge rollback should route to document_rollback")
        chat_plan = bridge.build_plan("你会做什么")
        _assert(chat_plan == [], "normal chat should not trigger task plan")

        rc = RiskClassifier()
        _assert(rc.classify(ToolInvocation("document_apply_rewrite", {"path": "x.md"}))[0].value == "A3", "document_apply_rewrite risk not A3")
        _assert(rc.classify(ToolInvocation("document_rollback", {"operation_id": "x"}))[0].value == "A3", "document_rollback risk not A3")

        print(json.dumps({
            "status": "passed",
            "workspace": _public_tmp(workspace),
            "operation_id": data.get("operation_id"),
            "checks": [
                "document_apply_rewrite_registered",
                "dry_run_no_write",
                "copy_mode_no_source_overwrite",
                "manifest_and_operation_id",
                "rollback_deletes_generated_copy",
                "pdf_writeback_guard",
                "plan_schema_aliases",
                "plan_bridge_apply_and_rollback",
                "normal_chat_no_task_trigger",
                "risk_levels",
            ],
        }, ensure_ascii=False, indent=2))
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    main()
