"""L4 第二阶段未来 L5 端口占位协议。"""

from __future__ import annotations

from typing import Protocol

from .gate_input import ActionGroundingGateInput
from .gate_result import ActionGroundingGateResult


class L5PermitValidatorPort(Protocol):
    """未来 L5 permit validator 占位；L4 第二阶段不提供实现。"""

    def validate_permit_ref(self, gate_input: ActionGroundingGateInput) -> ActionGroundingGateResult:
        """返回未来 L5 校验结果；本包不实现该方法。"""
        ...


class L5CredentialResolverPort(Protocol):
    """未来 L5 credential resolver 占位；不得在 L4 读取真实凭据。"""

    def resolve_credential_handle_ref(self, gate_input: ActionGroundingGateInput) -> object:
        """返回未来凭据句柄解析结果；本包不实现该方法。"""
        ...


class L5AuditSinkPort(Protocol):
    """未来 L5 audit sink 占位；不得在 L4 写审计存储。"""

    def report_audit_requirement_ref(self, gate_result: ActionGroundingGateResult) -> object:
        """返回未来审计需求回执；本包不实现该方法。"""
        ...


class L5ResourceBudgetPort(Protocol):
    """未来 L5 resource budget 占位；不得在 L4 创建或消费额度。"""

    def check_resource_limit_ref(self, gate_input: ActionGroundingGateInput) -> object:
        """返回未来资源限制检查结果；本包不实现该方法。"""
        ...


class L5BoundaryRecheckPort(Protocol):
    """未来 L5 boundary recheck 占位；不得在 L4 重新裁决边界。"""

    def recheck_boundary_ref(self, gate_input: ActionGroundingGateInput) -> object:
        """返回未来边界复检结果；本包不实现该方法。"""
        ...


class L5PermitConsumptionReporterPort(Protocol):
    """未来 L5 permit consumption reporter 占位；不得在 L4 消费真实资源。"""

    def report_permit_consumption_ref(self, gate_result: ActionGroundingGateResult) -> object:
        """返回未来消费摘要回执；本包不实现该方法。"""
        ...


class L5BoundaryFeedbackPort(Protocol):
    """未来 L5 boundary feedback 占位；L4 只传递反馈引用。"""

    def report_boundary_feedback(self, gate_result: ActionGroundingGateResult) -> object:
        """返回未来边界反馈回执；本包不实现该方法。"""
        ...
