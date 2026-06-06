from tiangong_kernel.l6_plugins.final_closure import L6ZipIntegrityReport

def test_zip_integrity_report_required():
    assert L6ZipIntegrityReport().object_ref == 'report:l6_phase8_zip_integrity'
