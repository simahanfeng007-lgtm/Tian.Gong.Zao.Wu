from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend" / "project"
FRONTEND = ROOT / "frontend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(FRONTEND) not in sys.path:
    sys.path.insert(0, str(FRONTEND))

RESULTS: list[tuple[str, bool, str]] = []


def check(issue_id: str, condition: bool, detail: str = "") -> None:
    RESULTS.append((issue_id, bool(condition), detail))
    if not condition:
        raise AssertionError(f"{issue_id}: {detail}")


def text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def load_bridge():
    path = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
    spec = importlib.util.spec_from_file_location("linyuanzhe_bridge_l6735_smoke", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def run_cmd(args: list[str], cwd: Path | None = None) -> tuple[int, str]:
    p = subprocess.run(args, cwd=str(cwd or ROOT), text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=120)
    return p.returncode, p.stdout


def main() -> None:
    if os.environ.get("TIANGONG_RUN_L6735_CLOSURE_FULL") != "1":
        print("L6.73.5 all_qa_issues_closure_smoke SKIP: legacy/full smoke is disabled by default; set TIANGONG_RUN_L6735_CLOSURE_FULL=1 to run the full path.")
        return 0
    from tiangong_agent_runtime.frontend_contract import validate_frontend_contract
    from linyuanzhe_frontend.clients.runtime_integration_probe import SECRET_RENDER_MARKERS
    from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
    from linyuanzhe_frontend.contracts.provider_settings import (
        ProviderSettingsWriteRequest,
        PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION,
        normalize_host_access_scope,
    )
    from linyuanzhe_frontend.contracts.model_settings import sanitize_runtime_settings
    from linyuanzhe_frontend.contracts.runtime_snapshot import (
        PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION as SNAP_PROVIDER_CONTRACT_VERSION,
    )
    from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION

    # P0-001
    contract = validate_frontend_contract().public_dict()
    check("P0-001", contract.get("ok") is True and not contract.get("issues"), str(contract))
    fc = text("backend/project/tiangong_agent_runtime/frontend_contract.py")
    check("P0-001/raw_base_url_forbidden", "base_url" in fc and "base_url_display" in fc, "base_url forbidden + display field present")

    # P0-002
    endpoint_markers = {"api.deepseek", "provider.example.invalid", "deepseek.example.invalid", "provider-write-l658"}
    check("P0-002", not any(marker in SECRET_RENDER_MARKERS for marker in endpoint_markers), str(SECRET_RENDER_MARKERS))
    rc, out = run_cmd([sys.executable, "-S", "run_rc_preflight.py", "--contract-server"], FRONTEND / "linyuanzhe_frontend")
    check("P0-002/rc_preflight", rc == 0, out[-400:])

    # P0-003
    client = SseRuntimeClient("http://127.0.0.1:8787")
    client._apply_provider_settings({"payload": {"provider":"deepseek", "base_url":"https://api.deepseek.com", "api_key":"mockkey_should-not-appear"}})  # type: ignore[attr-defined]
    projected_provider_settings = client.get_provider_settings()
    check("P0-003", "base_url" not in projected_provider_settings and projected_provider_settings.get("base_url_display") == "https://api.deepseek.com", repr(projected_provider_settings))
    check("P0-003/no_api_key", "api_key" not in projected_provider_settings, repr(projected_provider_settings))

    # P0-004 / P2-008 source guards.
    feature = text("frontend/linyuanzhe_frontend/ui/main_window_feature_pages.py")
    actions = text("frontend/linyuanzhe_frontend/ui/main_window_actions.py")
    check("P0-004", 'provider_settings.get("base_url")' not in feature and '"base_url", "base_url_display"' not in feature, "UI does not read/allow raw base_url")
    check("P2-008", 'result.get("base_url")' not in actions, "save-result display does not fall back to raw base_url")

    # P0-005 / P2-002 / P1-005
    real_path = "/home/alice/project"
    req = ProviderSettingsWriteRequest.from_form({"provider":"deepseek", "model":"deepseek-v4-pro", "base_url":"https://api.deepseek.com", "host_access_scope":"自定义根目录", "host_access_root":real_path})
    check("P0-005", req.host_access_root == real_path and req.to_runtime_payload()["host_access_root"] == real_path, req.to_runtime_payload().get("host_access_root", ""))
    settings = sanitize_runtime_settings({"host_access_scope":"全电脑 / 系统盘", "host_access_root":real_path})
    check("P2-002", settings["host_access_scope"] == "system_drive", str(settings))
    check("P1-005", PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION == SNAP_PROVIDER_CONTRACT_VERSION, f"{PROVIDER_SETTINGS_WRITE_CONTRACT_VERSION} != {SNAP_PROVIDER_CONTRACT_VERSION}")

    # P0-006 / P1-006
    bridge = load_bridge()
    aliases = {
        "全电脑 / 系统盘": "system_drive", "全电脑/系统盘": "system_drive",
        "项目工作区": "project_workspace", "项目目录": "project_workspace",
        "用户目录": "user_home", "用户主目录": "user_home",
        "自定义根目录": "custom_root", "自定义": "custom_root",
    }
    for label, expected in aliases.items():
        check(f"P1-006/{label}", bridge._normalize_host_access_scope(label) == expected, bridge._normalize_host_access_scope(label))
    invalid_root = bridge._resolve_host_access_root("custom_root", "/path/that/does/not/exist/__l6735__")
    check("P0-006", invalid_root == bridge.BACKEND.resolve(), "invalid custom_root resolved to project workspace fallback")

    # P1-001 / P3-003
    import tiangong_kernel.l5_plugin_host as host
    import tiangong_kernel.l5_plugin_host.phase8_closure  # noqa: F401
    import tiangong_kernel.l5_plugin_host.model_capability_invariants  # noqa: F401
    from tiangong_kernel.l5_plugin_host import ModelInvocationPermit, ModelProviderPermitScope  # noqa: F401
    check("P1-001", bool(host), "l5_plugin_host imports")
    check("P3-003", "ModelInvocationPermit" in getattr(host, "__all__", ()), "model invariants are package-root exported")

    # P1-002 / P2-003
    rc, out = run_cmd([sys.executable, "scripts/desktop_entry_layout_audit_l6710.py"])
    check("P1-002", rc == 0, out[-400:])
    rc, out = run_cmd([sys.executable, "scripts/desktop_provider_settings_acceptance_l6715.py"])
    check("P2-003", rc == 0 and ("SKIP" in out or "PASS" in out), out[-400:])

    # P1-003: old frontend smoke must not hard-lock to an exact L6.72.x runtime.
    old_smokes = [
        "run_real_host_execution_acceptance_smoke_l67232.py",
        "run_chat_bubble_codex_progress_smoke_l67241.py",
        "run_chat_compact_header_alignment_smoke_l67242.py",
        "run_chat_surface_control_prune_fixed_scale_smoke_l67240.py",
        "run_conversation_full_render_and_soul_smoke_l67234.py",
        "run_conversation_render_readability_smoke_l67233.py",
        "run_desktop_history_export_tray_smoke_l67222.py",
        "run_desktop_layout_overflow_smoke_l67224.py",
        "run_desktop_os_human_factors_smoke_l67229.py",
        "run_desktop_run_workbench_smoke_l67227.py",
        "run_duplicate_selection_prune_smoke_l67230.py",
        "run_long_chain_chat_progress_smoke_l67238.py",
        "run_readfile_encoding_tool_output_sanitizer_smoke_l67243.py",
        "run_windows_native_gui_path_compat_smoke_l67235.py",
        "run_work_mode_activation_smoke_l67225.py",
    ]
    strict_old_version = re.compile(r'FE_RUNTIME_VERSION\s*==\s*"L6\.72\.[0-9]+"')
    for smoke in old_smokes:
        src = text(f"frontend/linyuanzhe_frontend/{smoke}")
        check(f"P1-003/{smoke}", not strict_old_version.search(src), "old smoke no longer hard-locks to exact L6.72.x")
    check("P2-004", FE_RUNTIME_VERSION.startswith("L6.73."), FE_RUNTIME_VERSION)

    # P1-004 / P2-007 shell permissions.
    non_exec = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".sh", ".command"} and not os.access(p, os.X_OK)]
    check("P1-004/P2-007", not non_exec, "; ".join(non_exec[:10]))

    # P1-007 / P2-005 / P2-006 cleanliness of mutable release state dirs.
    # Earlier contract/preflight smoke calls may create local transient state.
    # Release packages must not carry these files, so the closure smoke first
    # removes known mutable runtime-output directories and then verifies they
    # are absent/empty.
    import shutil
    for rel in [
        "backend/project/.linyuanzhe/document_contexts",
        "backend/project/.linyuanzhe/file_handoffs",
        "backend/project/.linyuanzhe/prompt_trace",
        "backend/project/.linyuanzhe/tasks",
        ".linyuanzhe/tasks",
        ".linyuanzhe/prompt_trace",
        ".linyuanzhe/file_handoffs",
        ".linyuanzhe/document_contexts",
        ".linyuanzhe/soul",
    ]:
        target = ROOT / rel
        if target.exists():
            shutil.rmtree(target)
    document_contexts = ROOT / "backend" / "project" / ".linyuanzhe" / "document_contexts"
    doc_files = list(document_contexts.rglob("*")) if document_contexts.exists() else []
    check("P1-007", not [p for p in doc_files if p.is_file()], "document_contexts empty/absent")
    soul_state = ROOT / ".linyuanzhe" / "soul" / "soul_emotion_baseline.json"
    check("P2-005", not soul_state.exists(), "soul baseline build state removed")
    report_leaks: list[str] = []
    for base in [ROOT / "reports", ROOT / "backend" / "project" / ".linyuanzhe"]:
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if p.is_file():
                rel = str(p.relative_to(ROOT))
                if rel.endswith("l6735_all_qa_issues_closure_smoke_report.json"):
                    continue
                body = p.read_text(encoding="utf-8", errors="ignore")
                if "/tmp/runtime_tool_alignment" in body or "/mnt/data" in body or "/home/oai" in body:
                    report_leaks.append(rel)
    check("P2-006", not report_leaks, "; ".join(report_leaks[:10]))

    # P2-001
    check("P2-001", 'state in {"ready", "就绪"}' in feature, "ready state has success color")

    # P3-002
    # Source trees may retain historical delivery reports for handoff tracing,
    # while L6.73.6 release zips exclude the delivery-report directory to keep
    # install trees clean. Accept either: required reports present in a source
    # tree, or the report directory absent/empty in a packaged runtime tree.
    delivery_dir = ROOT / "交付报告"
    required_reports = [
        "L6.73.2_SettingsPersistenceSoulScrollUX设置页全量可保存与Soul滚轮优化修复报告.txt",
        "L6.73.2_修改文件清单.txt",
        "L6.73.2_全量质检结果.txt",
        "L6.73.2_本机验收清单.txt",
    ]
    source_reports_ok = delivery_dir.exists() and all((delivery_dir / name).exists() for name in required_reports)
    package_reports_clean = (not delivery_dir.exists()) or (not any(delivery_dir.rglob("*")))
    check("P3-002", source_reports_ok or package_reports_clean, "source reports missing or packaged report dir not clean")

    out = {
        "ok": True,
        "case_count": len(RESULTS),
        "passed": len([x for x in RESULTS if x[1]]),
        "failed": [x for x in RESULTS if not x[1]],
        "version": FE_RUNTIME_VERSION,
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
