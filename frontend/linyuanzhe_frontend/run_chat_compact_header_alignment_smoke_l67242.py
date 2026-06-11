from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



from pathlib import Path

from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION, PROVIDER_CONFIG_SCHEMA_VERSION


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    root = Path(__file__).resolve().parent
    chat = (root / "ui" / "main_window_chat_runtime.py").read_text(encoding="utf-8")
    main = (root / "ui" / "main_window.py").read_text(encoding="utf-8")
    theme = (root / "ui" / "theme.py").read_text(encoding="utf-8")

    require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "frontend version must be L6.72.42")
    require(PROVIDER_CONFIG_SCHEMA_VERSION.startswith("tiangong.l6_73_") or PROVIDER_CONFIG_SCHEMA_VERSION.endswith(("l6_72_52.local_provider_config.v1", "l6_73_5.local_provider_config.v1")), "provider schema must accept L6.72.52+ / L6.73.x")
    require('text="天工造物V2"' in main, "fixed product title missing")
    require('Chip(context, "v2.0", "gray")' not in main, "topbar version chip must be removed")
    require('执行力优先 ·' not in main, "topbar explanatory text must be removed")
    require('Run {run_short}' not in chat and '当前：{tool_name}' not in chat and '事件：{last_event}' not in chat, "run workbench verbose explanations still present")
    require('text="任务工作台"' in chat and 'text=f"● {label}"' in chat, "compact task workbench title/lamp missing")
    for label in ['信息', '重连', '停止', '诊断']:
        require(f'("{label}",' in chat or f'text="{label}"' in chat, f"task workbench button {label} missing")
    require('height=74' in chat and 'height=2' in chat, "input area must be compact")
    require('for col, (label, command) in enumerate' in chat and 'uniform="input_ctrl"' in chat, "bottom controls must use aligned grid")
    require('"topbar_h": 38' in theme and '"statusbar_h": 24' in theme, "chrome dimensions must be compact")
    require('text="新会话"' not in main, "top-right new conversation button must remain removed")

    print("PASS L6.72.42-L6.72.43 compact header/button alignment smoke")


if __name__ == "__main__":
    main()
