"""L6.51.1 后端产品身份元数据。

该模块只导出公开、只读的产品署名元数据，不参与 Runtime 执行、
Provider 调用、工具调度、记忆写入、审计写入或回滚决策。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

PRODUCT_IDENTITY_SCHEMA = "tiangong.l6_51_1.product_identity.v1"
PRODUCT_NAME = "天工造物 / 临渊者"
UNIQUE_DEVELOPER_NAME = "于泳翔"
ANGEL_INVESTOR_NAME = "胖胖龙"
PRODUCT_IDENTITY_ENDPOINT = "/metadata/product"


@dataclass(frozen=True)
class ProductIdentity:
    """前端与文档可读取的公开产品身份信息。"""

    schema: str = PRODUCT_IDENTITY_SCHEMA
    product_name: str = PRODUCT_NAME
    unique_developer: str = UNIQUE_DEVELOPER_NAME
    angel_investor: str = ANGEL_INVESTOR_NAME
    endpoint: str = PRODUCT_IDENTITY_ENDPOINT
    public: bool = True
    runtime_semantics: str = "metadata_only"
    frontend_permission: str = "read_only_display"

    def public_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_product_identity_public() -> dict[str, Any]:
    """返回可公开展示的产品身份投影。"""
    return ProductIdentity().public_dict()
