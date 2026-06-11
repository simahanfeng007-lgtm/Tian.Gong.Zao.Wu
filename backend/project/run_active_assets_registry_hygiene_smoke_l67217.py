from __future__ import annotations

import json
import tempfile
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry

SCHEMA = "tiangong.l67218.active_assets_registry_hygiene_smoke.v2"


def main() -> int:
    # Q12: build an active registry in a temporary workspace; do not require delivery .linyuanzhe.
    with tempfile.TemporaryDirectory(prefix="active_assets_registry_hygiene_") as tmp:
        workspace = Path(tmp) / "workspace"
        runtime = RuntimeEntry()
        drill = runtime.run_text("asset-activate drill pytest missing tests", workspace=workspace, max_steps=20)
        assert drill.results and all(item.ok for item in drill.results), "failed to seed temporary active assets"
        registry = workspace / ".linyuanzhe" / "active_assets" / "r20" / "active_assets_registry.json"
        assert registry.exists() and registry.stat().st_size > 0, "active_assets_registry.json missing or empty"
        text = registry.read_text(encoding="utf-8")
        data = json.loads(text)
        assert data.get("active_count", 0) > 0, "active_count must be > 0"
        assert isinstance(data.get("records"), list) and data["records"], "records must be non-empty"
        assert data.get("relocation_supported") is True, "relocation_supported must be true"
        assert "/mnt/data/work_" not in text and "\\mnt\\data\\work_" not in text, "registry contains build-machine absolute path"
        for rec in data["records"]:
            assert rec.get("active_dir_relative"), "record missing active_dir_relative"
            assert rec.get("active_manifest_relative"), "record missing active_manifest_relative"
        print({"schema": SCHEMA, "status": "PASS", "active_count": data.get("active_count"), "records": len(data["records"]), "workspace": "<tmp>"})
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
