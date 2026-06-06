"""L1 副作用授权引用协议端口。

本模块只描述副作用授权与策略引用请求形状，不做授权、风险裁决或策略裁决。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from tiangong_kernel.l0_primitives.identity import TypedRef

from .port_result import PortResult


EFFECT_AUTHORIZATION_PORT_SCHEMA_VERSION = "0.1"


@dataclass(frozen=True, slots=True)
class EffectAuthorizationRequest:
    """副作用授权请求协议对象。"""

    request_ref: TypedRef | None = None
    effect_ref: TypedRef | None = None
    side_effect_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    boundary_bundle_ref: TypedRef | None = None
    request_only: bool = True
    schema_version: str = EFFECT_AUTHORIZATION_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.request_only is not True:
            raise ValueError("EffectAuthorizationRequest.request_only must remain true")
        if not self.schema_version:
            raise ValueError("EffectAuthorizationRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EffectAuthorizationResponse:
    """副作用授权响应协议对象，只保存授权引用。"""

    response_ref: TypedRef | None = None
    authorization_ref: TypedRef | None = None
    denial_ref: TypedRef | None = None
    response_only: bool = True
    grants_permission: bool = False
    schema_version: str = EFFECT_AUTHORIZATION_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.response_only is not True:
            raise ValueError("EffectAuthorizationResponse.response_only must remain true")
        if self.grants_permission:
            raise ValueError("EffectAuthorizationResponse cannot grant permission")
        if not self.schema_version:
            raise ValueError("EffectAuthorizationResponse.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EffectPolicyReferenceRequest:
    """副作用策略引用请求协议对象。"""

    request_ref: TypedRef | None = None
    effect_ref: TypedRef | None = None
    policy_candidate_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    request_only: bool = True
    schema_version: str = EFFECT_AUTHORIZATION_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.request_only is not True:
            raise ValueError("EffectPolicyReferenceRequest.request_only must remain true")
        if not self.schema_version:
            raise ValueError("EffectPolicyReferenceRequest.schema_version cannot be empty")


@dataclass(frozen=True, slots=True)
class EffectPolicyReferenceResponse:
    """副作用策略引用响应协议对象。"""

    response_ref: TypedRef | None = None
    policy_reference_refs: tuple[TypedRef, ...] = field(default_factory=tuple)
    response_only: bool = True
    policy_decision_made: bool = False
    schema_version: str = EFFECT_AUTHORIZATION_PORT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.response_only is not True:
            raise ValueError("EffectPolicyReferenceResponse.response_only must remain true")
        if self.policy_decision_made:
            raise ValueError("EffectPolicyReferenceResponse cannot decide policy")
        if not self.schema_version:
            raise ValueError("EffectPolicyReferenceResponse.schema_version cannot be empty")


class EffectAuthorizationPort(ABC):
    """副作用授权端口协议，只定义请求/响应形状。"""

    @abstractmethod
    def request_effect_authorization(
        self, request: EffectAuthorizationRequest
    ) -> PortResult[EffectAuthorizationResponse]:
        """请求未来副作用授权引用。"""


class EffectPolicyReferencePort(ABC):
    """副作用策略引用端口协议。"""

    @abstractmethod
    def request_effect_policy_reference(
        self, request: EffectPolicyReferenceRequest
    ) -> PortResult[EffectPolicyReferenceResponse]:
        """请求未来策略引用。"""
