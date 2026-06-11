from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "backend" / "project"
FRONTEND = ROOT / "frontend"


def run(cmd: list[str], *, env: dict[str, str] | None = None, cwd: Path | None = None, timeout: int = 120) -> None:
    merged = os.environ.copy()
    merged["PYTHONDONTWRITEBYTECODE"] = "1"
    if env:
        merged.update(env)
    print("$", " ".join(str(x) for x in cmd), flush=True)
    subprocess.run([str(x) for x in cmd], cwd=str(cwd or ROOT), env=merged, check=True, timeout=timeout)


def main() -> int:
    if os.environ.get("TIANGONG_RUN_L67251_FULL_QUALITY_SMOKE") != "1":
        print("L6.72.51 full_quality_smoke SKIP: legacy/full smoke is disabled by default; set TIANGONG_RUN_L67251_FULL_QUALITY_SMOKE=1 to run the full path.")
        return 0
    py = sys.executable
    be_fe_env = {"PYTHONPATH": f"{PROJECT}:{FRONTEND}", "TIANGONG_ALLOW_INTERNAL_MOCK": "1"}
    be_env = {"PYTHONPATH": str(PROJECT), "TIANGONG_ALLOW_INTERNAL_MOCK": "1"}
    fe_env = {"PYTHONPATH": str(FRONTEND)}

    run([py, "-m", "compileall", "-q", "backend/project/tiangong_agent_shell", "backend/project/tiangong_agent_runtime", "desktop", "frontend/linyuanzhe_frontend"], timeout=180)
    run([py, PROJECT / "run_prompt_integrator_activation_smoke_l67251.py"], env=be_fe_env)
    run([py, FRONTEND / "linyuanzhe_frontend" / "run_work_mode_activation_smoke_l67225.py"], env=fe_env)

    with tempfile.TemporaryDirectory(prefix="l67251_full_cli_") as tmp:
        target = Path(tmp) / "full_quality.txt"
        run([
            py,
            PROJECT / "run_agent.py",
            "--mock",
            "--once",
            "请创建 full_quality.txt 文件 内容 hello",
            "--workspace",
            tmp,
            "--tool-mode",
            "runtime_governed",
            "--planner-mode",
            "model_suggest",
            "--max-steps",
            "5",
        ], env=be_env)
        assert target.exists() and "hello" in target.read_text(encoding="utf-8"), target

    run([py, "-c", "from tiangong_agent_runtime.model_plan_compat_replay import replay_deepseek_plan_samples; r=replay_deepseek_plan_samples().public_dict(); assert r['ok'], r; print('deepseek_plan_replay PASS', r['pass_rate'])"], env=be_env)
    print("L6.72.51 full quality smoke PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
