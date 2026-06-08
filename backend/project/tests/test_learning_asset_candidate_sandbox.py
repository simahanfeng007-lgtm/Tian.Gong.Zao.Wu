from __future__ import annotations

import json
from pathlib import Path

from tiangong_agent_runtime.runtime_entry import RuntimeEntry
from tiangong_agent_runtime.tool_invocation import ToolInvocation


def test_learning_asset_candidate_sandbox_drill_builds_reviewable_packages(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    names = set(runtime.registry.names())
    assert "learning_asset_candidate_sandbox_guide" in names
    assert "learning_asset_candidate_sandbox_build" in names
    assert "learning_asset_candidate_sandbox_validate" in names
    assert "learning_asset_candidate_sandbox_review" in names

    result = runtime.run_text("asset-candidate-sandbox drill pytest missing tests", workspace=tmp_path, max_steps=15)
    assert [step.tool_name for step in result.plan] == [
        "learning_asset_candidate_sandbox_guide",
        "synthesize_experience_candidates",
        "queue_skill_candidates",
        "queue_tool_production_requests",
        "learning_asset_contract_normalize",
        "learning_asset_contract_validate",
        "learning_asset_sandbox_align",
        "learning_asset_sandbox_validate",
        "learning_asset_candidate_sandbox_build",
        "learning_asset_candidate_sandbox_validate",
        "learning_asset_candidate_sandbox_review",
    ]
    assert all(item.ok for item in result.results)
    build = result.results[-3].data
    validate = result.results[-2].data
    review = result.results[-1].data
    assert build["status"] == "pass"
    assert validate["status"] == "pass"
    assert review["status"] == "review_ready"
    assert build["package_count"] >= 2
    assert build["tool_package_count"] >= 1
    assert build["skill_package_count"] >= 1
    assert build["static_scan_pass"] is True
    assert build["smoke_pass"] is True
    for package in build["packages"]:
        package_dir = Path(package["package_dir"])
        assert package_dir.exists()
        assert package_dir.is_relative_to(tmp_path)
        manifest = json.loads(Path(package["manifest_path"]).read_text(encoding="utf-8"))
        assert manifest["candidate_only"] is True
        assert manifest["no_runtime_tool_registration"] is True
        assert manifest["no_skill_activation"] is True
        assert manifest["no_candidate_tool_invocation"] is True
        assert Path(package["zip_path"]).exists()
        assert Path(package["rollback_evidence_path"]).exists()
        assert Path(package["registration_review_path"]).exists()


def test_learning_asset_candidate_sandbox_registry_alignment(tmp_path: Path) -> None:
    runtime = RuntimeEntry()
    result = runtime.execute_plan(
        [
            ToolInvocation("runtime_tool_alignment_check", {"include_cards": True}),
            ToolInvocation("runtime_llm_operational_drill", {}),
        ],
        workspace=tmp_path,
        user_message="r18 candidate sandbox alignment",
        max_steps=5,
    )
    assert all(item.ok for item in result.results)
    report = result.results[0].data
    assert report["tool_count"] == len(runtime.registry.names())
    assert report["usage_card_count"] == report["tool_count"]
    assert report["all_tools_have_usage_cards"] is True
    assert report["all_registered_tools_classifier_allowed"] is True
    assert "skill.learning_asset_candidate_sandbox_workflow" in report["skill_sources"]
    cards = {card["tool"]: card for card in report["tool_usage_cards"]}
    assert cards["learning_asset_candidate_sandbox_build"]["family"] == "learning_asset_candidate_sandbox"
    drill = result.results[1].data
    assert drill["missing_tool_routes"] == []
    assert drill["empty_routes"] == []
