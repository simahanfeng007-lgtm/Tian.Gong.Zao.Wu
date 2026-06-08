from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def make_sample_repo(root: Path) -> None:
    (root / "src").mkdir(parents=True, exist_ok=True)
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "src" / "calc.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (root / "tests" / "test_calc.py").write_text("from src.calc import add\n\ndef test_add():\n    assert add(1, 2) == 3\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\npythonpath=['.']\n", encoding="utf-8")


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="codex_runtime_smoke_") as tmp:
        repo = Path(tmp)
        make_sample_repo(repo)
        runtime = RuntimeEntry()
        plan = [
            ToolInvocation("code_x_runtime_status", {}),
            ToolInvocation("repo_map", {}),
            ToolInvocation("issue_to_file_localizer", {"issue_text": "add function behavior"}),
            ToolInvocation("workspace_snapshot", {}),
            ToolInvocation("workspace_patch_applier", {"edit_units": [{"edit_type": "create_file", "path": "src/new_feature.py", "content": "VALUE = 42\n"}]}),
            ToolInvocation("python_quality_runner", {}),
            ToolInvocation("failure_attribution_analyzer", {"log_text": "SyntaxError: invalid syntax"}),
            ToolInvocation("code_x_package_workflow", {"include_paths": ["src"], "output_zip": "dist/code_x_delivery.zip"}),
        ]
        result = runtime.execute_plan(plan, workspace=repo, user_message="Code-X runtime usable smoke", max_steps=20)
        payload = {
            "ok": all(item.ok for item in result.results),
            "tool_count": len(runtime.registry.names()),
            "code_x_tools_present": all(name in runtime.registry.names() for name in ["repo_map", "workspace_patch_applier", "python_quality_runner", "code_x_package_workflow"]),
            "results": [
                {"tool_name": item.tool_name, "status": item.status.value, "error_code": item.error_code, "summary": item.output_summary[:300]}
                for item in result.results
            ],
            "zip_created": (repo / "dist" / "code_x_delivery.zip").exists(),
        }
        out = Path("reports") / "l6702_codex_runtime_smoke_report.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps({"ok": payload["ok"], "report": str(out), "tool_count": payload["tool_count"]}, ensure_ascii=False, indent=2))
        return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
