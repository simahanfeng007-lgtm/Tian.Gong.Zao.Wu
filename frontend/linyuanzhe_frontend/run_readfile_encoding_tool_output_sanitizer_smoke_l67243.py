from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))



import tempfile
from pathlib import Path

from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient
from linyuanzhe_frontend.ui.main_window_chat_runtime import enhance_conversation_readability
from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def main() -> None:
    require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "frontend version must be L6.72.43")
    client = SseRuntimeClient("http://127.0.0.1:8787")
    garbled = "readfile: ok | �! □□�H�\\x00\\x01PK\\x03\\x04 random binary"
    cleaned = client._clean_assistant_visible_content(garbled, final=False)
    require("readfile: ok" not in cleaned.lower(), "raw readfile prefix must be hidden")
    require("乱码" in cleaned or cleaned == "", "garbled payload must be hidden or explained")

    rendered = enhance_conversation_readability("�! □□�H�\\x00\\x01PK\\x03\\x04", is_assistant=True)
    require("主会话已隐藏原始输出" in rendered, "renderer must guard cached garbled text")

    print("PASS L6.72.43 readfile encoding + tool output sanitizer frontend smoke")


if __name__ == "__main__":
    main()
