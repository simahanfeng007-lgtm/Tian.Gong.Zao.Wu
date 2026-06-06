import pytest

from tiangong_kernel.l6_plugins.mind import *


def test_pollution_defense_is_not_value_dictatorship():
    risk = PollutionRiskProjection(pollution_risk_score=0.7, quarantine_suggested=True)
    assert risk.value_dictatorship is False
    assert risk.bans_user is False
    assert PollutionRiskScoreModel(toxic_content_exposure=0.9).pollution_risk_score > 0
    with pytest.raises(ValueError):
        PollutionRiskProjection(value_dictatorship=True)
    with pytest.raises(ValueError):
        PollutionRiskScoreModel(value_dictatorship=True)
