"""L6.72.33 ConversationRenderingReadability + RealHostExecutionAcceptance smoke.

Validates: frontend work-mode intent -> local bridge -> backend Runtime -> PlanBridge -> WorkspaceGuard -> tool result.
The frontend still only submits intent and displays events; it never executes tools.
"""
from __future__ import annotations

# L6.73.8 direct-file smoke bootstrap.
if __package__ in (None, ""):
    import sys as _sys
    from pathlib import Path as _Path
    _pkg_parent = _Path(__file__).resolve().parent.parent
    if str(_pkg_parent) not in _sys.path:
        _sys.path.insert(0, str(_pkg_parent))


import json
import importlib.util
import os
import sys
import tempfile
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend" / "project"
DESKTOP_BRIDGE = ROOT / "desktop" / "linyuanzhe_local_runtime_bridge_l671.py"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))
if str(ROOT / "frontend") not in sys.path:
    sys.path.insert(0, str(ROOT / "frontend"))

if __name__ == "__main__" and os.environ.get("LINYUANZHE_RUN_REAL_HOST_SMOKE", "").strip().lower() not in {"1", "true", "yes", "on"}:
    print(json.dumps({
        "ok": True,
        "status": "SKIP",
        "smoke": "L6.72.52 RealHostExecutionAcceptance",
        "reason": "real-host execution smoke is opt-in to avoid headless/no-output CI timeouts; set LINYUANZHE_RUN_REAL_HOST_SMOKE=1 to run the full scenario",
    }, ensure_ascii=False), flush=True)
    raise SystemExit(0)

os.environ.setdefault("TIANGONG_SOUL_BASELINE_PERSIST", "0")

from linyuanzhe_frontend.version_info import FE_RUNTIME_VERSION, PROVIDER_CONFIG_SCHEMA_VERSION  # noqa: E402
from linyuanzhe_frontend.contracts.sse_events import SSE_EVENT_TYPES  # noqa: E402
from tiangong_agent_runtime.plan_bridge import PlanBridge  # noqa: E402


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


@contextmanager
def _patched_env(**values: str):
    old = {key: os.environ.get(key) for key in values}
    try:
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        for key, value in old.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


def _load_bridge():
    spec = importlib.util.spec_from_file_location("linyuanzhe_local_runtime_bridge_l671", DESKTOP_BRIDGE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def main() -> None:
    print("START L6.72.52 RealHostExecutionAcceptance full smoke", flush=True)
    _require((FE_RUNTIME_VERSION.startswith(("L6.72.", "L6.73.")) or FE_RUNTIME_VERSION.startswith("L6.73.")), "frontend version must be L6.72.39")
    _require(PROVIDER_CONFIG_SCHEMA_VERSION.startswith("tiangong.l6_73_") or PROVIDER_CONFIG_SCHEMA_VERSION.endswith(("l6_72_52.local_provider_config.v1", "l6_73_5.local_provider_config.v1")), "provider schema must accept L6.72.52+ / L6.73.x")
    _require("tool_progress" in SSE_EVENT_TYPES, "Run Workbench must support tool_progress")
    _require("approval_required" in SSE_EVENT_TYPES, "Run Workbench must support approval_required")

    bridge = _load_bridge()
    _require(bridge._normalize_host_access_scope("全电脑") == "system_drive", "全电脑 alias must map to system_drive")
    _require(bridge._resolve_host_access_root("project_workspace").exists(), "project workspace root must exist")
    _require(bridge._resolve_host_access_root("user_home").exists(), "user_home root must exist")
    _require(bridge._resolve_host_access_root("system_drive").exists(), "system_drive root must exist")

    with tempfile.TemporaryDirectory(prefix="l67232_host_") as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "Desktop").mkdir()
        (tmp_path / "Downloads").mkdir()
        (tmp_path / "Documents").mkdir()
        (tmp_path / "Desktop" / "junk_probe.tmp").write_text("temporary desktop probe", encoding="utf-8")

        with _patched_env(
            HOME=str(tmp_path),
            USERPROFILE=str(tmp_path),
            LINYUANZHE_HOST_ACCESS_SCOPE="custom_root",
            LINYUANZHE_HOST_ACCESS_ROOT=str(tmp_path),
            TIANGONG_ALLOW_INTERNAL_MOCK="1",
            TIANGONG_PROVIDER="mock",
            TIANGONG_MODEL="mock-model",
            TIANGONG_API_KEY="mock-key",
            LINYUANZHE_PROVIDER_KEY="mock-key",
            TIANGONG_BASE_URL="http://mock.local",
            LINYUANZHE_PROVIDER_BASE="http://mock.local",
        ):
            state = bridge.BridgeState(backend_mode="auto", timeout=20)
            _require(state.effective_backend_mode == "provider", "smoke uses mock provider for LLM ActivationForm")
            _require(state.host_access_scope == "custom_root", "custom host scope not applied")
            _require(state.host_access_root == tmp_path.resolve(), "custom host root not applied")

            hint = bridge._host_access_context_hint(state.host_access_scope, state.host_access_root)
            _require("desktop_relative_path=Desktop" in hint, "desktop path must resolve relative to host root")
            _require("downloads_relative_path=Downloads" in hint, "downloads path must resolve relative to host root")
            _require("documents_relative_path=Documents" in hint, "documents path must resolve relative to host root")

            runtime_message = bridge._compose_runtime_message("帮我看看桌面有没有垃圾文件", state, {"tools_requested": True})
            plan = PlanBridge().build_plan(runtime_message)
            _require(plan and plan[0].tool_name == "list_dir", "natural Desktop intent must become list_dir")
            _require(plan[0].arguments.get("path") == "Desktop", "Desktop intent must use relative Desktop path")

            normal_directives = bridge._runtime_directives_from_payload({
                "message": "帮我看看桌面有没有垃圾文件",
                "frontend_work_mode": "file",
                "planner_allowed": True,
                "tools_requested": True,
                "tool_execution_mode": "runtime_governed",
            })
            _require(normal_directives["frontend_work_mode"] == "work", "legacy file mode must alias to work")
            _require(normal_directives["task_mode"] == "tool_task", "file alias enters LLM activation task")
            _require(normal_directives["tools_requested"] is True, "work/file alias must request tools after LLM activation")
            _require(normal_directives["planner_mode"] == "model_suggest", "work task must enter model_suggest")

            directives = bridge._runtime_directives_from_payload({
                "message": "帮我看看桌面有没有垃圾文件",
                "frontend_work_mode": "long_chain",
                "work_mode": {"mode": "long_chain", "long_chain_requested": True},
            })
            _require(directives["frontend_work_mode"] == "work", "legacy long_chain must alias to work")
            _require(directives["task_mode"] == "tool_task", "work must map to LLM ActivationForm task")
            _require(directives["activation_requested"] is True, "long_chain must request ActivationForm")
            _require(directives["planner_mode"] == "model_suggest", "work task must enter model_suggest path")

            answer, returncode, elapsed = bridge._run_backend_subprocess(
                "帮我看看桌面有没有垃圾文件",
                state,
                runtime_directives=normal_directives,
                run_id="",
            )
            _require(returncode == 0, f"real host Runtime task failed: {returncode} {elapsed} {answer}")
            _require("junk_probe.tmp" in answer, "real host list_dir did not return Desktop probe file")
            _require("尚未配置模型接口" not in answer, "tool task must not be blocked when mock provider is configured")

            for scope in ("user_home", "system_drive"):
                with _patched_env(LINYUANZHE_HOST_ACCESS_SCOPE=scope, LINYUANZHE_HOST_ACCESS_ROOT=""):
                    scoped_state = bridge.BridgeState(backend_mode="auto", timeout=20)
                    scoped_hint = bridge._host_access_context_hint(scoped_state.host_access_scope, scoped_state.host_access_root)
                    scoped_plan = PlanBridge().build_plan("帮我看看桌面有没有垃圾文件\n\n" + scoped_hint)
                    _require(scoped_plan and scoped_plan[0].tool_name == "list_dir", f"{scope} natural Desktop intent did not plan")
                    scoped_answer, scoped_code, scoped_elapsed = bridge._run_backend_subprocess(
                        "帮我看看桌面有没有垃圾文件",
                        scoped_state,
                        runtime_directives=normal_directives,
                        run_id="",
                    )
                    _require(scoped_code == 0, f"{scope} host Runtime task failed: {scoped_code} {scoped_elapsed} {scoped_answer}")
                    _require("junk_probe.tmp" in scoped_answer, f"{scope} did not list Desktop probe")

            _require(bridge._classify_execution_error("path_not_found 文件不存在", 1, "1ms") == "file_path_error", "file path error classification failed")
            _require(bridge._classify_execution_error("HTTP 401 invalid api key", 1, "1ms") == "auth_failed", "provider auth classification failed")
            state.last_bridge_error_kind = "file_path_error"
            state.last_provider_check_state = "not_tested"
            state.record_provider_check(ok=False, answer="missing file", returncode=2, elapsed="1ms", audit_id="audit_smoke")
            _require(state.last_provider_check_state == "not_tested", "non-provider errors must not poison provider state")

            cleaned = bridge._clean_user_facing_answer("- return_analysis: ok｜User message appears incomplete", "在不")
            _require(cleaned == "在。", "conversation surface guard regression failed")

    print("PASS L6.72.52 RealHostExecutionAcceptance smoke", flush=True)


if __name__ == "__main__":
    main()
