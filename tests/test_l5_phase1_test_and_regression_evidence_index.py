import pytest

from tiangong_kernel.l5_plugin_host import (
    L5Phase1RegressionBaselineRecord,
    L5Phase1RegressionEvidenceIndex,
    L5Phase1TestEvidenceIndex,
    L5Phase1TestEvidenceRecord,
)


def test_passed_test_evidence_requires_command_return_code_and_summary():
    record = L5Phase1TestEvidenceRecord(
        record_ref="test_evidence:compileall",
        command="python -m compileall -q tiangong_kernel tests",
        scope="compileall",
        expected_purpose="语法与导入检查",
        observed_summary="passed",
        return_code=0,
        status="passed",
        report_ref="docs/l5_phase1_test_results_zh.txt",
        evidence_ref="evidence:compileall",
    )
    index = L5Phase1TestEvidenceIndex(index_ref="test_evidence_index:phase1", records=(record,))
    assert index.records[0].status == "passed"


def test_passed_test_evidence_rejects_missing_summary_or_nonzero_return_code():
    with pytest.raises(ValueError):
        L5Phase1TestEvidenceRecord(
            record_ref="test_evidence:bad",
            command="python -m pytest -q tests",
            scope="full",
            expected_purpose="回归",
            observed_summary="",
            return_code=0,
            status="passed",
            report_ref="docs/l5_phase1_test_results_zh.txt",
            evidence_ref="evidence:bad",
        )
    with pytest.raises(ValueError):
        L5Phase1TestEvidenceRecord(
            record_ref="test_evidence:bad_rc",
            command="python -m pytest -q tests",
            scope="full",
            expected_purpose="回归",
            observed_summary="failed",
            return_code=1,
            status="passed",
            report_ref="docs/l5_phase1_test_results_zh.txt",
            evidence_ref="evidence:bad_rc",
        )


def test_regression_evidence_records_pre_and_post_l5_summaries():
    record = L5Phase1RegressionBaselineRecord(
        baseline_ref="regression:phase1",
        pre_l5_baseline_summary="929 passed before L5 phase 1",
        post_l5_full_test_summary="not yet recorded",
        delta_explanation="新增 L5 测试后应重新统计。",
        changed_test_files=("tests/test_l5_phase1_test_and_regression_evidence_index.py",),
        warning_summary="none",
        regression_status="not_run",
    )
    index = L5Phase1RegressionEvidenceIndex(index_ref="regression_index:phase1", records=(record,), evidence_refs=("evidence:regression",))
    assert index.records[0].pre_l5_baseline_summary.startswith("929 passed")
