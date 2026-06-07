from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent


def run(cmd: list[str], cwd: Path) -> dict:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=90)
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": cmd,
            "returncode": 124,
            "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr": ((exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "") + "\nTIMEOUT",
        }
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "stdout": proc.stdout[-4000:],
        "stderr": proc.stderr[-4000:],
    }


def main() -> int:
    results: dict = {
        "version": "L6-FE.01 STEP19 / L6.58",
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "root": str(ROOT),
    }

    required = [
        "app.py",
        "DEMO_START_HERE.txt",
        "README_FE01.txt",
        "requirements.txt",
        "run_desktop_demo.py",
        "run_desktop_demo.bat",
        "run_desktop_demo.sh",
        "run_runtime_sse_demo.py",
        "run_runtime_sse_demo.bat",
        "run_runtime_sse_demo.sh",
        "run_backend_integration_smoke.py",
        "run_backend_integration_smoke.bat",
        "run_backend_integration_smoke.sh",
        "run_rc_preflight.py",
        "run_rc_preflight.bat",
        "run_rc_preflight.sh",
        "run_validation.bat",
        "run_validation.sh",
        "contracts/runtime_client.py",
        "contracts/runtime_snapshot.py",
        "contracts/model_settings.py",
        "contracts/product_identity.py",
        "contracts/sse_events.py",
        "contracts/runtime_controls.py",
        "contracts/agent_ui_events.py",
        "contracts/streaming_render.py",
        "contracts/action_guard.py",
        "contracts/integration_smoke.py",
        "contracts/provider_settings.py",
        "contracts/rc_readiness.py",
        "clients/mock_runtime_client.py",
        "clients/json_report_runtime_client.py",
        "clients/future_runtime_client.py",
        "clients/sse_runtime_client.py",
        "clients/runtime_integration_probe.py",
        "ui/main_window.py",
        "ui/theme.py",
        "ui/widgets.py",
        "ui/page_specs.py",
        "ui/visual_spec.py",
        "ui/design_tokens.py",
        "tokens/linyuanzhe_design_tokens.json",
        "mock_data/runtime_snapshot_mock.json",
        "tests/smoke_test_frontend.py",
        "tests/gui_construct_smoke.py",
        "tests/test_frontend_contracts.py",
        "tests/test_l6_52_sse_runtime_client.py",
        "tests/test_l6_53_streaming_controls.py",
        "tests/test_l6_54_smooth_agent_ui.py",
        "tests/test_l6_55_action_guard_cards.py",
        "tests/test_l6_56_e2e_integration_smoke.py",
        "tests/test_l6_57_provider_settings_writeback.py",
        "tests/test_l6_58_rc_preflight.py",
        "docs/demo_manifest_step09.json",
        "docs/demo_manifest_step10b.json",
        "docs/homepage_screenshot_acceptance_step10b.txt",
        "docs/demo_manifest_step12.json",
        "docs/demo_manifest_step13.json",
        "docs/demo_manifest_step14.json",
        "docs/demo_manifest_step15.json",
        "docs/demo_manifest_step16.json",
        "docs/demo_manifest_step17.json",
        "docs/demo_manifest_step18.json",
        "docs/demo_manifest_step19.json",
        "docs/STEP12_启动修复与L6511契约对齐完成报告_20260607.txt",
        "docs/STEP13_L652_Runtime_SSE状态接线完成报告_20260607.txt",
        "docs/STEP14_L653_流式续接错误态与任务控制完成报告_20260607.txt",
        "docs/STEP15_L654_顺滑层AgentUI事件契约与视觉Token完成报告_20260607.txt",
        "docs/STEP16_L655_行动守卫卡审计回滚只读与确认请求UX完成报告_20260607.txt",
        "docs/STEP17_L656_真实后端联调包与端到端桌面烟测完成报告_20260607.txt",
        "docs/STEP18_L657_Provider设置页后端写入回执与密钥状态UX完成报告_20260607.txt",
        "docs/STEP19_L658_真实后端实例联调与RC前置收口完成报告_20260607.txt",
        "docs/secret_scan_step16.json",
        "docs/provider_sdk_import_scan_step16.json",
        "docs/bare_except_pass_scan_step16.json",
        "docs/secret_scan_step17.json",
        "docs/provider_sdk_import_scan_step17.json",
        "docs/bare_except_pass_scan_step17.json",
        "docs/secret_scan_step18.json",
        "docs/provider_sdk_import_scan_step18.json",
        "docs/bare_except_pass_scan_step18.json",
        "docs/secret_scan_step19.json",
        "docs/provider_sdk_import_scan_step19.json",
        "docs/bare_except_pass_scan_step19.json",
    ]
    missing = [item for item in required if not (ROOT / item).exists()]
    results["missing_files"] = missing

    compile_result = run([sys.executable, "-m", "compileall", "-q", str(ROOT)], cwd=PARENT)
    results["compileall"] = compile_result

    smoke_result = run([sys.executable, str(ROOT / "tests" / "smoke_test_frontend.py")], cwd=PARENT)
    results["smoke_test"] = smoke_result

    if os.environ.get("LINYUANZHE_VALIDATE_GUI") == "1":
        gui_cmd = [sys.executable, str(ROOT / "tests" / "gui_construct_smoke.py")]
        gui_result = run(gui_cmd, cwd=PARENT)
    else:
        gui_result = {
            "cmd": ["gui_construct_smoke", "skipped_by_validation_default"],
            "returncode": 0,
            "stdout": "GUI construct smoke is skipped by default in validate_demo_package to avoid headless DISPLAY/Xvfb hangs; run xvfb-run -a python tests/gui_construct_smoke.py for desktop CI.",
            "stderr": "",
        }
    results["gui_construct_smoke"] = gui_result

    pytest_result = run([sys.executable, "-m", "pytest", "-q", str(ROOT / "tests" / "test_frontend_contracts.py"), str(ROOT / "tests" / "test_l6_52_sse_runtime_client.py"), str(ROOT / "tests" / "test_l6_53_streaming_controls.py"), str(ROOT / "tests" / "test_l6_54_smooth_agent_ui.py"), str(ROOT / "tests" / "test_l6_55_action_guard_cards.py"), str(ROOT / "tests" / "test_l6_56_e2e_integration_smoke.py"), str(ROOT / "tests" / "test_l6_57_provider_settings_writeback.py"), str(ROOT / "tests" / "test_l6_58_rc_preflight.py")], cwd=PARENT)
    results["pytest_contracts"] = pytest_result

    integration_report = ROOT / "reports" / "validation_l6_58_real_runtime_e2e_smoke.json"
    integration_result = run([sys.executable, "-m", "linyuanzhe_frontend.run_backend_integration_smoke", "--contract-server", "--out", str(integration_report)], cwd=PARENT)
    results["l6_58_real_runtime_e2e_smoke"] = integration_result

    rc_report = ROOT / "reports" / "validation_l6_58_rc_preflight.json"
    rc_result = run([sys.executable, "-m", "linyuanzhe_frontend.run_rc_preflight", "--contract-server", "--out", str(rc_report)], cwd=PARENT)
    results["l6_58_rc_preflight"] = rc_result

    ok = (
        not missing
        and compile_result["returncode"] == 0
        and smoke_result["returncode"] == 0
        and gui_result["returncode"] == 0
        and pytest_result["returncode"] == 0
        and integration_result["returncode"] == 0
        and rc_result["returncode"] == 0
    )
    results["ok"] = ok

    out = ROOT / "docs" / "validation_step19.json"
    out.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    if ok:
        print("FE.01 STEP19 / L6.58 real runtime RC preflight validation passed")
        print(f"validation_report={out}")
        return 0
    print("FE.01 STEP19 / L6.58 real runtime RC preflight validation failed")
    print(json.dumps(results, ensure_ascii=False, indent=2))
    return 1


if __name__ == "__main__":
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
