from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from tiangong_agent_runtime.execution_policy import RiskLevel
from tiangong_agent_runtime.plan_bridge import PlanBridge
from tiangong_agent_runtime.plan_schema import validate_and_build_plan
from tiangong_agent_runtime.provider_adaptation_shell import (
    ProviderAdaptationBridge,
    stable_provider_adaptation_digest,
)
from tiangong_agent_runtime.risk_classifier import RiskClassifier
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def test_l6_27_empty_bridge_is_shell_only() -> None:
    bridge = ProviderAdaptationBridge()
    snapshot = bridge.public_dict()
    assert snapshot["schema"] == "tiangong.l6_27.provider_adaptation_shell.v1"
    assert snapshot["status"] == "empty"


def test_l6_27_bridge_builds_five_provider_profiles_without_live_call() -> None:
    bridge = ProviderAdaptationBridge()
    report = bridge.build(notes="真实 Provider 适配外壳，不裸调 SDK。")
    payload = report.public_dict()
    assert payload["schema"] == "tiangong.l6_27.provider_adaptation_shell.v1"
    assert payload["status"] == "provider_adaptation_shell_ready"
    assert payload["provider_count"] == 5
    assert payload["route_count"] == 6
    assert payload["execution_first"] is True
    assert payload["shell_only"] is True
    assert payload["provider_declaration_only"] is True
    assert payload["kernel_pollution_guard"] is True
    assert payload["performs_network_call"] is False
    assert payload["reads_credentials"] is False
    assert payload["stores_credentials"] is False
    assert payload["imports_provider_sdk"] is False
    assert payload["invokes_model"] is False
    assert payload["registers_formal_provider_adapter"] is False
    assert payload["modifies_kernel"] is False
    assert payload["bypasses_governance"] is False
    providers = {item["provider_id"]: item for item in payload["provider_profiles"]}
    assert set(providers) == {"deepseek_v4", "mimo", "glm_5_1", "minimax_m3", "gpt_5_5"}
    assert providers["mimo"]["lower_case_model_ids_required"] is True
    assert all(item["disabled_by_default"] is True for item in providers.values())
    assert all(item["requires_l5_permit"] is True for item in providers.values())
    routes = {(item["provider_id"], item["surface_id"]): item for item in payload["api_surface_routes"]}
    assert ("mimo", "ordinary_api") in routes
    assert ("mimo", "token_plan_api") in routes
    assert routes[("mimo", "ordinary_api")]["normal_api_supported"] is True
    assert routes[("mimo", "ordinary_api")]["plan_api_supported"] is False
    assert routes[("mimo", "token_plan_api")]["plan_api_supported"] is True
    assert routes[("gpt_5_5", "responses_api")]["plan_api_supported"] is True
    assert all(route["live_call_enabled"] is False for route in payload["api_surface_routes"])
    assert all(route["sdk_import_required"] is False for route in payload["api_surface_routes"])
    assert all(mount["no_plugin_sdk_call"] is True for mount in payload["governance_mounts"])
    assert all(mount["no_l6_direct_network_call"] is True for mount in payload["governance_mounts"])
    assert all(draft["dry_run_only"] is True for draft in payload["health_check_drafts"])
    assert all(draft["performs_network_call"] is False for draft in payload["health_check_drafts"])
    assert payload["report_digest"]
    assert stable_provider_adaptation_digest(report) == payload["report_digest"]


def test_l6_27_runtime_builds_provider_adaptation_shell(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.run_provider_adaptation(
        workspace=tmp_path,
        path=".",
        notes="L6.27 Provider 适配，普通 API 与 plan API 壳装。",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        refresh_shell_mount=True,
    )
    assert result.results[-1].tool_name == "build_provider_adaptation"
    assert result.results[-1].status is ToolResultStatus.OK
    report = runtime.provider_adaptation_snapshot()
    assert report["schema"] == "tiangong.l6_27.provider_adaptation_shell.v1"
    assert report["provider_count"] == 5
    assert report["route_count"] == 6
    assert report["shell_mount_status"] in {"shell_mount_ready", "unknown", "empty"}
    assert report["provider_declaration_only"] is True
    assert report["performs_network_call"] is False
    assert not (tmp_path / "provider_live_call.log").exists()


def test_l6_27_tool_is_a2_and_registered() -> None:
    runtime = RuntimeEntry()
    names = {tool.name: tool.default_risk for tool in runtime.available_tools()}
    assert names["build_provider_adaptation"] == "A2"
    risk, reason = RiskClassifier().classify(ToolInvocation("build_provider_adaptation", {"path": "."}))
    assert risk is RiskLevel.A2
    assert "L6.27" in reason
    assert "不触网" in reason
    assert "不读密钥" in reason
    assert "不注册正式适配器" in reason


def test_l6_27_plan_bridge_and_schema_allow_provider_adaptation() -> None:
    plan = PlanBridge().build_plan("provider-build . L6.27 真实 Provider 适配")
    assert [step.tool_name for step in plan] == ["build_provider_adaptation"]
    built = validate_and_build_plan(
        {
            "steps": [
                {
                    "tool_name": "build_provider_adaptation",
                    "arguments": {"path": ".", "notes": "只生成 Provider 适配外壳"},
                }
            ]
        }
    )
    assert built[0].tool_name == "build_provider_adaptation"
    assert built[0].arguments["path"] == "."


def test_l6_27_cli_provider_build_and_export(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    proc = subprocess.run(
        [
            sys.executable,
            "run_agent.py",
            "--mock",
            "--tool-mode",
            "runtime_governed",
            "--workspace",
            str(tmp_path),
        ],
        cwd=ROOT,
        input="/provider-build . Provider 适配外壳\n/provider\n/provider-save provider_adaptation.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "L6.27 Provider 适配外壳" in proc.stdout
    exported = json.loads((tmp_path / "provider_adaptation.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_27.provider_adaptation_shell.v1"
    assert exported["provider_count"] == 5
    assert exported["route_count"] == 6
    assert exported["shell_only"] is True
    assert exported["provider_declaration_only"] is True
    assert exported["performs_network_call"] is False
    assert exported["reads_credentials"] is False
    assert exported["modifies_kernel"] is False


def test_l6_27_notes_are_redacted() -> None:
    runtime = RuntimeEntry()
    runtime.run_provider_adaptation(
        notes="api_key=sk-test-secret token=abc password=123 authorization=Bearer xyz",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
    )
    text = json.dumps(runtime.provider_adaptation_snapshot(), ensure_ascii=False)
    assert "sk-test-secret" not in text
    assert "token=abc" not in text
    assert "password=123" not in text
    assert "Bearer xyz" not in text


def test_l6_27_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = [
        "provider_adaptation_shell",
        "build_provider_adaptation",
        "ProviderAdaptationBridge",
        "/provider-build",
    ]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
