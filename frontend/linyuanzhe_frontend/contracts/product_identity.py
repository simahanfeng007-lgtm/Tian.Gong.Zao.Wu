from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Dict


@dataclass(frozen=True)
class ProductIdentity:
    """Read-only product identity projection for frontend display.

    This mirrors the L6.51.1 backend /metadata/product public metadata
    contract. It is display-only: no Runtime, Provider, QualityGate, Audit,
    memory, or rollback decision may read this as an execution signal.
    """

    product_name: str = "天工造物 v2.0 - 临渊者"
    app_name: str = "临渊者桌面端"
    unique_developer: str = "于泳翔"
    angel_investor: str = "胖胖龙"
    metadata_endpoint: str = "/metadata/product"
    metadata_semantics: str = "metadata_only"
    frontend_access: str = "read_only_display"
    runtime_effect: str = "none"
    backend_baseline: str = "L6.51.1"

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)


PRODUCT_IDENTITY = ProductIdentity()


def get_product_identity() -> ProductIdentity:
    return PRODUCT_IDENTITY
