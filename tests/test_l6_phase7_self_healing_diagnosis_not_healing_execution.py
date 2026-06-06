import pytest
from tiangong_kernel.l6_plugins.adaptive_collaboration import SelfHealingDiagnosisCandidate

def test_self_healing_diagnosis_not_healing_execution():
    item = SelfHealingDiagnosisCandidate()
    assert item.executes_healing is False
    with pytest.raises(ValueError):
        SelfHealingDiagnosisCandidate(executes_healing=True)
