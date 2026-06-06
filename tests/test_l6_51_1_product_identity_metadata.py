from __future__ import annotations

import inspect
import json

from tiangong_agent_runtime import __version__, build_product_identity_public
from tiangong_agent_runtime.frontend_contract import build_frontend_backend_contract, validate_frontend_contract
from tiangong_agent_runtime.product_identity import (
    ANGEL_INVESTOR_NAME,
    PRODUCT_IDENTITY_ENDPOINT,
    PRODUCT_IDENTITY_SCHEMA,
    PRODUCT_NAME,
    UNIQUE_DEVELOPER_NAME,
    ProductIdentity,
)


def test_l6_51_1_product_identity_is_public_readonly_metadata() -> None:
    identity = ProductIdentity()
    assert identity.schema == PRODUCT_IDENTITY_SCHEMA
    assert identity.product_name == PRODUCT_NAME == "天工造物 / 临渊者"
    assert identity.unique_developer == UNIQUE_DEVELOPER_NAME == "于泳翔"
    assert identity.angel_investor == ANGEL_INVESTOR_NAME == "胖胖龙"
    assert identity.endpoint == PRODUCT_IDENTITY_ENDPOINT == "/metadata/product"
    assert identity.public is True
    assert identity.runtime_semantics == "metadata_only"
    assert identity.frontend_permission == "read_only_display"


def test_l6_51_1_product_identity_projection_has_no_execution_or_secret_fields() -> None:
    public = build_product_identity_public()
    raw = json.dumps(public, ensure_ascii=False)
    assert public["unique_developer"] == "于泳翔"
    assert public["angel_investor"] == "胖胖龙"
    assert "api_key" not in raw.lower()
    assert "bearer" not in raw.lower()
    assert "token" not in raw.lower()
    assert "endpoint" in public  # metadata endpoint only, not provider endpoint
    assert public["runtime_semantics"] == "metadata_only"


def test_l6_51_1_frontend_contract_exposes_identity_without_expanding_permissions() -> None:
    contract = build_frontend_backend_contract()
    identity = contract["product_identity"]
    assert contract["product_metadata_endpoint"] == PRODUCT_IDENTITY_ENDPOINT
    assert identity["unique_developer"] == "于泳翔"
    assert identity["angel_investor"] == "胖胖龙"
    assert identity["frontend_permission"] == "read_only_display"
    assert contract["l6_51_1_product_identity_freeze"]["runtime_semantics"] == "metadata_only"
    assert "direct_provider_sdk_call" in contract["forbidden_frontend_actions"]
    assert "direct_tool_adapter_call" in contract["forbidden_frontend_actions"]
    assert validate_frontend_contract().ok is True


def test_l6_51_1_runtime_package_exports_identity_projection_only() -> None:
    assert __version__ == "2.0.0"
    public = build_product_identity_public()
    assert public["unique_developer"] == "于泳翔"
    source = inspect.getsource(build_product_identity_public)
    forbidden_runtime_verbs = ("open(", "requests", "subprocess", "RuntimeEntry", "ModelPlanner")
    assert not any(verb in source for verb in forbidden_runtime_verbs)
