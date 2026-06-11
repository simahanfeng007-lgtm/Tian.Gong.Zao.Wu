"""Q19 verifier: historical entries + real folder/Desktop/Downloads/permission boundary.

Offline and CI-safe:
- historical heavy/GUI entries must return PASS or explicit SKIP quickly
- no package-root reports/.linyuanzhe/pycache pollution
- Desktop headless failure must be controlled and write only to user reports
- Downloads/workspace with spaces + Unicode can complete mock LLM write/pack loop
- workspace traversal attempts are blocked
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True


def _fail(message: str, *, stdout: str = "", stderr: str = "", package_root: Path | None = None, workspace: Path | None = None) -> int:
    def redact(text: str) -> str:
        value = str(text or "")
        if package_root is not None:
            value = value.replace(str(package_root), "<package-root>")
        if workspace is not None:
            value = value.replace(str(workspace), "<workspace>")
        value = value.replace(tempfile.gettempdir(), "<tmp-root>")
        return value[:5000]

    print(f"FAIL Q19 history/permission verifier: {message}")
    if stdout:
        print("--- stdout ---")
        print(redact(stdout))
    if stderr:
        print("--- stderr ---")
        print(redact(stderr))
    return 1


def _snapshot_pollution(package_root: Path) -> set[str]:
    polluted: set[str] = set()
    for rel in (".linyuanzhe", "reports", "backend/project/reports", "frontend/linyuanzhe_frontend/reports"):
        if (package_root / rel).exists():
            polluted.add(rel)
    for p in package_root.rglob("__pycache__"):
        polluted.add(str(p.relative_to(package_root)))
    for p in package_root.rglob("*.pyc"):
        polluted.add(str(p.relative_to(package_root)))
    return polluted


def _run_py(package_root: Path, rel: str, *, timeout: int = 20, args: list[str] | None = None, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update(
        {
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8:replace",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "TIANGONG_SOUL_BASELINE_PERSIST": "0",
        }
    )
    if env_extra:
        env.update(env_extra)
    return subprocess.run(
        [sys.executable, "-S", rel, *(args or [])],
        cwd=str(package_root),
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )


def _run_shell(package_root: Path, rel: str, *, timeout: int = 12, env_extra: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = dict(os.environ)
    env.update({"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8:replace", "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1"})
    if env_extra:
        env.update(env_extra)
    return subprocess.run(["bash", rel], cwd=str(package_root), env=env, capture_output=True, text=True, timeout=timeout, check=False)


def _assert_no_package_leak(package_root: Path, text: str, label: str) -> None:
    if str(package_root) in text:
        raise AssertionError(f"{label} leaked package absolute path")


def _assert_no_pollution(package_root: Path, before: set[str], label: str) -> None:
    after = _snapshot_pollution(package_root)
    new_items = sorted(after - before)
    if new_items:
        raise AssertionError(f"{label} polluted package root: {new_items[:20]}")


def _history_entry_matrix(package_root: Path) -> None:
    before = _snapshot_pollution(package_root)
    cases: list[tuple[str, int, tuple[str, ...]]] = [
        ("backend/project/run_bat_line_ending_smoke_l67219.py", 8, ("PASS",)),
        ("backend/project/run_bridge_network_asset_smoke_l67218.py", 12, ("PASS",)),
        ("backend/project/run_l67254_no_silent_chat_fallback_smoke.py", 12, ("PASS",)),
        ("backend/project/run_codex_runtime_smoke.py", 8, ("SKIP",)),
        ("backend/project/run_l67251_full_quality_smoke.py", 8, ("SKIP",)),
        ("backend/project/run_l6731_sandbox_chat_upload_handoff_smoke.py", 8, ("SKIP",)),
        ("backend/project/run_l6735_all_qa_issues_closure_smoke.py", 8, ("SKIP",)),
        ("backend/project/run_l6736_extra_qa_round4_round5_closure_smoke.py", 8, ("SKIP",)),
        ("backend/project/run_l6737_extra_qa_round6_round7_closure_smoke.py", 8, ("SKIP",)),
        ("backend/project/run_l6738_extra_qa_round8_round9_closure_smoke.py", 8, ("SKIP",)),
        ("backend/project/run_no_pyc_compile_check_l6738.py", 25, ('"ok": true',)),
        ("frontend/linyuanzhe_frontend/run_duplicate_selection_prune_smoke_l67230.py", 8, ("PASS",)),
        ("frontend/linyuanzhe_frontend/run_runtime_sse_demo.py", 8, ("SKIP",)),
        ("backend/project/run_l6733_real_acceptance_special_cases_smoke.py", 12, ('"ok": true', '"report": "<tmp>/')),
        ("backend/project/run_document_context_query_export_smoke_l67245.py", 12, ('"status": "passed"', '"workspace": "<tmp>/')),
        ("backend/project/run_document_writeback_rollback_smoke_l67246.py", 12, ('"status": "passed"', '"workspace": "<tmp>/')),
    ]
    for rel, timeout, markers in cases:
        proc = _run_py(package_root, rel, timeout=timeout)
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            raise AssertionError(f"{rel} rc={proc.returncode}: {output[:1200]}")
        for marker in markers:
            if marker not in output:
                raise AssertionError(f"{rel} missing marker {marker!r}: {output[:1200]}")
        _assert_no_package_leak(package_root, output, rel)
        _assert_no_pollution(package_root, before, rel)


def _desktop_headless_boundary(package_root: Path) -> None:
    before = _snapshot_pollution(package_root)
    home = Path(tempfile.mkdtemp(prefix="q19_home_"))
    try:
        (home / "Desktop").mkdir()
        (home / "Downloads").mkdir()
        proc = _run_shell(
            package_root,
            "00_ASCII_START_HERE/linux_macos/start_desktop_auto_l6719.sh",
            timeout=12,
            env_extra={"HOME": str(home), "DISPLAY": "", "WAYLAND_DISPLAY": ""},
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode not in (0, 12):
            raise AssertionError(f"desktop entry rc={proc.returncode}: {output[:1200]}")
        if "<package-root>" not in output:
            raise AssertionError(f"desktop entry did not redact package root: {output[:1200]}")
        if "启动失败报告：<user-reports>/" not in output:
            raise AssertionError(f"desktop failure report not routed to user reports: {output[:1200]}")
        _assert_no_package_leak(package_root, output, "desktop entry")
        _assert_no_pollution(package_root, before, "desktop entry")
    finally:
        shutil.rmtree(home, ignore_errors=True)


def _downloads_write_fix_pack_boundary(package_root: Path) -> None:
    before = _snapshot_pollution(package_root)
    home = Path(tempfile.mkdtemp(prefix="q19_home_downloads_"))
    try:
        downloads = home / "Downloads"
        desktop = home / "Desktop"
        downloads.mkdir()
        desktop.mkdir()
        workspace = downloads / "临渊者 Workspace With Spaces"
        workspace.mkdir()
        state = workspace / "_state"
        env = {
            "HOME": str(home),
            "TIANGONG_ALLOW_INTERNAL_MOCK": "1",
            "LINYUANZHE_FRONTEND_WORK_MODE": "work",
            "TIANGONG_SOUL_BASELINE_PERSIST": "0",
            "LINYUANZHE_STATE_DIR": str(state),
            "TIANGONG_STATE_DIR": str(state),
            "TIANGONG_PROMPT_TRACE_FILE": str(state / "prompt_trace" / "prompt_trace.jsonl"),
            "TIANGONG_PROMPT_TUNER_FILE": str(state / "prompt_trace" / "prompt_tuning_state.json"),
        }
        proc = _run_py(
            package_root,
            "backend/project/run_agent.py",
            timeout=40,
            args=[
                "--mock",
                "--workspace",
                str(workspace),
                "--once",
                "请模拟LLM进行长链工作：创建 Q19_DOWNLOAD_BOUNDARY.txt 内容：download boundary ok；修复项目；运行测试；打包交付；输出总结。",
                "--max-steps",
                "8",
            ],
            env_extra=env,
        )
        output = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode != 0:
            raise AssertionError(f"download workspace run_agent rc={proc.returncode}: {output[:1600]}")
        if "[工作链]" not in output or "failures=0" not in output:
            raise AssertionError(f"download workspace long-chain did not complete: {output[:1600]}")
        if str(workspace) in output or str(package_root) in output:
            raise AssertionError("download workspace output leaked absolute paths")
        target = workspace / "Q19_DOWNLOAD_BOUNDARY.txt"
        if not target.exists() or "download boundary ok" not in target.read_text(encoding="utf-8"):
            raise AssertionError("download workspace marker file missing")
        zips = list((workspace / "dist").glob("*.zip"))
        if not zips:
            raise AssertionError("download workspace package zip missing")
        with zipfile.ZipFile(zips[0]) as zf:
            names = zf.namelist()
            if any(name.startswith("/") or ".." in Path(name).parts for name in names):
                raise AssertionError("download workspace zip contains unsafe paths")
        _assert_no_pollution(package_root, before, "download workspace run")
    finally:
        shutil.rmtree(home, ignore_errors=True)


def _permission_boundary(package_root: Path) -> None:
    before = _snapshot_pollution(package_root)
    project = package_root / "backend" / "project"
    if str(project) not in sys.path:
        sys.path.insert(0, str(project))
    from tiangong_agent_runtime.runtime_entry import RuntimeEntry
    from tiangong_agent_runtime.tool_invocation import ToolInvocation

    parent = Path(tempfile.mkdtemp(prefix="q19_permission_"))
    try:
        workspace = parent / "workspace"
        workspace.mkdir()
        outside = parent / "outside.txt"
        outside.write_text("secret", encoding="utf-8")
        runtime = RuntimeEntry()
        blocked = runtime.execute_plan(
            [ToolInvocation("read_file", {"path": "../outside.txt"})],
            workspace=workspace,
            user_message="permission boundary read",
            max_steps=1,
        )
        first = blocked.results[0]
        if first.ok or first.status.value != "blocked" or first.error_code != "workspace_violation":
            raise AssertionError(f"outside read was not blocked: {first}")
        write_blocked = runtime.execute_plan(
            [ToolInvocation("write_workspace_file", {"path": "../escape.txt", "content": "bad"})],
            workspace=workspace,
            user_message="permission boundary write",
            max_steps=1,
        )
        second = write_blocked.results[0]
        if second.ok or second.status.value != "blocked" or second.error_code != "workspace_violation":
            raise AssertionError(f"outside write was not blocked: {second}")
        if (parent / "escape.txt").exists():
            raise AssertionError("workspace traversal created escape.txt")
        ok = runtime.execute_plan(
            [ToolInvocation("write_workspace_file", {"path": "safe.txt", "content": "ok"})],
            workspace=workspace,
            user_message="permission boundary positive write",
            max_steps=1,
        )
        if not ok.results[0].ok or (workspace / "safe.txt").read_text(encoding="utf-8") != "ok":
            raise AssertionError(f"safe write failed: {ok.results[0]}")
        _assert_no_pollution(package_root, before, "permission boundary")
    finally:
        shutil.rmtree(parent, ignore_errors=True)


def main() -> int:
    package_root = Path(__file__).resolve().parents[1]
    try:
        _history_entry_matrix(package_root)
        _desktop_headless_boundary(package_root)
        _downloads_write_fix_pack_boundary(package_root)
        _permission_boundary(package_root)
    except Exception as exc:  # noqa: BLE001 - verifier should return a readable failure
        return _fail(str(exc), package_root=package_root)
    print(
        json.dumps(
            {
                "ok": True,
                "schema": "tiangong.l6738.q19.history_entry_permission_boundary.v1",
                "checks": [
                    "historical_entries_pass_or_skip",
                    "bat_template_crlf",
                    "bridge_registry_temp_workspace",
                    "no_pyc_default_compile_check",
                    "desktop_headless_user_reports",
                    "downloads_unicode_workspace_write_fix_pack",
                    "workspace_traversal_blocked",
                    "no_package_pollution",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
