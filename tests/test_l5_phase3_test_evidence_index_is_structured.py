from tiangong_kernel.l5_plugin_host import L5Phase3TestEvidenceIndex, L5Phase3TestEvidenceRecord


def test_phase3_test_evidence_records_are_structured():
    record = L5Phase3TestEvidenceRecord(
        command="python -m pytest -q tests",
        purpose="full regression",
        runtime_summary="not run in unit sample",
        status="passed",
        evidence_ref="evidence:test",
        output_summary="sample passed",
        related_tests=("tests/test_l5_phase3_registry_quality_gate.py",),
        related_requirements=("full_pytest",),
        real_execution_result=True,
    )
    index = L5Phase3TestEvidenceIndex(index_ref="test_evidence:l5_phase3", records=(record,), evidence_refs=("evidence:test",))
    assert index.records[0].command.startswith("python")
