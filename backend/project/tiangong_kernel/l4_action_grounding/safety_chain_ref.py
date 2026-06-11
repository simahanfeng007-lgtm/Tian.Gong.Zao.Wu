"""L4 side-effect safety chain references."""

from __future__ import annotations

from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .identity import L4_ACTION_GROUNDING_SCHEMA_VERSION, ensure_false, ensure_schema_version, ensure_short_text, ensure_true


@dataclass(frozen=True, slots=True)
class L3SafetyChainRef:
    """L3 安全链引用，不代表 L4 授权。"""

    safety_chain_ref: TypedRef
    source_action_intent_ref: TypedRef | None = None
    boundary_bundle_ref: TypedRef | None = None
    audit_requirement_ref: TypedRef | None = None
    lease_or_denial_ref: TypedRef | None = None
    secret_privacy_guard_ref: TypedRef | None = None
    transaction_compensation_ref: TypedRef | None = None
    ref_only: bool = True
    l4_authorized_action: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_true(self.ref_only, "L3SafetyChainRef.ref_only")
        ensure_false(self.l4_authorized_action, "L3SafetyChainRef.l4_authorized_action")
        ensure_schema_version(self.schema_version, "L3SafetyChainRef.schema_version")


@dataclass(frozen=True, slots=True)
class SideEffectSafetyPreconditionRef:
    """副作用安全前置条件引用。"""

    precondition_ref: TypedRef
    safety_chain_ref: TypedRef | None = None
    requirement_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    missing_requirement_codes: tuple[str, ...] = field(default_factory=tuple)
    ref_only: bool = True
    validation_only: bool = True
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.missing_requirement_codes:
            ensure_short_text(item, "SideEffectSafetyPreconditionRef.missing_requirement_codes", 128)
        ensure_true(self.ref_only, "SideEffectSafetyPreconditionRef.ref_only")
        ensure_true(self.validation_only, "SideEffectSafetyPreconditionRef.validation_only")
        ensure_schema_version(self.schema_version, "SideEffectSafetyPreconditionRef.schema_version")


@dataclass(frozen=True, slots=True)
class SafetyChainValidationResult:
    """安全链结构校验结果，不授权动作。"""

    validation_ref: TypedRef
    safety_chain_ref: TypedRef | None = None
    missing_requirement_codes: tuple[str, ...] = field(default_factory=tuple)
    accepted_structure: bool = False
    validation_only: bool = True
    l4_authorized_action: bool = False
    real_action_performed: bool = False
    schema_version: str = L4_ACTION_GROUNDING_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for item in self.missing_requirement_codes:
            ensure_short_text(item, "SafetyChainValidationResult.missing_requirement_codes", 128)
        ensure_true(self.validation_only, "SafetyChainValidationResult.validation_only")
        ensure_false(self.l4_authorized_action, "SafetyChainValidationResult.l4_authorized_action")
        ensure_false(self.real_action_performed, "SafetyChainValidationResult.real_action_performed")
        ensure_schema_version(self.schema_version, "SafetyChainValidationResult.schema_version")
