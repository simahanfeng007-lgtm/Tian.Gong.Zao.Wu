from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))


def main() -> int:
    print("run_desktop_demo 旧 Mock 演示入口已废弃。请使用 00_ASCII_START_HERE 或 01_启动入口 下的 START_FROM_ANYWHERE / start_desktop_auto 入口；本提示为兼容性成功退出。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
