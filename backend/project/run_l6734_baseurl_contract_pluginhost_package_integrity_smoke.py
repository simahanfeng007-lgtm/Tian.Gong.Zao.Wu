"""L6.73.4 Base URL contract / plugin host / packaging integrity smoke."""

from __future__ import annotations

import importlib
import inspect
import json
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "backend" / "project"
FRONTEND = ROOT / "frontend"
for item in (str(PROJECT), str(FRONTEND)):
    if item not in sys.path:
        sys.path.insert(0, item)


def _check(condition: bool, name: str, details: str = "") -> dict[str, object]:
    return {"name": name, "ok": bool(condition), "details": details}


def main() -> int:
    checks: list[dict[str, object]] = []

    from tiangong_agent_runtime.frontend_contract import validate_frontend_contract

    contract = validate_frontend_contract().public_dict()
    checks.append(_check(contract.get("ok") is True, "frontend_contract_ok", json.dumps(contract, ensure_ascii=False)))

    import tiangong_kernel.l5_plugin_host as plugin_host

    importlib.import_module("tiangong_kernel.l5_plugin_host.model_capability_invariants")
    importlib.import_module("tiangong_kernel.l5_plugin_host.phase8_closure")
    for exported in (
        "L5Phase1RegressionBaselineRecord",
        "L5Phase1RegressionEvidenceIndex",
        "L5Phase1TestEvidenceIndex",
        "L5Phase1TestEvidenceRecord",
    ):
        checks.append(_check(hasattr(plugin_host, exported), f"plugin_host_exports_{exported}"))

    from linyuanzhe_frontend.clients.runtime_integration_probe import SECRET_RENDER_MARKERS

    endpoint_markers = {"api.deepseek", "provider.example.invalid", "deepseek.example.invalid", "provider-write-l658"}
    checks.append(_check(not endpoint_markers.intersection(set(SECRET_RENDER_MARKERS)), "rc_secret_markers_exclude_base_url_fixtures", str(SECRET_RENDER_MARKERS)))

    from linyuanzhe_frontend.clients.sse_runtime_client import SseRuntimeClient

    client = SseRuntimeClient("http://127.0.0.1:65535")
    client._apply_provider_settings({  # type: ignore[attr-defined]
        "payload": {
            "provider": "deepseek",
            "model": "deepseek-v4-pro",
            "base_url": "https://api.deepseek.com",
            "base_url_normalized": "https://api.deepseek.com/v1",
            "base_url_configured": True,
            "api_key": "must_not_survive",
        }
    })
    projected = client.get_provider_settings()
    checks.append(_check("base_url" not in projected and "base_url_normalized" not in projected and "api_key" not in projected, "sse_provider_projection_has_no_raw_base_url_or_key", str(projected)))
    checks.append(_check(projected.get("base_url_display") == "https://api.deepseek.com", "sse_raw_base_url_converted_to_display", str(projected)))

    from linyuanzhe_frontend.contracts.model_settings import sanitize_runtime_settings
    from linyuanzhe_frontend.contracts.provider_settings import ProviderSettingsWriteRequest, normalize_host_access_scope
    from linyuanzhe_frontend.ui.localization import host_access_scope_value

    scope_cases = {
        "全电脑 / 系统盘": "system_drive",
        "全电脑/系统盘": "system_drive",
        "用户目录": "user_home",
        "用户主目录": "user_home",
        "项目工作区": "project_workspace",
        "项目目录": "project_workspace",
        "自定义根目录": "custom_root",
        "自定义": "custom_root",
    }
    for label, expected in scope_cases.items():
        checks.append(_check(normalize_host_access_scope(label) == expected, f"host_scope_normalize_{label}", normalize_host_access_scope(label)))
        checks.append(_check(host_access_scope_value(label) == expected, f"host_scope_ui_value_{label}", host_access_scope_value(label)))
        checks.append(_check(sanitize_runtime_settings({"host_access_scope": label})["host_access_scope"] == expected, f"host_scope_runtime_snapshot_{label}"))
        checks.append(_check(ProviderSettingsWriteRequest.from_form({"host_access_scope": label}).host_access_scope == expected, f"host_scope_write_request_{label}"))

    from linyuanzhe_frontend.ui.main_window_feature_pages import FeaturePagesMixin

    hydrate_src = inspect.getsource(FeaturePagesMixin._hydrate_provider_form_from_public)
    public_src = inspect.getsource(FeaturePagesMixin._get_provider_settings_public)
    checks.append(_check('provider_settings.get("base_url")' not in hydrate_src, "ui_hydrate_does_not_read_raw_base_url"))
    checks.append(_check('"base_url",' not in public_src and '"base_url"' not in public_src.split('allowed =', 1)[-1].split('safe:', 1)[0], "ui_public_allowed_excludes_raw_base_url"))
    checks.append(_check('if state in {"ready", "就绪"}' in inspect.getsource(FeaturePagesMixin._provider_status_color), "provider_ready_color_accepts_machine_value"))

    mojibake_chars = set("σΣτΦµΘ╕╛╜╚╔╗║╝╞╟╧╨╩╦╠╣╒╓╫╬╥╙╘╤╪╢╡⌐₧")
    mojibake_paths = [str(path.relative_to(ROOT)) for path in ROOT.rglob("*") if any(ch in path.name for ch in mojibake_chars)]
    checks.append(_check(not mojibake_paths, "source_tree_has_no_mojibake_names", "\n".join(mojibake_paths[:20])))

    ok = all(row["ok"] for row in checks)
    report = {"ok": ok, "case_count": len(checks), "checks": checks}
    out = Path(tempfile.mkdtemp(prefix="linyuanzhe_smoke_report_")) / "l6734_baseurl_contract_pluginhost_package_integrity_smoke_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": ok, "case_count": len(checks), "failed": [row for row in checks if not row["ok"]], "report": f"<tmp>/{out.name}"}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
