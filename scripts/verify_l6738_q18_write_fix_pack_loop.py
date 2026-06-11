"""Q18 verifier: mock LLM long-chain write -> repair -> verify -> package loop.

This script is intentionally offline and CI-safe:
- uses the internal mock model only when TIANGONG_ALLOW_INTERNAL_MOCK is enabled
- runs in a temporary workspace outside the release tree
- checks that the package root is not polluted by reports/.linyuanzhe/pycache
"""

from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def _fail(message: str, *, stdout: str = "", stderr: str = "", workspace: Path | None = None) -> int:
    def redact(text: str) -> str:
        value = str(text or "")
        if workspace is not None:
            value = value.replace(str(workspace), "<workspace>")
        return value[:4000]

    print(f"FAIL Q18 write-fix-pack loop: {message}")
    if stdout:
        print("--- stdout ---")
        print(redact(stdout))
    if stderr:
        print("--- stderr ---")
        print(redact(stderr))
    return 1


def _compile_file(path: Path) -> tuple[bool, str]:
    try:
        source = path.read_text(encoding="utf-8-sig")
        compile(source, path.name, "exec", dont_inherit=True)
        return True, ""
    except Exception as exc:  # noqa: BLE001 - verifier should return a readable failure
        return False, f"{type(exc).__name__}: {exc}"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    package_root = Path(__file__).resolve().parents[1]
    workspace = Path(tempfile.mkdtemp(prefix="linyuanzhe_q18_write_fix_pack_"))
    try:
        (workspace / "broken.py").write_text("def broken()\n    return 1\n", encoding="utf-8")
        env = dict(os.environ)
        state_dir = workspace / "_runtime_state"
        env.update(
            {
                "PYTHONUTF8": "1",
                "PYTHONIOENCODING": "utf-8:replace",
                "PYTHONNOUSERSITE": "1",
                "PYTHONDONTWRITEBYTECODE": "1",
                "TIANGONG_ALLOW_INTERNAL_MOCK": "1",
                "LINYUANZHE_FRONTEND_WORK_MODE": "work",
                "TIANGONG_SOUL_BASELINE_PERSIST": "0",
                "LINYUANZHE_STATE_DIR": str(state_dir),
                "TIANGONG_STATE_DIR": str(state_dir),
                "TIANGONG_PROMPT_TRACE_FILE": str(state_dir / "prompt_trace" / "prompt_trace.jsonl"),
                "TIANGONG_PROMPT_TUNER_FILE": str(state_dir / "prompt_trace" / "prompt_tuning_state.json"),
            }
        )
        cmd = [
            sys.executable,
            "-S",
            str(package_root / "backend" / "project" / "run_agent.py"),
            "--mock",
            "--workspace",
            str(workspace),
            "--once",
            "请模拟LLM进行长链工作：创建 CHANGELOG.txt 内容：Q18 loop marker；修复项目；运行测试；打包交付；输出总结。",
            "--max-steps",
            "8",
        ]
        completed = subprocess.run(  # noqa: S603 - verifier runs a fixed argv
            cmd,
            cwd=str(package_root),
            env=env,
            capture_output=True,
            text=True,
            timeout=40,
            check=False,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        if completed.returncode != 0:
            return _fail(f"run_agent returned rc={completed.returncode}", stdout=stdout, stderr=stderr, workspace=workspace)
        required_markers = [
            "[计划器]",
            "repair_attempted=True",
            "repair_succeeded=True",
            "恢复执行原计划剩余步骤",
            "长链写入、修复、复检、打包与总结闭环完成",
            "dist/model_planner_demo.zip",
        ]
        for marker in required_markers:
            if marker not in stdout:
                return _fail(f"missing stdout marker: {marker}", stdout=stdout, stderr=stderr, workspace=workspace)
        forbidden_markers = [
            str(workspace),
            ".linyuanzhe/document_writeback",
            "尚未配置模型接口",
            "path_not_found",
            "__pycache__",
        ]
        for marker in forbidden_markers:
            if marker and marker in stdout:
                return _fail(f"stdout leaked/contained forbidden marker: {marker}", stdout=stdout, stderr=stderr, workspace=workspace)
        changelog = workspace / "CHANGELOG.txt"
        if not changelog.exists() or changelog.read_text(encoding="utf-8") != "Q18 loop marker":
            return _fail("CHANGELOG.txt was not written with the exact requested content", stdout=stdout, stderr=stderr, workspace=workspace)
        repaired = workspace / "broken.py"
        if "def broken():" not in repaired.read_text(encoding="utf-8-sig"):
            return _fail("broken.py was not repaired with the missing colon", stdout=stdout, stderr=stderr, workspace=workspace)
        ok, compile_error = _compile_file(repaired)
        if not ok:
            return _fail(f"repaired broken.py does not compile: {compile_error}", stdout=stdout, stderr=stderr, workspace=workspace)

        zip_path = workspace / "dist" / "model_planner_demo.zip"
        sha_path = workspace / "dist" / "model_planner_demo.zip.sha256"
        if not zip_path.exists() or not sha_path.exists():
            return _fail("delivery zip or sha256 sidecar missing", stdout=stdout, stderr=stderr, workspace=workspace)
        if _sha256(zip_path) not in sha_path.read_text(encoding="utf-8"):
            return _fail("zip sha256 sidecar does not match the generated zip", stdout=stdout, stderr=stderr, workspace=workspace)
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            if "CHANGELOG.txt" not in names or "broken.py" not in names:
                return _fail(f"zip missing expected entries: {names}", stdout=stdout, stderr=stderr, workspace=workspace)
            bad_entries = [
                name
                for name in names
                if name.startswith((".linyuanzhe/", "reports/", "_runtime_state/"))
                or "__pycache__" in name
                or name.endswith((".pyc", ".pyo"))
                or "\\" in name
                or name.startswith("/")
                or ".." in Path(name).parts
            ]
            if bad_entries:
                return _fail(f"zip contains forbidden entries: {bad_entries[:20]}", stdout=stdout, stderr=stderr, workspace=workspace)
        package_pollution = []
        for bad in (".linyuanzhe", "reports", "__pycache__", ".pytest_cache"):
            if (package_root / bad).exists():
                package_pollution.append(bad)
        if list(package_root.rglob("*.pyc")):
            package_pollution.append("*.pyc")
        if package_pollution:
            return _fail(f"package root polluted during verifier: {package_pollution}", stdout=stdout, stderr=stderr, workspace=workspace)

        print("PASS Q18 write-fix-pack loop: write, adaptive repair, verify, package, sha256 and zip hygiene all passed.")
        return 0
    finally:
        if os.environ.get("LINYUANZHE_Q18_KEEP_WORKSPACE") != "1":
            shutil.rmtree(workspace, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
