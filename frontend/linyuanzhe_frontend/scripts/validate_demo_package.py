from __future__ import annotations

"""FE01 STEP68 / L6.73.8 current package validator.

验证器原则：
- 子检查默认使用 python -S 与隔离环境，避免 sitecustomize / artifact_tool 等外部启动钩子污染 stderr。
- 报告默认写入临时目录；只有显式 --out 时才写入用户指定路径。
- 报告不记录构建机绝对路径，只记录相对路径、命令摘要和尾部输出。
"""

import argparse
import json
import os
import subprocess
import sys
sys.dont_write_bytecode = True
import tempfile
import tokenize
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
FRONTEND_PARENT = ROOT.parent
PROJECT_ROOT = ROOT.parents[1]
VERSION = "FE01 STEP68 / L6.73.8"
SCHEMA = "tiangong.l6_73_8.frontend_current_package_validation.v1"
REQUIRED_FILES = [
    "VERSION_FE01.txt",
    "__init__.py",
    "app.py",
    "requirements.txt",
    "run_rc_preflight.py",
    "run_rc_preflight.sh",
    "run_rc_preflight.bat",
    "run_validation.sh",
    "run_validation.bat",
    "contracts/runtime_snapshot.py",
    "contracts/sse_events.py",
    "contracts/provider_settings.py",
    "contracts/file_transfer.py",
    "contracts/hook_bus.py",
    "contracts/run_workbench.py",
    "clients/sse_runtime_client.py",
    "clients/runtime_integration_probe.py",
    "ui/main_window.py",
    "ui/main_window_actions.py",
    "ui/main_window_feature_pages.py",
    "ui/main_window_chat_runtime.py",
    "scripts/runtime_contract_server.py",
]
FORBIDDEN_REPORT_MARKERS = ("/mnt/data", "/tmp/", "Traceback", "artifact_tool", "RemoteError")


def _rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except Exception:
        try:
            return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
        except Exception:
            return path.name


def _scrub_text(text: str, limit: int = 4000) -> str:
    text = str(text or "")[-limit:]
    replacements = {
        str(PROJECT_ROOT.resolve()): ".",
        str(ROOT.resolve()): "frontend/linyuanzhe_frontend",
        str(FRONTEND_PARENT.resolve()): "frontend",
        str(Path(tempfile.gettempdir()).resolve()): "<tmp>",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def _clean_env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONPATH"] = str(FRONTEND_PARENT)
    env["PYTHONNOUSERSITE"] = "1"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env.setdefault("LINYUANZHE_VALIDATION_CLEAN", "1")
    for key in list(env):
        if key.lower().startswith(("artifact_tool", "caas_")):
            env.pop(key, None)
    return env


def _cmd_public(cmd: list[str]) -> list[str]:
    public: list[str] = []
    for item in cmd:
        if item == sys.executable:
            public.append("python")
        else:
            public.append(_scrub_text(item, 1000))
    return public


def _run(cmd: list[str], cwd: Path, timeout: int = 90) -> dict[str, Any]:
    try:
        proc = subprocess.run(cmd, cwd=str(cwd), text=True, capture_output=True, timeout=timeout, env=_clean_env())
        return {
            "cmd": _cmd_public(cmd),
            "cwd": _rel(cwd),
            "returncode": proc.returncode,
            "stdout": _scrub_text(proc.stdout),
            "stderr": _scrub_text(proc.stderr),
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "cmd": _cmd_public(cmd),
            "cwd": _rel(cwd),
            "returncode": 124,
            "stdout": _scrub_text(exc.stdout or ""),
            "stderr": _scrub_text(exc.stderr or ""),
        }


def _default_out() -> Path:
    report_dir = os.environ.get("TIANGONG_REPORT_DIR") or os.environ.get("LINYUANZHE_REPORT_DIR")
    if report_dir:
        return Path(report_dir) / "validation_l6738.json"
    return Path(tempfile.mkdtemp(prefix="linyuanzhe_validate_l6738_")) / "validation_l6738.json"


def _identity_checks() -> list[dict[str, Any]]:
    checks: list[dict[str, Any]] = []
    version_file = (ROOT / "VERSION_FE01.txt").read_text(encoding="utf-8", errors="replace").strip()
    checks.append({"name": "VERSION_FE01", "ok": version_file == VERSION, "value": version_file})
    help_result = _run([sys.executable, "-S", "-B", str(ROOT / "app.py"), "--help"], cwd=PROJECT_ROOT, timeout=30)
    help_text = str(help_result.get("stdout", "")) + str(help_result.get("stderr", ""))
    checks.append({
        "name": "app_help_identity",
        "ok": help_result["returncode"] == 0 and VERSION in help_text and "L6.73.7" not in help_text and "L6.73.6" not in help_text,
        "result": help_result,
    })
    return checks



def _compile_tree_no_pyc(target: Path) -> dict[str, Any]:
    """Syntax-compile Python files without writing __pycache__ / *.pyc."""
    errors: list[dict[str, Any]] = []
    files: list[Path]
    if target.is_file():
        files = [target]
    else:
        files = sorted(p for p in target.rglob("*.py") if "__pycache__" not in p.parts)
    for path in files:
        try:
            with tokenize.open(str(path)) as handle:
                source = handle.read()
            compile(source, _rel(path), "exec", dont_inherit=True)
        except Exception as exc:
            errors.append({"file": _rel(path), "error": f"{exc.__class__.__name__}: {_scrub_text(str(exc), 500)}"})
    return {
        "cmd": ["python", "-S", "-B", "syntax_compile_no_pyc", _rel(target)],
        "cwd": _rel(PROJECT_ROOT),
        "returncode": 0 if not errors else 1,
        "files_checked": len(files),
        "errors": errors[:20],
        "stdout": "",
        "stderr": "",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=f"{VERSION} current package validation")
    parser.add_argument("--out", default="", help="输出报告 JSON 路径；未指定时写入临时目录，避免污染交付树。")
    args = parser.parse_args(argv)

    missing = [rel for rel in REQUIRED_FILES if not (ROOT / rel).exists()]
    checks: list[dict[str, Any]] = [{"name": "required_files", "ok": not missing, "missing": missing}]
    checks.extend(_identity_checks())
    compile_result = _compile_tree_no_pyc(ROOT)
    checks.append({"name": "compile_frontend_no_pyc", "ok": compile_result["returncode"] == 0 and not compile_result.get("stderr"), "result": compile_result})
    rc_out = Path(tempfile.mkdtemp(prefix="linyuanzhe_rc_l6738_")) / "rc_preflight_l6738.json"
    rc_result = _run([sys.executable, "-S", "-B", "-m", "linyuanzhe_frontend.run_rc_preflight", "--contract-server", "--out", str(rc_out)], cwd=FRONTEND_PARENT, timeout=120)
    checks.append({"name": "rc_preflight_contract_server_clean", "ok": rc_result["returncode"] == 0 and not rc_result.get("stderr"), "result": rc_result})
    report = {
        "schema": SCHEMA,
        "version": VERSION,
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "root": ".",
        "checks": checks,
    }
    out = Path(args.out) if args.out else _default_out()
    out.parent.mkdir(parents=True, exist_ok=True)
    serialized = json.dumps(report, ensure_ascii=False, indent=2)
    # Hard stop if the report would carry host paths or external traceback noise.
    report_clean = not any(marker in serialized for marker in FORBIDDEN_REPORT_MARKERS)
    if not report_clean:
        checks.append({"name": "report_sanitized", "ok": False, "forbidden_markers": [m for m in FORBIDDEN_REPORT_MARKERS if m in serialized]})
        serialized = json.dumps(report, ensure_ascii=False, indent=2)
    out.write_text(serialized, encoding="utf-8")
    failed = [c["name"] for c in checks if not c.get("ok")]
    if failed:
        print(f"{VERSION} current package validation FAILED: {', '.join(failed)}")
        print(f"report: {_rel(out)}")
        return 1
    print(f"{VERSION} current package validation PASS")
    print(f"report: {_rel(out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
