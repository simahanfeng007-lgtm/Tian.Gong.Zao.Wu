from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

SCHEMA = "tiangong.l67218.bridge_network_asset_smoke.v1"
ROOT = Path(__file__).resolve().parents[2]
PROJECT = Path(__file__).resolve().parent


def _import_backend_network_policy() -> None:
    sys.path.insert(0, str(PROJECT))
    from tiangong_agent_shell.network_policy import NetworkPolicyError, validate_url

    validate_url("http://127.0.0.1:8787/health/runtime", allow_loopback_http=True, purpose="smoke_loopback")
    try:
        validate_url("http://example.com/v1/chat/completions", allow_loopback_http=True, purpose="smoke_remote")
    except NetworkPolicyError:
        pass
    else:
        raise AssertionError("remote HTTP must be blocked")
    validate_url("https://api.deepseek.com/chat/completions", allow_loopback_http=True, purpose="smoke_https")


def _import_frontend_network_policy() -> None:
    sys.path.insert(0, str(ROOT / "frontend"))
    from linyuanzhe_frontend.clients.network_policy import NetworkPolicyError, validate_url

    validate_url("http://localhost:8787", allow_loopback_http=True, purpose="frontend_loopback")
    try:
        validate_url("http://runtime.example.invalid", allow_loopback_http=True, purpose="frontend_remote")
    except NetworkPolicyError:
        pass
    else:
        raise AssertionError("frontend remote HTTP must be blocked")


def _bridge_stderr_is_not_user_text() -> None:
    sys.path.insert(0, str(ROOT / "desktop"))
    import linyuanzhe_local_runtime_bridge_l671 as bridge

    class DummyState:
        provider_key = "mockkey_secret-value"
        provider_base = "https://api.deepseek.com"
        timeout = 15
        tool_execution_mode = "runtime_governed"
        effective_backend_mode = "provider"
        provider = "deepseek"
        model = "deepseek-chat"
        chat_history_file = Path(tempfile.gettempdir()) / "linyuanzhe_smoke_chat.json"
        persona_name = "临渊者"
        persona_prompt = ""
        file_handoffs = []
        last_bridge_diagnostic = ""
        last_bridge_error_kind = ""

    old_popen = bridge.subprocess.Popen

    class FakeProc:
        returncode = 7
        pid = 67227
        def poll(self):
            return self.returncode
        def terminate(self):
            pass
        def kill(self):
            pass
        def communicate(self, timeout=None):
            return "", "[错误] api_key=mockkey_secret-value\n[运行链] 未生成可执行计划，将退回普通模型对话"

    def fake_popen(*args, **kwargs):
        return FakeProc()

    bridge.subprocess.Popen = fake_popen
    try:
        answer, code, _elapsed = bridge._run_backend_subprocess("测试", DummyState())
    finally:
        bridge.subprocess.Popen = old_popen
    assert code == 7
    assert "mockkey_secret-value" not in answer
    assert "[运行链]" not in answer
    assert "未生成可执行计划" not in answer
    assert "stderr" in answer or "诊断" in answer


def _registry_has_no_absolute_paths() -> None:
    """Build the active-assets registry in an isolated workspace.

    Q19: the release ZIP is intentionally delivered without a runtime
    .linyuanzhe tree.  This smoke used to hard-read backend/project/.linyuanzhe
    and therefore failed on every clean package.  Generate a temporary registry
    instead, then assert the registry remains relocatable and free of host paths.
    """
    sys.path.insert(0, str(PROJECT))
    from tiangong_agent_runtime.runtime_entry import RuntimeEntry

    with tempfile.TemporaryDirectory(prefix="bridge_asset_registry_") as tmp:
        workspace = Path(tmp) / "workspace"
        runtime = RuntimeEntry()
        drill = runtime.run_text("asset-activate drill pytest missing tests", workspace=workspace, max_steps=20)
        assert drill.results and all(item.ok for item in drill.results), "failed to seed temporary active assets"
        p = workspace / ".linyuanzhe" / "active_assets" / "r20" / "active_assets_registry.json"
        text = p.read_text(encoding="utf-8")
        assert p.stat().st_size > 0
        assert not any(marker in text for marker in ("/mnt/data/", "/tmp/", "/home/", "C:\\", "D:\\"))
        data = json.loads(text)
        assert data.get("active_count", 0) > 0
        assert data.get("relocation_supported") is True


def _dataup_network_policy_blocks_remote_http() -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from network_policy_l67218 import NetworkPolicyError, validate_url

    try:
        validate_url("http://example.com/dataup/latest.json", allow_loopback_http=False, purpose="dataup")
    except NetworkPolicyError:
        pass
    else:
        raise AssertionError("DataUp remote HTTP must be blocked")
    validate_url("https://example.com/dataup/latest.json", allow_loopback_http=False, purpose="dataup")


def main() -> int:
    _import_backend_network_policy()
    _import_frontend_network_policy()
    _bridge_stderr_is_not_user_text()
    _registry_has_no_absolute_paths()
    _dataup_network_policy_blocks_remote_http()
    print({"schema": SCHEMA, "status": "PASS"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
