from pathlib import Path

import pytest

from tiangong_kernel.l0_primitives.serialization import stable_json_dumps
from tiangong_kernel.l2_state import (
    CredentialStatus,
    PrivacyCredentialState,
    PrivacyStatus,
    SecurityStatus,
)
from tests.test_l2_phase4_serialization import build_phase4_objects, identity, status, typed


SECURITY_FILE = Path(__file__).resolve().parents[1] / "tiangong_kernel" / "l2_state" / "security_state.py"


def test_l2_phase4_security_boundary_records_security_privacy_and_credential_refs():
    objects = build_phase4_objects()
    security = objects["security"]

    assert security.security_status is SecurityStatus.WARNING_RECORDED
    assert security.subject_ref == objects["phase3"]["effect_observation"].identity.state_ref
    assert security.privacy_state_refs == (objects["privacy"].identity.state_ref,)
    assert security.credential_state_refs == (objects["secret"].identity.state_ref,)
    assert security.boundary_check_refs == (objects["boundary_check"].identity.state_ref,)


def test_l2_phase4_privacy_and_secret_states_default_to_redacted_absent_values():
    objects = build_phase4_objects()
    privacy = objects["privacy"]
    secret = objects["secret"]

    assert privacy.privacy_status is PrivacyStatus.SENSITIVE_DATA_REF_ONLY
    assert privacy.credential_status is CredentialStatus.REF_ONLY
    assert privacy.redacted is True
    assert privacy.value_absent is True
    assert secret.redacted is True
    assert secret.value_absent is True


def test_l2_phase4_privacy_credential_state_rejects_unredacted_values():
    with pytest.raises(ValueError):
        PrivacyCredentialState(
            identity=identity(800),
            status=status(),
            privacy_ref=typed(801, "privacy"),
            credential_ref=typed(802, "credential"),
            redacted=False,
        )


def test_l2_phase4_security_serialization_and_source_exclude_forbidden_secret_fields():
    payload = stable_json_dumps(build_phase4_objects()["secret"])
    source = SECURITY_FILE.read_text(encoding="utf-8")
    forbidden_names = {
        "secret_value",
        "credential_value",
        "token_value",
        "password",
        "api_key",
        "cookie_value",
        "raw_secret",
        "raw_token",
        "raw_credential",
    }
    assert all(name not in source for name in forbidden_names)
    assert all(name not in payload for name in forbidden_names)
