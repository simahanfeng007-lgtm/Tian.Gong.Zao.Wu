import pytest

from tiangong_kernel.l6_plugins.cognitive_continuity import *


def test_forbidden_scan_blocks_public_leakage():
    dirty_text = "\n".join(["full_affective_profile=True", "raw_prompt=\'x\'", "complete_evidence_chain=\'x\'", "execution_plan=\'x\'"])
    dirty = scan_l6_phase4_text("l6:dirty_public", dirty_text)
    assert dirty.passed is False
    assert dirty.p0_count >= 4
