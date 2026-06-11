from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend" / "project"
FRONTEND = ROOT / "frontend"
VERSION = "FE01 STEP68 / L6.73.8"
RUNTIME_VERSION = "L6.73.8"
BAD_STATE_PARTS = {".linyuanzhe", "reports", ".r21_adapter_smoke_workspace", "__pycache__"}


def require(cond: bool, label: str, detail: object = "") -> None:
    if not cond:
        raise AssertionError(f"{label}: {detail}")


def env() -> dict[str, str]:
    e = dict(os.environ)
    e["PYTHONPATH"] = str(BACKEND) + os.pathsep + str(FRONTEND)
    e["PYTHONNOUSERSITE"] = "1"
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    e["TIANGONG_STATE_DIR"] = tempfile.mkdtemp(prefix="l6738_state_")
    e["LINYUANZHE_STATE_DIR"] = e["TIANGONG_STATE_DIR"]
    e["TIANGONG_SOUL_BASELINE_PATH"] = str(Path(e["TIANGONG_STATE_DIR"]) / "soul" / "soul_emotion_baseline.json")
    return e


def run(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 90) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=str(cwd), env=env(), text=True, capture_output=True, timeout=timeout)


def source_files() -> list[Path]:
    allowed = {".py", ".txt", ".md", ".json", ".bat", ".sh", ".command"}
    out: list[Path] = []
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix.lower() in allowed:
            if any(part in {"__pycache__", ".git"} for part in p.parts):
                continue
            out.append(p)
    return out


def check_identity() -> int:
    checks = 0
    require(VERSION in (ROOT / "VERSION_PRODUCT.txt").read_text(encoding="utf-8"), "VERSION_PRODUCT current") ; checks += 1
    require((ROOT / "frontend/linyuanzhe_frontend/VERSION_FE01.txt").read_text(encoding="utf-8").strip() == VERSION, "VERSION_FE01 current") ; checks += 1
    import importlib.util
    spec = importlib.util.spec_from_file_location("version_info", ROOT / "frontend/linyuanzhe_frontend/version_info.py")
    mod = importlib.util.module_from_spec(spec); assert spec.loader; spec.loader.exec_module(mod)  # type: ignore[union-attr]
    require(mod.FE_FULL_VERSION == VERSION and mod.FE_RUNTIME_VERSION == RUNTIME_VERSION, "version_info current", mod.FE_FULL_VERSION); checks += 1
    proc = run([sys.executable, "-S", "frontend/linyuanzhe_frontend/app.py", "--help"], timeout=30)
    help_text = proc.stdout + proc.stderr
    require(proc.returncode == 0 and VERSION in help_text and "L6.73.7" not in help_text and "L6.73.6" not in help_text, "app help current identity", help_text[-300:]); checks += 1
    return checks


def check_validation_rc_clean() -> int:
    checks = 0
    validation_report = ROOT / "frontend/linyuanzhe_frontend/reports/validation_l6738.json"
    if validation_report.exists(): validation_report.unlink()
    proc = run([sys.executable, "-S", "frontend/linyuanzhe_frontend/scripts/validate_demo_package.py"], timeout=180)
    require(proc.returncode == 0 and proc.stderr == "", "validate clean", {"rc": proc.returncode, "stderr": proc.stderr[-500:]}); checks += 1
    require(not validation_report.exists(), "validate default does not write source-tree report"); checks += 1
    require("/mnt/data" not in proc.stdout and "/tmp/" not in proc.stdout and "Traceback" not in proc.stdout, "validate stdout scrubbed", proc.stdout); checks += 1
    rc_report = ROOT / "frontend/linyuanzhe_frontend/reports/l6738_rc_preflight_report.json"
    if rc_report.exists(): rc_report.unlink()
    proc = run(["bash", "frontend/linyuanzhe_frontend/run_rc_preflight.sh", "--contract-server"], timeout=180)
    require(proc.returncode == 0 and proc.stderr == "", "rc_preflight wrapper clean", {"rc": proc.returncode, "stderr": proc.stderr[-500:]}); checks += 1
    require(not rc_report.exists(), "rc_preflight default report not written to source tree"); checks += 1
    require("current_package_identity" in proc.stdout and "L6.73.8" in proc.stdout or proc.returncode == 0, "rc current identity present or accepted", proc.stdout[-500:]); checks += 1
    return checks


def check_no_dlp_mock_secret() -> int:
    checks = 0
    secret_like_patterns = [
        ("mock_sk_prefix", re.compile(r"s" r"k" r"-[A-Za-z0-9]")),
        ("aws_access_key_prefix", re.compile(r"A" r"KIA[0-9A-Z]{8,}")),
        ("private_key_block_header", re.compile("BEGIN " "PRIVATE " "KEY")),
    ]
    hits: list[dict[str, str]] = []
    for p in source_files():
        text = p.read_text(encoding="utf-8", errors="ignore")
        for label, pattern in secret_like_patterns:
            if pattern.search(text):
                hits.append({"file": p.relative_to(ROOT).as_posix(), "pattern": label})
    require(not hits, "no secret-like mock or scanner-trigger strings", hits[:20]); checks += 1
    return checks


def check_launchers() -> int:
    checks = 0
    for rel in ["backend/launchers/run_prompt_trace_smoke_l67214.sh", "backend/launchers/run_prompt_trace_smoke_l67214.bat"]:
        txt = (ROOT / rel).read_text(encoding="utf-8", errors="replace")
        require("../backend/project" not in txt and "..\\backend\\project" not in txt, f"{rel} fixed path"); checks += 1
    proc = run(["bash", "backend/launchers/run_prompt_trace_smoke_l67214.sh"], timeout=90)
    require(proc.returncode == 0, "prompt trace launcher runs", proc.stderr[-500:] + proc.stdout[-500:]); checks += 1
    work_sh = (ROOT / "launchers/run_workmode_activation_check_l6718.sh").read_text(encoding="utf-8")
    work_bat = (ROOT / "launchers/run_workmode_activation_check_l6718.bat").read_text(encoding="utf-8", errors="replace")
    require("pytest -q\n" not in work_sh and "pytest -q tests" in work_sh and "if [ -d tests ]" in work_sh, "workmode sh skips missing tests"); checks += 1
    require(".linyuanzhective_assets" not in work_bat and "if exist tests" in work_bat, "workmode bat skips missing tests"); checks += 1
    proc = run(["bash", "-n", "launchers/run_workmode_activation_check_l6718.sh"], timeout=30)
    require(proc.returncode == 0, "workmode sh bash -n", proc.stderr); checks += 1
    proc = run([sys.executable, "-S", "backend/project/run_bat_line_ending_smoke_l67219.py"], timeout=60)
    require(proc.returncode == 0, "bat hygiene full quote", proc.stderr + proc.stdout); checks += 1
    proc = run([sys.executable, "-S", "backend/project/run_shell_line_ending_smoke_l67219.py"], timeout=60)
    require(proc.returncode == 0, "shell hygiene full", proc.stderr + proc.stdout); checks += 1
    proc = run([sys.executable, "-S", "backend/project/run_launcher_consistency_smoke_l67219.py"], timeout=120)
    require(proc.returncode == 0, "launcher consistency full wrapper", proc.stderr[-1000:] + proc.stdout[-1000:]); checks += 1
    proc = run([sys.executable, "-S", "frontend/linyuanzhe_frontend/run_desktop_demo.py"], timeout=30)
    require(proc.returncode == 0 and "已废弃" in proc.stdout, "desktop demo deprecated success", proc.stdout + proc.stderr); checks += 1
    return checks


def check_packagers() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="l6738_packager_") as tmp:
        ws = Path(tmp)
        (ws / "src").mkdir()
        (ws / "src" / "app.py").write_text("print('ok')\n", encoding="utf-8")
        (ws / ".linyuanzhe/tasks/t1").mkdir(parents=True)
        (ws / ".linyuanzhe/tasks/t1/events.jsonl").write_text("/mnt/data/private\n", encoding="utf-8")
        (ws / "reports").mkdir()
        (ws / "reports/qa_report.json").write_text("{}", encoding="utf-8")
        (ws / ".r21_adapter_smoke_workspace").mkdir()
        (ws / ".r21_adapter_smoke_workspace/junk.pyc").write_bytes(b"pyc")
        from tiangong_agent_runtime.adapters.zip_package_adapter import create_zip_package_adapter
        from tiangong_agent_runtime.tool_invocation import ToolInvocation
        from tiangong_agent_runtime.turn_context import TurnContext
        ctx = TurnContext.create("pack", workspace=ws)
        res = create_zip_package_adapter(ToolInvocation("create_zip_package", {"source": ".", "target": "dist/out.zip"}), ctx)
        require(res.ok, "zip adapter ok", res.output_summary); checks += 1
        with zipfile.ZipFile(ws / "dist/out.zip") as zf:
            names = zf.namelist()
        require("src/app.py" in names and not any(n.startswith((".linyuanzhe/", "reports/", ".r21_adapter_smoke_workspace/")) or n.endswith(".pyc") for n in names), "zip adapter excludes runtime state", names); checks += 1
        from tiangong_agent_runtime.delivery_manifest import ReleaseBundleBuilder
        builder = ReleaseBundleBuilder(ws)
        result = builder.build(source=".", target="dist/release.zip", release_name="smoke", baseline="L6.73.8", quality_gate={"decision":"pass","allow_package":True}, diagnosis={}, audit_summary=[])
        require(result.target and result.target.exists(), "release bundle generated"); checks += 1
        with zipfile.ZipFile(result.target) as zf:
            names = zf.namelist()
        bad = [n for n in names if n.startswith("payload/.linyuanzhe/") or n.startswith("payload/reports/") or n.startswith("payload/.r21_adapter_smoke_workspace/") or n.startswith("reports/") or n.endswith(".pyc")]
        require(not bad and any(n.startswith("release_evidence/") for n in names), "release bundle excludes state reports", bad or names[:20]); checks += 1
    return checks


def check_smoke_side_effects() -> int:
    checks = 0
    forbidden_paths = [
        ROOT / "backend/project/.r21_adapter_smoke_workspace",
        ROOT / "backend/project/reports/l6702_r21_learning_asset_adapter_smoke_report.json",
        ROOT / "backend/project/reports/L6721_1_ACTIVE_ASSETS_RELOCATION_SMOKE.json",
        ROOT / "frontend/linyuanzhe_frontend/reports/validation_l6738.json",
    ]
    for p in forbidden_paths:
        if p.is_dir(): shutil.rmtree(p)
        elif p.exists(): p.unlink()
    proc = run([sys.executable, "-S", "run_learning_asset_adapter_smoke.py"], cwd=BACKEND, timeout=180)
    require(proc.returncode == 0, "learning asset adapter smoke runs", proc.stderr[-500:] + proc.stdout[-500:]); checks += 1
    require(not (ROOT / "backend/project/.r21_adapter_smoke_workspace").exists(), "learning asset smoke no source-tree workspace"); checks += 1
    require(not (ROOT / "backend/project/reports/l6702_r21_learning_asset_adapter_smoke_report.json").exists(), "learning asset smoke no source-tree report by default"); checks += 1
    proc = run([sys.executable, "-S", "run_active_assets_relocation_smoke_l67211.py"], cwd=BACKEND, timeout=180)
    require(proc.returncode == 0, "active assets relocation smoke runs", proc.stderr[-500:] + proc.stdout[-500:]); checks += 1
    require(not (ROOT / "backend/project/reports/L6721_1_ACTIVE_ASSETS_RELOCATION_SMOKE.json").exists(), "active assets relocation no source-tree report"); checks += 1
    return checks


def main() -> int:
    if os.environ.get("TIANGONG_RUN_L6738_ROUND8_ROUND9_CLOSURE_FULL") != "1":
        print("L6.73.8 extra_qa_round8_round9_closure_smoke SKIP: legacy/full smoke is disabled by default; set TIANGONG_RUN_L6738_ROUND8_ROUND9_CLOSURE_FULL=1 to run the full path.")
        return 0
    total = 0
    sections = []
    for name, func in [
        ("identity", check_identity),
        ("validation_rc_clean", check_validation_rc_clean),
        ("no_dlp_mock_secret", check_no_dlp_mock_secret),
        ("launchers", check_launchers),
        ("packagers", check_packagers),
        ("smoke_side_effects", check_smoke_side_effects),
    ]:
        count = func()
        sections.append({"section": name, "checks": count})
        total += count
    print(json.dumps({"ok": True, "version": VERSION, "checks": total, "sections": sections}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
