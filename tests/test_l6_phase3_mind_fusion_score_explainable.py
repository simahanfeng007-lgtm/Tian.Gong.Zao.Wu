import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_mind_fusion_score_has_explainable_digest_and_scores():
    model = MindFusionScoreModel(belief_confidence_score=0.8, pollution_risk_score=0.1)
    assert 0 <= model.weighted_score <= 1
    assert 0 <= model.conflict_resolution_score <= 1
    assert 0 <= model.uncertainty_score <= 1
    assert model.digest
    assert ExplanationDigest().digest
