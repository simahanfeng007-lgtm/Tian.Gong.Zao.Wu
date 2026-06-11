from __future__ import annotations

"""FE01 STEP31J / L6.71.0 cross-platform categorized desktop delivery audit."""

import json
import os
import re
import stat
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
ENTRY = ROOT / "01_启动入口"
URL_RE = re.compile(r"LINYUANZHE_LOCAL_RUNTIME_URL=(http://[^\s]+)")

WINDOWS_FILES = [
    ENTRY / "Windows" / "01_启动临渊者桌面端_自动模式_L6710.bat",
    ENTRY / "Windows" / "02_启动临渊者桌面端_真实模型_L6710.bat",
    ENTRY / "Windows" / "01_启动临渊者桌面端_自动模式_L6710.bat",
    ENTRY / "Windows" / "04_一键自检_L6710.bat",
]
POSIX_FILES = [
    ENTRY / "macOS" / "01_启动临渊者桌面端_自动模式_L6710.command",
    ENTRY / "macOS" / "02_启动临渊者桌面端_真实模型_L6710.command",
    ENTRY / "macOS" / "01_启动临渊者桌面端_自动模式_L6710.command",
    ENTRY / "macOS" / "04_一键自检_L6710.command",
    ENTRY / "Linux" / "01_start_desktop_auto_l6710.sh",
    ENTRY / "Linux" / "02_start_desktop_provider_l6710.sh",
    ENTRY / "Linux" / "03_start_desktop_mock_l6710.sh",
    ENTRY / "Linux" / "04_self_check_l6710.sh",
]


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def line_ending_state(path: Path) -> dict[str, int | bool]:
    if not path.exists():
        return {"crlf": 0, "lone_lf": 0, "lone_cr": 0, "exists": False}
    data = path.read_bytes()
    crlf = data.count(b"\r\n")
    lf = data.count(b"\n")
    cr = data.count(b"\r")
    return {"crlf": crlf, "lone_lf": lf - crlf, "lone_cr": cr - crlf, "exists": True}


def check_entry_layout() -> tuple[bool, dict[str, object]]:
    missing = [rel(p) for p in WINDOWS_FILES + POSIX_FILES if not p.exists()]
    root_scripts = [p.name for p in ROOT.iterdir() if p.is_file() and p.suffix.lower() in {".bat", ".cmd", ".ps1", ".sh", ".command", ".py"}]
    executable_bad = [rel(p) for p in POSIX_FILES if p.exists() and not (p.stat().st_mode & stat.S_IXUSR)]
    ok = not missing and not root_scripts and not executable_bad
    return ok, {"missing": missing, "root_scripts": root_scripts, "executable_bad": executable_bad}


def check_line_endings() -> tuple[bool, list[dict[str, object]]]:
    items: list[dict[str, object]] = []
    ok = True
    for path in WINDOWS_FILES:
        state = line_ending_state(path)
        item_ok = bool(state["exists"]) and state["lone_lf"] == 0 and state["lone_cr"] == 0 and state["crlf"] > 0
        ok = ok and item_ok
        items.append({"file": rel(path), "kind": "windows", "ok": item_ok, **state})
    for path in POSIX_FILES:
        state = line_ending_state(path)
        mode_ok = bool(path.exists() and os.access(path, os.X_OK))
        item_ok = bool(state["exists"]) and state["crlf"] == 0 and state["lone_cr"] == 0 and state["lone_lf"] > 0 and mode_ok
        ok = ok and item_ok
        items.append({"file": rel(path), "kind": "posix", "ok": item_ok, "executable": mode_ok, **state})
    return ok, items


def check_append_guard() -> tuple[bool, list[str]]:
    allowed_fragments = [
        'ChatMessage("user", "你"',
        'self.chat_messages.append(message)',
        'self.chat_messages.append(',
    ]
    violations: list[str] = []
    for base in [ROOT / "frontend" / "linyuanzhe_frontend" / "clients", ROOT / "frontend" / "linyuanzhe_frontend" / "contracts"]:
        for path in base.rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for no, line in enumerate(text.splitlines(), 1):
                if "chat_messages.append" not in line:
                    continue
                relp = path.relative_to(ROOT).as_posix()
                if relp.endswith("contracts/runtime_snapshot.py") and any(fragment in line for fragment in allowed_fragments):
                    continue
                if relp.endswith("clients/sse_runtime_client.py") and 'ChatMessage("user", "你"' in line:
                    continue
                violations.append(f"{relp}:{no}:{line.strip()}")
    return not violations, violations


def check_self_check() -> tuple[bool, str]:
    proc = subprocess.run(
        [sys.executable, str(ENTRY / "通用Python" / "START_DESKTOP_L6710.py"), "--self-check"],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=20,
    )
    return proc.returncode == 0, proc.stdout[-4000:]


def start_bridge_probe() -> tuple[bool, dict[str, object]]:
    proc = subprocess.Popen(
        [sys.executable, "-u", str(ENTRY / "通用Python" / "START_DESKTOP_L6710.py"), "--backend-mode", "auto", "--bridge-only", "--bridge-log"],
        cwd=str(ROOT),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        bufsize=1,
    )
    assert proc.stdout is not None
    seen: list[str] = []
    url = ""
    deadline = time.time() + 20
    result_ok = False
    result_payload: dict[str, object] = {"url": "", "tail": []}
    termination_warning = ""
    try:
        while time.time() < deadline:
            line = proc.stdout.readline()
            if line:
                seen.append(line.rstrip())
                match = URL_RE.search(line)
                if match:
                    url = match.group(1)
                    break
            if proc.poll() is not None:
                break
        if not url:
            result_ok = False
            result_payload = {"url": "", "tail": seen[-20:], "returncode": proc.poll()}
        else:
            with urllib.request.urlopen(url + "/health/runtime", timeout=5) as resp:
                health = json.loads(resp.read().decode("utf-8"))
            with urllib.request.urlopen(url + "/settings/provider", timeout=5) as resp:
                settings = json.loads(resp.read().decode("utf-8"))
            result_ok = health.get("payload", {}).get("status") == "ok" and bool(settings.get("local_desktop_bridge"))
            result_payload = {
                "url": url,
                "health_status": health.get("payload", {}).get("status"),
                "settings_state": settings.get("provider_config_state"),
                "tail": seen[-10:],
            }
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                termination_warning = "bridge process could not be killed"
    if termination_warning:
        result_payload["termination_warning"] = termination_warning
    return result_ok, result_payload


def main() -> int:
    REPORTS.mkdir(parents=True, exist_ok=True)
    checks: dict[str, object] = {}
    ok_layout, layout_payload = check_entry_layout()
    checks["entry_layout"] = {"ok": ok_layout, **layout_payload}
    ok_line, line_items = check_line_endings()
    checks["line_endings"] = {"ok": ok_line, "items": line_items}
    ok_append, append_violations = check_append_guard()
    checks["append_guard"] = {"ok": ok_append, "violations": append_violations}
    ok_self, self_output = check_self_check()
    checks["self_check"] = {"ok": ok_self, "output_tail": self_output}
    ok_bridge, bridge_payload = start_bridge_probe()
    checks["bridge_probe"] = {"ok": ok_bridge, **bridge_payload}
    overall = all(bool(checks[name]["ok"]) for name in checks)  # type: ignore[index]
    payload = {"version": "FE01 STEP31J / L6.71.0", "ok": overall, "checks": checks}
    (REPORTS / "cross_platform_desktop_audit_l6710.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if overall else 1


if __name__ == "__main__":
    raise SystemExit(main())
