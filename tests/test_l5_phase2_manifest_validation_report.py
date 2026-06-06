from tiangong_kernel.l5_plugin_host import PluginManifestValidationIssue, PluginManifestValidationReport


def test_validation_issue_requires_p0_p1_to_be_blocking():
    issue = PluginManifestValidationIssue(
        issue_code="MISSING_PLUGIN_ID",
        severity="P1",
        field_path="plugin_id",
        message="plugin_id is required",
        blocking=True,
        evidence_ref="evidence:missing_plugin_id",
    )
    report = PluginManifestValidationReport(report_ref="report:one", manifest_ref="manifest:one", issues=(issue,))
    assert not report.passed
    assert report.p1_count == 1
