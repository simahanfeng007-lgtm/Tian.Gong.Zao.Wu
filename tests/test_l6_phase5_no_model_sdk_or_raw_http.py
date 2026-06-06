import pytest

from tiangong_kernel.l6_plugins.governance_control import *

def test_no_model_sdk_or_raw_http_scan():
    report = scan_l6_phase5_text('test:l6_phase5_bad_model', 'import openai\nrequests.get')
    assert report.passed is False
    assert report.p0_count >= 1
    clean = scan_l6_phase5_text('test:l6_phase5_clean_model', 'summary only model requirement ref')
    assert clean.passed is True
