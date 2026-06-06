from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

from tiangong_agent_runtime.delivery_manifest import DeliveryManifestBridge, evaluate_release_gate
from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation
from tiangong_agent_runtime.tool_result import ToolResultStatus
from tiangong_agent_shell.tool_bridge import ToolExecutionMode

ROOT = Path(__file__).resolve().parents[1]


def _seed_project(root: Path, *, with_pyproject: bool = True) -> None:
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (root / "demo.py").write_text("def add(a, b):\n    return a + b\n", encoding="utf-8")
    (root / "test_demo.py").write_text("from demo import add\n\ndef test_add():\n    assert add(1, 2) == 3\n", encoding="utf-8")
    if with_pyproject:
        (root / "pyproject.toml").write_text("[project]\nname='demo'\nversion='0.0.1'\n", encoding="utf-8")


def test_l6_19_delivery_manifest_empty_state() -> None:
    bridge = DeliveryManifestBridge()
    assert bridge.public_dict()["schema"] == "tiangong.l6_19.delivery_manifest.v1"
    assert bridge.public_dict()["status"] == "empty"


def test_l6_19_release_gate_blocks_without_quality_gate() -> None:
    gate = evaluate_release_gate({"status": "empty"}, [])
    assert gate.decision == "blocked"
    assert gate.allow_release is False


def test_l6_19_runtime_release_pass_creates_bundle_manifest_and_sha(tmp_path: Path) -> None:
    _seed_project(tmp_path, with_pyproject=True)
    runtime = RuntimeEntry()
    result = runtime.run_release(
        workspace=tmp_path,
        path=".",
        target="dist/pass_release.zip",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        require_pytest=True,
    )
    manifest = runtime.delivery_snapshot()
    assert manifest["schema"] == "tiangong.l6_19.delivery_manifest.v1"
    assert manifest["quality_gate"]["decision"] == "pass"
    assert manifest["release_gate"]["decision"] == "pass"
    assert manifest["release_gate"]["allow_release"] is True
    assert manifest["bundle_sha256_finalized"] is True
    assert (tmp_path / "dist" / "pass_release.zip").exists()
    assert (tmp_path / "dist" / "pass_release.zip.sha256").exists()
    assert (tmp_path / "dist" / "pass_release.zip.manifest.json").exists()
    assert any(item.endswith("pass_release.zip") for item in result.projection.artifacts)
    with zipfile.ZipFile(tmp_path / "dist" / "pass_release.zip") as zf:
        names = set(zf.namelist())
    assert "RELEASE_MANIFEST.json" in names
    assert "RELEASE_MANIFEST.md" in names
    assert "reports/quality_gate.json" in names
    assert "payload/README.md" in names
    assert "payload/demo.py" in names


def test_l6_19_runtime_release_warn_allows_bundle_but_discloses_warning(tmp_path: Path) -> None:
    _seed_project(tmp_path, with_pyproject=False)
    runtime = RuntimeEntry()
    runtime.run_release(
        workspace=tmp_path,
        path=".",
        target="dist/warn_release.zip",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        require_pytest=True,
    )
    manifest = runtime.delivery_snapshot()
    assert manifest["quality_gate"]["decision"] == "warn"
    assert manifest["release_gate"]["decision"] == "warn"
    assert manifest["release_gate"]["allow_release"] is True
    assert (tmp_path / "dist" / "warn_release.zip").exists()
    assert any(issue["code"].endswith("missing_dependency_manifest") for issue in manifest["quality_gate"]["issues"])


def test_l6_19_runtime_release_blocks_on_failed_quality_gate(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Demo\n", encoding="utf-8")
    (tmp_path / "bad.py").write_text("def broken(:\n", encoding="utf-8")
    runtime = RuntimeEntry()
    result = runtime.run_release(
        workspace=tmp_path,
        path=".",
        target="dist/blocked_release.zip",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        require_pytest=False,
    )
    manifest = runtime.delivery_snapshot()
    assert manifest["quality_gate"]["decision"] == "fail"
    assert manifest["release_gate"]["decision"] == "blocked"
    assert manifest["release_gate"]["allow_release"] is False
    assert not (tmp_path / "dist" / "blocked_release.zip").exists()
    assert (tmp_path / "dist" / "blocked_release.zip.manifest.json").exists()
    assert result.results[-1].status is ToolResultStatus.BLOCKED


def test_l6_19_runtime_release_blocks_secret_scan_even_when_quality_allows(tmp_path: Path) -> None:
    _seed_project(tmp_path, with_pyproject=True)
    (tmp_path / ".env").write_text("PLACEHOLDER=demo-value\n", encoding="utf-8")
    runtime = RuntimeEntry()
    runtime.run_release(
        workspace=tmp_path,
        path=".",
        target="dist/secret_blocked.zip",
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        require_pytest=True,
    )
    manifest = runtime.delivery_snapshot()
    assert manifest["release_gate"]["decision"] == "blocked"
    assert manifest["release_gate"]["allow_release"] is False
    assert not (tmp_path / "dist" / "secret_blocked.zip").exists()
    findings = manifest["secret_scan"]["findings"]
    assert any(item["path"].endswith(".env") for item in findings)


def test_l6_19_direct_release_tool_requires_quality_gate_first(tmp_path: Path) -> None:
    _seed_project(tmp_path, with_pyproject=True)
    runtime = RuntimeEntry()
    result = runtime.execute_plan(
        [ToolInvocation("create_release_bundle", {"source": ".", "target": "dist/direct.zip"})],
        workspace=tmp_path,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=1,
    )
    assert result.results[-1].status is ToolResultStatus.BLOCKED
    assert not (tmp_path / "dist" / "direct.zip").exists()
    assert runtime.delivery_snapshot()["release_gate"]["decision"] == "blocked"


def test_l6_19_cli_release_delivery_and_export(tmp_path: Path) -> None:
    _seed_project(tmp_path, with_pyproject=True)
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
        input="/release dist/cli_release.zip .\n/delivery\n/delivery-save delivery.json\n/exit\n",
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Release Gate" in proc.stdout
    assert "交付 Manifest 已导出" in proc.stdout
    assert (tmp_path / "dist" / "cli_release.zip").exists()
    exported = json.loads((tmp_path / "delivery.json").read_text(encoding="utf-8"))
    assert exported["schema"] == "tiangong.l6_19.delivery_manifest.v1"
    assert exported["release_gate"]["allow_release"] is True


def test_l6_19_runtime_does_not_pollute_kernel_import_direction() -> None:
    kernel_root = ROOT / "tiangong_kernel"
    forbidden = ["delivery_manifest", "create_release_bundle", "ReleaseBundle", "/release"]
    offenders: list[str] = []
    for path in kernel_root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in forbidden:
            if token in text:
                offenders.append(f"{path.relative_to(ROOT)}::{token}")
    assert offenders == []
