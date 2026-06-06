from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports" / "l6_47_freeze_baseline"


def test_l6_47_freeze_manifest_exists_and_covers_21_steps() -> None:
    manifest_path = REPORT_DIR / "freeze_baseline_manifest.json"
    assert manifest_path.exists()
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert payload["schema"] == "tiangong.l6.47.four_path_freeze_baseline.v1"
    assert payload["status"] == "frozen"
    assert payload["p0_p1_issues_found"] is False
    assert len(payload["steps"]) == 21
    assert [item["no"] for item in payload["steps"]] == list(range(1, 22))
    assert all(item["status"] == "completed" for item in payload["steps"])


def test_l6_47_core_pollution_check_is_clean() -> None:
    payload = json.loads((REPORT_DIR / "freeze_baseline_manifest.json").read_text(encoding="utf-8"))
    check = payload["core_pollution_check"]
    assert check["status"] == "PASS"
    assert check["changed_core_files"] == 0
    assert check["checked_core_files"] >= 500


def test_l6_47_static_boundary_scan_has_no_offenders() -> None:
    payload = json.loads((REPORT_DIR / "freeze_baseline_manifest.json").read_text(encoding="utf-8"))
    scan = payload["static_boundary_scan"]
    assert scan["status"] == "PASS"
    offenders = [item for item in scan["offenders"] if item["class"] == "offender"]
    assert offenders == []


def test_l6_47_all_required_runtime_modules_present() -> None:
    payload = json.loads((REPORT_DIR / "freeze_baseline_manifest.json").read_text(encoding="utf-8"))
    modules = {item["path"]: item for item in payload["module_manifest"]}
    required = {
        "tiangong_agent_runtime/memory_math_core.py",
        "tiangong_agent_runtime/memory_store_bridge.py",
        "tiangong_agent_runtime/affective_state.py",
        "tiangong_agent_runtime/affective_execution_route.py",
        "tiangong_agent_runtime/lifecycle_coordinator.py",
        "tiangong_agent_runtime/lifecycle_clock.py",
        "tiangong_agent_runtime/autonomous_goal_queue.py",
        "tiangong_agent_runtime/self_iteration_frontend_projection.py",
        "tiangong_agent_runtime/four_path_context_router.py",
        "tiangong_agent_runtime/planner_unified_consumption.py",
        "tiangong_agent_runtime/budget_low_friction_governance.py",
        "tiangong_agent_runtime/rollback_audit_binding.py",
        "tiangong_agent_runtime/long_chain_failure_injection_harness.py",
    }
    assert required.issubset(set(modules))
    assert all(modules[path]["exists"] is True for path in required)


def test_l6_47_freeze_reports_are_present() -> None:
    assert (REPORT_DIR / "l6_47_21_step_freeze_matrix.md").exists()
    assert (REPORT_DIR / "l6_47_freeze_index.md").exists()
    assert (REPORT_DIR / "l6_47_freeze_handoff.txt").exists()
    report = ROOT / "docs" / "L6_47_四主路径冻结基线_交付报告_20260606.txt"
    assert report.exists()
    text = report.read_text(encoding="utf-8")
    assert "changed_core_files：0" in text
    assert "未发现 P0/P1 问题" in text
