from __future__ import annotations
import os, subprocess, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]; FRONTEND=ROOT/"frontend"; BACKEND=ROOT/"backend"/"project"
for p in (FRONTEND,BACKEND):
    if str(p) not in sys.path: sys.path.insert(0,str(p))
from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.contracts.file_transfer import FileTransferRequest
from linyuanzhe_frontend.contracts.hook_bus import HOOK_STAGE_PRE_FILE_TRANSFER_REQUEST, HookBus
from linyuanzhe_frontend.contracts.sse_events import RuntimeSseEvent
from linyuanzhe_frontend.contracts.provider_settings import provider_settings_write_policy
def require(name, cond, detail=""):
    if not cond: raise AssertionError(f"{name}: {detail}")
def run(cmd,cwd,timeout=60):
    e=dict(os.environ); e["PYTHONPATH"]=str(FRONTEND)+os.pathsep+str(BACKEND)+os.pathsep+e.get("PYTHONPATH",""); return subprocess.run(cmd,cwd=str(cwd),capture_output=True,text=True,timeout=timeout,env=e)
def main():
    if os.environ.get("TIANGONG_RUN_L6736_CLOSURE_FULL") != "1":
        print("L6.73.6 extra_qa_round4_round5_closure_smoke SKIP: legacy/full smoke is disabled by default; set TIANGONG_RUN_L6736_CLOSURE_FULL=1 to run the full path.")
        return 0
    checks=0; client=SseRuntimeClient("http://127.0.0.1:1")
    event=RuntimeSseEvent(event="run_terminal", display_channel="status", payload={"status":"completed"})
    require("run_terminal plain chat no task flow", client._event_requests_task_flow("run_terminal", {"status":"completed"}, event) is False); checks+=1
    event2=RuntimeSseEvent(event="run_terminal", display_channel="status", run_id="run_1", payload={"status":"completed","run_id":"run_1"})
    require("run_terminal with run_id task flow", client._event_requests_task_flow("run_terminal", {"status":"completed","run_id":"run_1"}, event2) is True); checks+=1
    with tempfile.TemporaryDirectory() as td:
        src=Path(td)/"用户上传.txt"; src.write_text("hello",encoding="utf-8"); req=FileTransferRequest.from_path(src); public=req.to_payload()
        require("public hides runtime_handoff_path", "runtime_handoff_path" not in public, str(public)); require("public hides raw path", str(src.resolve()) not in str(public), str(public))
        require("private bridge has raw path", req.to_bridge_payload().get("runtime_handoff_path")==str(src.resolve())); require("private header has raw path", "X-Linyuanzhe-Local-Handoff-Path-B64" in req.to_private_runtime_headers())
        bus=HookBus.default_frontend_bus(); ok=bus.evaluate(HOOK_STAGE_PRE_FILE_TRANSFER_REQUEST,{"payload":public}); require("hook allows sanitized public payload", ok.ok, ok.reason)
        bad=dict(public); bad["runtime_handoff_path"]=str(src.resolve()); blocked=bus.evaluate(HOOK_STAGE_PRE_FILE_TRANSFER_REQUEST,{"payload":bad}); require("hook blocks raw path public payload", not blocked.ok, blocked.reason); checks+=6
    policy=provider_settings_write_policy(); require("base_url public forbidden", "base_url" in policy.get("runtime_public_projection_forbidden_raw_fields", []), str(policy)); require("base_url display field", policy.get("runtime_public_projection_base_url_field")=="base_url_display", str(policy)); checks+=2
    for name,cmd,timeout in [("run_rc_preflight.sh relocatable",["bash","frontend/linyuanzhe_frontend/run_rc_preflight.sh","--contract-server"],90),("current validator",[sys.executable,"frontend/linyuanzhe_frontend/scripts/validate_demo_package.py"],120),("bat hygiene",[sys.executable,"backend/project/run_bat_line_ending_smoke_l67219.py"],60),("shell hygiene",[sys.executable,"backend/project/run_shell_line_ending_smoke_l67219.py"],60)]:
        r=run(cmd,ROOT,timeout); require(name,r.returncode==0,r.stderr[-1000:]+r.stdout[-1000:]); checks+=1
    print(f"l6736_extra_qa_round4_round5_closure_smoke PASS: {checks}/14"); return 0
if __name__=="__main__": raise SystemExit(main())
