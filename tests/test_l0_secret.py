from dataclasses import FrozenInstanceError
import pytest
from tiangong_kernel.l0_primitives.identity import RefId
from tiangong_kernel.l0_primitives.serialization import stable_json_dumps, stable_hash

def rid(prefix: str = "ref") -> RefId:
    return RefId(f"{prefix}:" + "7" * 32)

def assert_frozen(obj):
    with pytest.raises(FrozenInstanceError):
        obj.schema_version = "x"

def assert_stable(obj):
    assert stable_json_dumps(obj) == stable_json_dumps(obj)
    assert stable_hash(obj) == stable_hash(obj)

from tiangong_kernel.l0_primitives.secret import SecretRef, SecretKind, SecretState, CredentialRef, CredentialKind, CredentialState, CapabilityTokenRef, TokenKind, TokenState, CredentialScopeRef, CredentialBindingRef, RevocationRef

def test_secret_objects_construct_freeze_serialize_hash_and_enum_values():
    secret = SecretRef(rid(), SecretKind.API_KEY, SecretState.ACTIVE)
    credential = CredentialRef(rid(), CredentialKind.USER_CREDENTIAL, CredentialState.BOUND, secret)
    scope = CredentialScopeRef(rid())
    token = CapabilityTokenRef(rid(), TokenKind.LEASE_BOUND_TOKEN, TokenState.ISSUED, scope)
    binding = CredentialBindingRef(rid(), credential)
    revocation = RevocationRef(rid())
    assert SecretKind.PRIVATE_KEY.value == "private_key"
    assert CredentialKind.SERVICE_ACCOUNT.value == "service_account"
    assert TokenKind.UNKNOWN.value == "unknown"
    for obj in (secret, credential, scope, token, binding, revocation):
        assert_frozen(obj); assert_stable(obj)
