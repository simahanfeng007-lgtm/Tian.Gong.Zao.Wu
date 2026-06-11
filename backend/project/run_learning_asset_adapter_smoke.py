from __future__ import annotations

import argparse
import json
import os
import sys
sys.dont_write_bytecode = True
import tempfile
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.learning_asset_adapter import TEMPLATES


def _default_report_path() -> Path:
    report_dir = os.environ.get("TIANGONG_REPORT_DIR") or os.environ.get("LINYUANZHE_REPORT_DIR")
    if report_dir:
        return Path(report_dir) / "l6702_r21_learning_asset_adapter_smoke_report.json"
    return Path(tempfile.mkdtemp(prefix="r21_learning_asset_report_")) / "l6702_r21_learning_asset_adapter_smoke_report.json"


def _public_report_path(path: Path) -> str:
    try:
        tmp_root = Path(tempfile.gettempdir()).resolve()
        resolved = path.resolve()
        if tmp_root in [resolved, *resolved.parents]:
            return "<tmp>/" + resolved.relative_to(tmp_root).as_posix()
    except Exception:
        pass
    return path.name


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="L6.73.8 learning asset adapter smoke; defaults to temporary workspace/report paths.")
    parser.add_argument("--workspace", default="", help="显式 smoke workspace；未指定时使用 TemporaryDirectory，结束自动清理。")
    parser.add_argument("--out", default="", help="显式报告路径；未指定时写入临时目录或 TIANGONG_REPORT_DIR。")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="r21_adapter_smoke_workspace_") as tmp:
        workspace = Path(args.workspace).resolve() if args.workspace else Path(tmp)
        workspace.mkdir(parents=True, exist_ok=True)
        runtime = RuntimeEntry()
        result = runtime.run_text("asset-adapter drill", workspace=workspace, max_steps=20)
        drill = result.results[3].data if len(result.results) > 3 else {}
        direct_calls = []
        activation = drill.get("activation_report") if isinstance(drill, dict) else {}
        for record in activation.get("activated_assets", []) if isinstance(activation, dict) else []:
            if not isinstance(record, dict):
                continue
            tool_name = str(record.get("tool_name") or "")
            template_id = str(record.get("adapter_template_id") or "")
            if not tool_name.startswith("learned_tool_") or template_id not in TEMPLATES:
                continue
            direct = runtime.execute_plan(
                [ToolInvocation(tool_name, dict(TEMPLATES[template_id].smoke_args))],
                workspace=workspace,
                user_message=f"R21 adapter smoke direct {template_id}",
                max_steps=3,
            )
            item = direct.results[0] if direct.results else None
            direct_calls.append({
                "tool_name": tool_name,
                "adapter_template_id": template_id,
                "ok": bool(item and item.ok),
                "status": item.status.value if item else "missing",
                "output_summary": item.output_summary[:280] if item else "",
                "candidate_status": item.data.get("data", {}).get("candidate_output", {}).get("status") if item and isinstance(item.data, dict) else "",
            })
        report = {
            "schema": "tiangong.l6702.r21.learning_asset_adapter_smoke_report.v2",
            "ok": all(item.ok for item in result.results) and bool(direct_calls) and all(row["ok"] for row in direct_calls),
            "plan": [step.tool_name for step in result.plan],
            "result_statuses": [item.status.value for item in result.results],
            "template_count": 5,
            "runtime_tool_count_after_drill": len(runtime.registry.names()),
            "workspace_mode": "explicit" if args.workspace else "temporary_cleaned",
            "drill": drill,
            "direct_calls": direct_calls,
        }
        out = Path(args.out) if args.out else _default_report_path()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({
            "ok": report["ok"],
            "report": _public_report_path(out),
            "workspace_mode": report["workspace_mode"],
            "template_count": report["template_count"],
            "runtime_tool_count_after_drill": report["runtime_tool_count_after_drill"],
            "direct_calls": len(direct_calls),
        }, ensure_ascii=False, indent=2))
        return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
