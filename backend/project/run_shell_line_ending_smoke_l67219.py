from __future__ import annotations
import os, stat, subprocess, sys
from pathlib import Path
ALLOWED_CONTROL={9,10,13}
def _bad_controls(data:bytes)->list[int]: return sorted(set(b for b in data if b<32 and b not in ALLOWED_CONTROL))
def _restore_exec_bit(p:Path)->bool:
    try:
        mode=p.stat().st_mode
        if mode & stat.S_IXUSR:
            return False
        os.chmod(p, mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        return True
    except OSError:
        return False
def main()->int:
    root=Path(__file__).resolve().parents[2]; files=sorted([p for pattern in ("*.sh","*.command") for p in root.rglob(pattern) if p.is_file()]); restored=[]; non_exec=[]
    for p in files:
        rel=p.relative_to(root); data=p.read_bytes(); bad=_bad_controls(data)
        if bad: print(f"shell_line_ending_smoke FAIL: control chars in {rel}: {bad}",file=sys.stderr); return 1
        try: data.decode("utf-8")
        except UnicodeDecodeError as exc: print(f"shell_line_ending_smoke FAIL: non UTF-8 script {rel}: {exc}",file=sys.stderr); return 1
        if b"\r" in data or b"\n" not in data: print(f"shell_line_ending_smoke FAIL: SH/COMMAND must use LF only: {rel}",file=sys.stderr); return 1
        r=subprocess.run(["bash","-n",str(p)],cwd=str(root),stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        if r.returncode!=0: print(f"shell_line_ending_smoke FAIL: bash -n failed for {rel}: {r.stderr[-800:]}",file=sys.stderr); return 1
        if not (p.stat().st_mode & stat.S_IXUSR):
            if _restore_exec_bit(p): restored.append(str(rel))
            else: non_exec.append(str(rel))
    if non_exec: print("shell_line_ending_smoke FAIL: scripts not executable and auto-restore failed: "+", ".join(non_exec[:20]),file=sys.stderr); return 1
    suffix=f"; auto-restored executable bit for {len(restored)} scripts" if restored else ""
    print(f"shell_line_ending_smoke PASS: {len(files)} SH/COMMAND files checked for LF, bash -n, executable bit and control chars{suffix}"); return 0
if __name__=="__main__": raise SystemExit(main())
