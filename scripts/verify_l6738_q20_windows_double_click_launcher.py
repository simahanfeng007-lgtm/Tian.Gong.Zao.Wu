from __future__ import annotations

"""Q20 verifier: Windows double-click safe launcher regression.

This verifier is CI-safe on non-Windows hosts: it statically validates the BAT
entry points and dynamically exercises the Python safe launcher plus bridge-only
startup path without opening the desktop UI.
"""

import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SAFE = ROOT / "00_ASCII_START_HERE" / "python" / "WIN_SAFE_LAUNCHER_L6738.py"
MANIFEST = ROOT / "scripts" / "launcher_manifest_l67220.json"


def fail(message: str) -> None:
    raise AssertionError(message)


def assert_true(name: str, cond: bool, detail: str = "") -> None:
    if not cond:
        fail(f"{name} FAIL {detail}".rstrip())
    print(f"{name}: PASS")


def clean_package_pollution() -> None:
    for rel in (".linyuanzhe", "reports"):
        path = ROOT / rel
        if path.exists():
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    for d in list(ROOT.rglob("__pycache__")):
        shutil.rmtree(d, ignore_errors=True)
    for f in list(ROOT.rglob("*.pyc")):
        try:
            f.unlink()
        except FileNotFoundError:
            pass


def package_is_clean() -> None:
    assert_true("no_package_reports", not (ROOT / "reports").exists())
    assert_true("no_package_runtime_state", not (ROOT / ".linyuanzhe").exists())
    assert_true("no_pycache", not any(ROOT.rglob("__pycache__")))
    assert_true("no_pyc", not any(ROOT.rglob("*.pyc")))


def read_manifest_windows_entries() -> list[Path]:
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return [ROOT / item["output_path"] for item in data["entries"] if item.get("platform") == "windows"]


def validate_bat_files() -> None:
    bat_files = read_manifest_windows_entries()
    assert_true("windows_manifest_entries", len(bat_files) >= 17, str(len(bat_files)))
    for path in bat_files:
        rel = path.relative_to(ROOT).as_posix()
        raw = path.read_bytes()
        assert_true(f"bat_exists::{rel}", path.exists())
        assert_true(f"bat_ascii::{rel}", all(b < 128 for b in raw))
        assert_true(f"bat_crlf::{rel}", b"\n" not in raw.replace(b"\r\n", b""))
        text = raw.decode("ascii")
        assert_true(f"bat_safe_marker::{rel}", "Q20_FIX=windows_double_click_safe_launcher" in text)
        assert_true(f"bat_uses_safe_launcher::{rel}", "WIN_SAFE_LAUNCHER_L6738.py" in text)
        assert_true(f"bat_no_old_forf_probe::{rel}", 'for /f "usebackq' not in text.lower())
        assert_true(f"bat_no_old_python_exe_probe::{rel}", "PYTHON_EXE" not in text)


def validate_static_runtime_patches() -> None:
    assert_true("safe_launcher_exists", SAFE.exists())
    safe_text = SAFE.read_text(encoding="utf-8")
    assert_true("safe_child_isolated", '"-S", "-B", "-u"' in safe_text)
    assert_true("safe_logs_outside_package", "user_log_dir()" in safe_text and "LINYUANZHE_REPORT_DIR" in safe_text)

    desktop = (ROOT / "desktop" / "start_linyuanzhe_desktop_l671.py").read_text(encoding="utf-8")
    assert_true("bridge_spawn_isolated", 'sys.executable,\n        "-S",\n        "-B",\n        "-u",\n        str(BRIDGE)' in desktop)
    assert_true("frontend_spawn_isolated", '[sys.executable, "-S", "-B", "-u", "-m", "linyuanzhe_frontend.app"' in desktop)
    assert_true("desktop_status_flush", 'flush=True' in desktop)

    bridge = (ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py").read_text(encoding="utf-8")
    assert_true("bridge_reports_outside_package", "def _default_reports_dir()" in bridge and "REPORTS = _default_reports_dir()" in bridge)
    assert_true("bridge_no_root_reports_default", 'REPORTS = ROOT / "reports"' not in bridge)


def run_safe_self_check(tmp: Path) -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["LINYUANZHE_LAUNCH_LOG_DIR"] = str(tmp / "logs")
    env["LINYUANZHE_REPORT_DIR"] = str(tmp / "reports")
    cmd = [
        sys.executable,
        "-S",
        "-B",
        "-u",
        str(SAFE),
        "--entry-kind",
        "self_check",
        "--python-entry",
        r"00_ASCII_START_HERE\python\SELF_CHECK_L6710.py",
        "--title",
        "FE01 STEP68 / L6.73.8 - SELF-CHECK",
        "--python-mode",
        "tk",
        "--launcher-dir",
        str(ROOT / "01_启动入口" / "Windows"),
        "--start-dir",
        str(ROOT),
    ]
    res = subprocess.run(cmd, cwd=str(ROOT), env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
    assert_true("safe_self_check_rc0", res.returncode == 0, res.stdout[-800:])
    assert_true("safe_self_check_banner", "Windows launch" in res.stdout)
    assert_true("safe_self_check_child_ok", "Child exit code: 0" in res.stdout)
    assert_true("safe_self_check_no_artifact_tool", "artifact_tool" not in res.stdout)
    assert_true("safe_self_check_log_written", (tmp / "logs" / "last_windows_launch.log").exists())


def run_bridge_only_smoke(tmp: Path) -> None:
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    env["LINYUANZHE_LAUNCH_LOG_DIR"] = str(tmp / "logs2")
    env["LINYUANZHE_REPORT_DIR"] = str(tmp / "reports2")
    cmd = [
        sys.executable,
        "-S",
        "-B",
        "-u",
        str(SAFE),
        "--entry-kind",
        "start_desktop_auto",
        "--python-entry",
        r"00_ASCII_START_HERE\python\START_DESKTOP_L6710.py",
        "--title",
        "FE01 STEP68 / L6.73.8 - AUTO",
        "--python-mode",
        "tk",
        "--launcher-dir",
        str(ROOT / "01_启动入口" / "Windows"),
        "--start-dir",
        str(ROOT),
        "--backend-mode",
        "auto",
        "--bridge-only",
        "--startup-timeout",
        "10",
        "--backend-timeout",
        "5",
    ]
    proc = subprocess.Popen(
        cmd,
        cwd=str(ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        start_new_session=(os.name != "nt"),
    )
    assert proc.stdout is not None
    lines: list[str] = []
    deadline = time.time() + 15
    got = False
    while time.time() < deadline:
        line = proc.stdout.readline()
        if line:
            clean = line.rstrip("\r\n")
            lines.append(clean)
            if "本地桥接后端已启动" in clean or "LINYUANZHE_LOCAL_RUNTIME_URL=" in clean:
                got = True
                break
        elif proc.poll() is not None:
            break
        else:
            time.sleep(0.05)
    output = "\n".join(lines)
    try:
        if os.name != "nt":
            os.killpg(proc.pid, signal.SIGTERM)
        else:
            proc.terminate()
    except Exception:
        proc.terminate()
    try:
        rest, _ = proc.communicate(timeout=5)
    except subprocess.TimeoutExpired:
        try:
            if os.name != "nt":
                os.killpg(proc.pid, signal.SIGKILL)
            else:
                proc.kill()
        except Exception:
            proc.kill()
        rest, _ = proc.communicate(timeout=5)
    output = output + "\n" + (rest or "")
    assert_true("bridge_only_started", got, output[-1200:])
    assert_true("bridge_only_no_artifact_tool", "artifact_tool" not in output)
    assert_true("bridge_only_log_written", (tmp / "logs2" / "last_windows_launch.log").exists())


def main() -> int:
    clean_package_pollution()
    validate_bat_files()
    validate_static_runtime_patches()
    with tempfile.TemporaryDirectory(prefix="linyuanzhe_q20_win_") as td:
        tmp = Path(td)
        run_safe_self_check(tmp)
        package_is_clean()
        run_bridge_only_smoke(tmp)
        package_is_clean()
    print("Q20 Windows double-click safe launcher verifier PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
