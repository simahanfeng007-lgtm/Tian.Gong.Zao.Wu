import json
from pathlib import Path


def test_l5_impact_report_matches_replayed_zip_to_zip_hash_compare():
    compare = json.loads(Path("docs/hash_compare_五模型专项_20260605.json").read_text(encoding="utf-8"))
    impact = Path("docs/L5_影响评估_五模型专项_20260605.md").read_text(encoding="utf-8")

    assert compare["compare_kind"] == "zip-to-zip replay for P2-001 baseline correction"
    assert compare["baseline"] == "天工造物_L5全阶段_hotfix2_五大模型高适配专项修复包_20260605.zip"
    assert compare["current"] == "天工造物_L5全阶段_hotfix3_五大模型高适配专项修复包_20260605.zip"
    assert compare["l5_added"] == []
    assert compare["l5_modified"] == []
    assert compare["l5_removed"] == []

    assert "L5 源码 0 added / 0 modified / 0 removed" in impact
    assert compare["baseline_sha256"] in impact
    assert compare["current_sha256"] in impact


def test_l5_impact_report_discloses_final_schema_version_only_delta():
    final_delta = json.loads(Path("docs/hash_compare_hotfix3_to_p2p3_final_20260605.json").read_text(encoding="utf-8"))
    impact = Path("docs/L5_影响评估_五模型专项_20260605.md").read_text(encoding="utf-8")

    assert final_delta["compare_kind"] == "zip-to-dir final P2/P3 patch delta"
    assert final_delta["l5_added"] == []
    assert final_delta["l5_removed"] == []
    assert final_delta["l5_modified"] == ["tiangong_kernel/l5_plugin_host/model_capability_invariants.py"]
    assert "仅为 schema version 元数据修正" in impact
