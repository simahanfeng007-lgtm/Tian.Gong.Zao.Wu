import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_forbidden_scan_blocks_model_sdk_and_http_patterns():
    clean = scan_l6_phase3_mind_text("mind:clean", "model requirement only and projection summary")
    assert clean.passed is True
    dirty = scan_l6_phase3_mind_text("mind:dirty", "import openai\nrequests.get('x')\nbase_url='x'\napi_key='x'")
    assert dirty.passed is False
    assert dirty.p0_count >= 3
