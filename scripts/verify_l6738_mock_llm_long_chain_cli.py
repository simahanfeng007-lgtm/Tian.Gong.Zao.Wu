#!/usr/bin/env python3
"""L6.73.8 Q17: CLI-level mock LLM long-chain simulation verifier.

This verifier exercises the user-facing ``run_agent.py --mock --once`` path with
Chinese long-chain prompts.  It must stay offline, deterministic, and package-read
only: Runtime state is written only to temporary workspaces.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RUN_AGENT = ROOT / "backend" / "project" / "run_agent.py"

PROMPTS = [
    "请模拟LLM进行一个长链代码修复工作：定位bug、提出计划、执行、验证、总结。",
    "请模拟LLM进行长链工作，检查项目并输出总结。",
]


def _run_prompt(prompt: str) -> dict:
    workspace = Path(tempfile.mkdtemp(prefix="linyuanzhe_mock_llm_chain_"))
    env = dict(os.environ)
    env.update(
        {
            "TIANGONG_ALLOW_INTERNAL_MOCK": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONNOUSERSITE": "1",
            "PYTHONUTF8": "1",
            "PYTHONIOENCODING": "utf-8:replace",
            "TIANGONG_SOUL_BASELINE_PERSIST": "0",
        }
    )
    cmd = [
        sys.executable,
        "-S",
        str(RUN_AGENT),
        "--mock",
        "--workspace",
        str(workspace),
        "--once",
        prompt,
        "--max-steps",
        "8",
    ]
    try:
        completed = subprocess.run(
            cmd,
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
            env=env,
        )
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        pycache_count = sum(1 for _ in workspace.rglob("__pycache__"))
        pyc_count = sum(1 for _ in workspace.rglob("*.pyc"))
        failures = []
        if completed.returncode != 0:
            failures.append(f"rc={completed.returncode}")
        if "[工作链]" not in stdout or "failures=0" not in stdout:
            failures.append("missing completed work-chain marker")
        for marker in ("尚未配置模型接口", "path_not_found", "README.md", "failed_recoverable"):
            if marker in stdout or marker in stderr:
                failures.append(f"unexpected marker: {marker}")
        if str(workspace) in stdout or str(workspace) in stderr:
            failures.append("absolute temp workspace path leaked")
        if pycache_count or pyc_count:
            failures.append(f"bytecode pollution: __pycache__={pycache_count}, pyc={pyc_count}")
        return {
            "prompt": prompt,
            "rc": completed.returncode,
            "ok": not failures,
            "failures": failures,
            "stdout_head": stdout[:1200],
            "stderr_head": stderr[:1200],
            "pycache_count": pycache_count,
            "pyc_count": pyc_count,
        }
    finally:
        shutil.rmtree(workspace, ignore_errors=True)


def main() -> int:
    results = [_run_prompt(prompt) for prompt in PROMPTS]
    ok = all(item["ok"] for item in results)
    payload = {
        "ok": ok,
        "status": "PASS" if ok else "FAIL",
        "smoke": "L6.73.8 mock LLM long-chain CLI",
        "case_count": len(results),
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
