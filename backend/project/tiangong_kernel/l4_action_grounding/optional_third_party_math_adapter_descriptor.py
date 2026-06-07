"""Optional third-party math adapter descriptors.

This module only names optional future dependency families.  It intentionally
does not import any of them and does not provide an executable adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .math_adapter_descriptor import MathAdapterDescriptor, build_math_adapter_descriptor


@dataclass(frozen=True, slots=True)
class OptionalThirdPartyMathAdapterDescriptor:
    """Descriptor-only reservation for future third-party math libraries."""

    descriptor: MathAdapterDescriptor = field(
        default_factory=lambda: build_math_adapter_descriptor(
            adapter_id="disabled.optional_third_party_math_adapter",
            adapter_kind="optional_third_party_math_adapter_descriptor",
            adapter_name="Disabled Optional Third Party Math Adapter Descriptor",
            supported_model_domains=("statistics", "local_model_scoring", "custom_formula"),
            optional_dependency_names=("numpy", "scipy", "sklearn"),
        )
    )
    descriptor_only: bool = True
    no_imports_performed: bool = True
    disabled_by_default: bool = True
    requires_l5_permit: bool = True
