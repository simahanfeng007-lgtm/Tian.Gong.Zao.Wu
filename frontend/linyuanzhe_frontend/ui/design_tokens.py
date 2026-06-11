from __future__ import annotations

"""L6.54 design token projection.

The token file keeps the Chinese enterprise visual language stable across
Tkinter now and future Web/Tauri shells. It is read-only display data.
"""

import json
from pathlib import Path
from typing import Any, Dict


DESIGN_TOKEN_CONTRACT_VERSION = "tiangong.l6_54.design_tokens.v1"
TOKEN_PATH = Path(__file__).resolve().parents[1] / "tokens" / "linyuanzhe_design_tokens.json"


def load_design_tokens() -> Dict[str, Any]:
    data = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    if data.get("schema") != DESIGN_TOKEN_CONTRACT_VERSION:
        raise ValueError("design token schema mismatch")
    return data


def design_token_policy() -> Dict[str, Any]:
    data = load_design_tokens()
    return {
        "schema": data["schema"],
        "theme": data["theme"],
        "home_principle": data["layout"]["home_principle"],
        "stream_flush_interval_ms": data["motion"]["stream_flush_interval_ms"],
        "dense_dashboard_forbidden": data["layout"]["dense_dashboard_forbidden"],
        "frontend_execution_permission": "none",
    }
