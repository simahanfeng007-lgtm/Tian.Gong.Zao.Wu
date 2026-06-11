from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BRIDGE_PATH = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"


def _load_bridge():
    spec = importlib.util.spec_from_file_location("linyuanzhe_local_runtime_bridge_l67231", BRIDGE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main() -> int:
    bridge = _load_bridge()
    state = bridge.BridgeState(backend_mode="auto", timeout=30)
    assert state.host_access_scope in {"system_drive", "user_home", "project_workspace", "custom_root"}
    assert state.host_access_root.exists(), state.host_access_root
    assert bridge._normalize_host_access_scope("全电脑") == "system_drive"
    projection = state.provider_projection()
    assert projection["host_access_scope"] == state.host_access_scope
    assert projection["host_access_runtime_only"] is True
    message = bridge._compose_runtime_message("帮我看看桌面有没有垃圾文件", state, {"tools_requested": True})
    assert "桌面端主机文件访问提示" in message
    assert "desktop_relative_path" in message
    assert "禁止使用 C" in message
    cmd = ["x"]
    # The real subprocess smoke is covered by compileall/runtime smoke; here we verify
    # the desktop bridge now has a host root that can be passed to --workspace.
    assert str(state.host_access_root)
    print("PASS L6.72.31-L6.72.33 host computer access smoke")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
