"""L6.72.59 模型执行力操作系统 Benchmark + RC smoke。"""

from __future__ import annotations

import os
import json
from pathlib import Path
import tempfile

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")
os.environ.setdefault("TIANGONG_SOUL_BASELINE_PATH", str(Path(tempfile.gettempdir()) / "linyuanzhe_l67259_soul_emotion_baseline.json"))
os.environ.setdefault("LINYUANZHE_STATE_DIR", str(Path(tempfile.mkdtemp(prefix="linyuanzhe_l67259_state_"))))
os.environ.setdefault("TIANGONG_STATE_DIR", os.environ["LINYUANZHE_STATE_DIR"])

from tiangong_agent_runtime.adapters.document_writeback_adapters import document_apply_rewrite_adapter
from tiangong_agent_runtime.model_execution_benchmark import run_model_execution_os_benchmark
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.turn_context import TurnContext


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_document_apply_rewrite_preserves_code_colon() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        target = root / "bad.py"
        target.write_text("def broken()\n    return 1\n", encoding="utf-8")
        result = document_apply_rewrite_adapter(
            ToolInvocation(
                "document_apply_rewrite",
                {
                    "path": "bad.py",
                    "old_text": "def broken()",
                    "new_text": "def broken():",
                    "operation": "replace",
                    "overwrite": True,
                    "allow_no_match": False,
                },
            ),
            TurnContext.create("修复 bad.py 缺失冒号", workspace=root),
        )
        assert_true(result.ok, f"document_apply_rewrite should succeed: {result.output_summary}")
        assert_true("def broken():" in target.read_text(encoding="utf-8-sig"), "code colon must be physically preserved")


def test_l67259_benchmark_rc() -> None:
    with tempfile.TemporaryDirectory() as td:
        report = run_model_execution_os_benchmark(Path(td))
        payload = report.public_dict()
        assert_true(report.ok and report.rc_ready, json.dumps(payload, ensure_ascii=False, indent=2))
        metrics = payload["metrics"]
        assert_true(metrics["false_completed_count"] == 0, "false_completed_count must be zero")
        assert_true(metrics["chat_transcript_pollution_count"] == 0, "chat transcript pollution must be zero")
        assert_true(metrics["recovery_success_rate"] >= 1.0, "recovery task must pass")
        assert_true(metrics["artifact_delivery_rate"] >= 0.85, "artifact delivery rate below L6.72.59 RC threshold")
        case_ids = {case["case_id"] for case in payload["cases"]}
        expected = {"simple_file_task", "code_micro_fix", "code_multifile_fix", "document_task", "recovery_task", "long_chain_delivery", "weak_model_block"}
        assert_true(expected.issubset(case_ids), f"benchmark cases missing: {expected - case_ids}")


def main() -> None:
    test_document_apply_rewrite_preserves_code_colon()
    test_l67259_benchmark_rc()
    print("L6.72.59 ModelExecutionOS Benchmark RC smoke PASS")


if __name__ == "__main__":
    main()
