from __future__ import annotations
import re, sys
from pathlib import Path
ALLOWED_CONTROL={9,10,13}
BROKEN_REMNANTS=(".linyuanzhective_assets","scriptsalidate_demo_package.py","scripts\nalidate_demo_package.py")
def _bad_controls(data:bytes)->list[int]: return sorted(set(b for b in data if b<32 and b not in ALLOWED_CONTROL))
def main()->int:
    root=Path(__file__).resolve().parents[2]; files=sorted(p for p in root.rglob("*.bat") if p.is_file())
    for p in files:
        rel=p.relative_to(root); data=p.read_bytes(); bad=_bad_controls(data)
        if bad: print(f"bat_line_ending_smoke FAIL: control chars in {rel}: {bad}",file=sys.stderr); return 1
        try: data.decode("utf-8")
        except UnicodeDecodeError as exc: print(f"bat_line_ending_smoke FAIL: non UTF-8 BAT {rel}: {exc}",file=sys.stderr); return 1
        if b"\r\n" not in data or b"\n" in data.replace(b"\r\n",b""):
            print(f"bat_line_ending_smoke FAIL: BAT must use CRLF only: {rel}",file=sys.stderr); return 1
        decoded=data.decode("utf-8")
        if re.search(r"(?im)^\s*cd\s+/d\s+%~dp0[^\r\n]*", decoded):
            print(f"bat_line_ending_smoke FAIL: unquoted cd /d %~dp0 path in {rel}",file=sys.stderr); return 1
        for remnant in BROKEN_REMNANTS:
            if remnant in decoded:
                print(f"bat_line_ending_smoke FAIL: broken control-char deletion remnant in {rel}: {remnant}",file=sys.stderr); return 1
    print(f"bat_line_ending_smoke PASS: {len(files)} BAT files checked for UTF-8, CRLF and control chars"); return 0
if __name__=="__main__": raise SystemExit(main())
