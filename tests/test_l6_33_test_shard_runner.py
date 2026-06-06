from __future__ import annotations

import json
import sys
from pathlib import Path

from tiangong_agent_runtime.test_shard_runner import (
    L6_33_SHARD_SCHEMA,
    TestShardSpec,
    build_pytest_shard,
    collect_existing_shard_results,
    run_test_shards,
)


ROOT = Path(__file__).resolve().parents[1]


def test_l6_33_shard_runner_passes_and_writes_reports(tmp_path: Path) -> None:
    summary = run_test_shards(
        [
            TestShardSpec(
                name="pass_smoke",
                command=[sys.executable, "-c", "print('l6_33_ok')"],
                cwd=ROOT,
                timeout_seconds=10,
                purpose="smoke pass",
            )
        ],
        output_dir=tmp_path / "shards",
    )
    assert summary.schema == L6_33_SHARD_SCHEMA
    assert summary.status == "passed"
    assert summary.total_shards == 1
    assert summary.passed_shards == 1
    assert summary.timeout_shards == 0
    assert summary.results[0].stdout_tail.strip() == "l6_33_ok"
    assert (tmp_path / "shards" / "shard_summary.json").exists()
    assert (tmp_path / "shards" / "shard_report.txt").exists()
    loaded = json.loads((tmp_path / "shards" / "shard_summary.json").read_text(encoding="utf-8"))
    assert loaded["schema"] == L6_33_SHARD_SCHEMA
    assert loaded["results"][0]["rerun_command"]


def test_l6_33_timeout_is_reaped_and_not_reported_as_passed(tmp_path: Path) -> None:
    summary = run_test_shards(
        [
            TestShardSpec(
                name="timeout_smoke",
                command=[sys.executable, "-c", "import time; time.sleep(5)"],
                cwd=ROOT,
                timeout_seconds=0.2,
                purpose="forced timeout",
            )
        ],
        output_dir=tmp_path / "timeout",
    )
    assert summary.status == "timeout"
    assert summary.timeout_shards == 1
    assert summary.required_failed_or_timeout == 1
    result = summary.results[0]
    assert result.status == "timeout"
    assert result.timed_out is True
    assert result.process_group_reaped is True
    assert "timeout after" in result.error_message
    assert result.status != "passed"


def test_l6_33_failed_optional_shard_is_partial_not_required_failure(tmp_path: Path) -> None:
    summary = run_test_shards(
        [
            TestShardSpec(
                name="optional_failure",
                command=[sys.executable, "-c", "raise SystemExit(3)"],
                cwd=ROOT,
                timeout_seconds=10,
                required=False,
                purpose="optional diagnostic shard",
            )
        ],
        output_dir=tmp_path / "optional",
    )
    assert summary.status == "partial"
    assert summary.skipped_shards == 1
    assert summary.required_failed_or_timeout == 0
    assert summary.results[0].returncode == 3


def test_l6_33_build_pytest_shard_uses_argv_not_shell_string() -> None:
    shard = build_pytest_shard(
        "pytest_l6_33_self",
        ["tests/test_l6_33_test_shard_runner.py::test_l6_33_build_pytest_shard_uses_argv_not_shell_string"],
        cwd=ROOT,
        timeout_seconds=30,
        extra_args=["-q"],
    )
    assert shard.command[:3] == [sys.executable, "-m", "pytest"]
    assert isinstance(shard.command, list)
    assert "pytest_l6_33_self" in shard.public_dict()["name"]
    assert shard.public_dict()["rerun_command"]


def test_l6_33_summary_preserves_boundary_flags(tmp_path: Path) -> None:
    summary = run_test_shards(
        [TestShardSpec(name="boundary", command=[sys.executable, "-c", "pass"], cwd=ROOT, timeout_seconds=10)],
        output_dir=tmp_path / "boundary",
    )
    payload = summary.public_dict()
    assert payload["timeout_reaper_enabled"] is True
    assert payload["shard_isolation_enabled"] is True
    assert payload["no_kernel_mutation"] is True
    assert payload["no_secret_read"] is True
    assert payload["no_network_call"] is True
    assert payload["no_shell_string_execution"] is True


def test_l6_33_can_rebuild_summary_from_existing_results(tmp_path: Path) -> None:
    output_dir = tmp_path / "recoverable"
    original = run_test_shards(
        [TestShardSpec(name="recover", command=[sys.executable, "-c", "print('recoverable')"], cwd=ROOT, timeout_seconds=10)],
        output_dir=output_dir,
    )
    (output_dir / "shard_summary.json").unlink()
    rebuilt = collect_existing_shard_results(output_dir)
    assert rebuilt.status == original.status == "passed"
    assert rebuilt.total_shards == 1
    assert rebuilt.results[0].stdout_tail.strip() == "recoverable"
    assert (output_dir / "shard_summary.json").exists()
    assert (output_dir / "shard_report.txt").exists()
