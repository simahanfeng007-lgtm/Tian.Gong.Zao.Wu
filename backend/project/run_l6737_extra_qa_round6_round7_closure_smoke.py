from __future__ import annotations
import os, subprocess, sys, tempfile, stat
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
FRONTEND=ROOT/"frontend"
BACKEND=ROOT/"backend"/"project"
for p in (FRONTEND,BACKEND):
    if str(p) not in sys.path: sys.path.insert(0,str(p))

def require(name:str, cond:bool, detail:str="") -> None:
    if not cond: raise AssertionError(f"{name}: {detail}")

def run(cmd:list[str], timeout:int=90) -> subprocess.CompletedProcess[str]:
    env=dict(os.environ)
    env["PYTHONPATH"]=str(FRONTEND)+os.pathsep+str(BACKEND)+os.pathsep+env.get("PYTHONPATH","")
    env.setdefault("PYTHONNOUSERSITE","1")
    return subprocess.run(cmd,cwd=str(ROOT),capture_output=True,text=True,timeout=timeout,env=env)

def main() -> int:
    if os.environ.get("TIANGONG_RUN_L6737_CLOSURE_FULL") != "1":
        print("L6.73.7 extra_qa_round6_round7_closure_smoke SKIP: legacy/full smoke is disabled by default; set TIANGONG_RUN_L6737_CLOSURE_FULL=1 to run the full path.")
        return 0
    checks=0
    bat=(ROOT/"launchers/run_workmode_activation_check_l6718.bat").read_text(encoding="utf-8")
    require("workmode BAT path remnant removed", ".linyuanzhective_assets" not in bat, bat); checks+=1
    require("workmode BAT active_assets path restored", ".linyuanzhe\\active_assets" in bat or ".linyuanzhe/active_assets" in bat, bat); checks+=1

    r=run([sys.executable,"00_ASCII_START_HERE/python/SELF_CHECK_L6710.py"], timeout=60)
    require("default self-check returns 0", r.returncode==0, r.stderr+r.stdout); checks+=1
    require("default self-check display is SKIP", "tkinter_display" in r.stdout and "SKIP" in r.stdout and "tkinter_display" in r.stdout, r.stdout); checks+=1
    require("default self-check display is not PASS", "tkinter_display      : PASS" not in r.stdout and "tkinter_display : PASS" not in r.stdout, r.stdout); checks+=1

    r=run([sys.executable,"-S","backend/project/run_document_parse_smoke_l67244.py"], timeout=90)
    require("document_parse python -S returns 0", r.returncode==0, r.stderr+r.stdout); checks+=1
    require("document_parse python -S PASS or SKIP", "PASS" in r.stdout or "SKIP" in r.stdout, r.stdout); checks+=1

    from linyuanzhe_frontend.contracts.provider_settings import ProviderSettingsWriteResult
    legacy=ProviderSettingsWriteResult.from_runtime_response({"payload":{"status":"saved","base_url_configured":True,"base_url":"https://api.example.invalid/v1"}})
    require("legacy base_url converted to display", legacy.base_url_display=="https://api.example.invalid/v1", repr(legacy)); checks+=1
    require("provider result dict has no raw base_url", "base_url" not in legacy.to_dict(), str(legacy.to_dict())); checks+=1

    # Simulate Python zipfile.extractall mode loss, then ensure shell hygiene auto-restores.
    shell_files=[p for pattern in ("*.sh","*.command") for p in ROOT.rglob(pattern) if p.is_file()]
    changed=[]
    for p in shell_files[:5]:
        try:
            os.chmod(p, p.stat().st_mode & ~stat.S_IXUSR & ~stat.S_IXGRP & ~stat.S_IXOTH)
            changed.append(p)
        except OSError:
            pass
    r=run([sys.executable,"backend/project/run_shell_line_ending_smoke_l67219.py"], timeout=90)
    require("shell hygiene auto-restores executable bit", r.returncode==0, r.stderr+r.stdout); checks+=1
    require("shell hygiene mentions PASS", "PASS" in r.stdout, r.stdout); checks+=1

    r=run([sys.executable,"backend/project/run_bat_line_ending_smoke_l67219.py"], timeout=60)
    require("bat hygiene detects no remnants", r.returncode==0, r.stderr+r.stdout); checks+=1

    for rel in ("frontend/linyuanzhe_frontend/DEMO_START_HERE.txt","frontend/linyuanzhe_frontend/README_FE01.txt"):
        txt=(ROOT/rel).read_text(encoding="utf-8")
        require(f"{rel} current version", "L6.73.8" in txt, txt[:200]); checks+=1
        require(f"{rel} no active old headline", "L6.58 真实后端" not in txt and "L6.54 真实 Runtime" not in txt, txt[:200]); checks+=1

    from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION
    require("version_info bumped", FE_RUNTIME_VERSION=="L6.73.8", FE_RUNTIME_VERSION); checks+=1

    r=run([sys.executable,"scripts/verify_launchers_l67220.py"], timeout=90)
    require("launcher verifier current pass", r.returncode==0, r.stderr+r.stdout); checks+=1

    print(f"l6737_extra_qa_round6_round7_closure_smoke PASS: {checks}/18")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
