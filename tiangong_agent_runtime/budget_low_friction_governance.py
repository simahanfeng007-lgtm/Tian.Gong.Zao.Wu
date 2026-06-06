"""L6.44 预算治理低摩擦改造。

本模块只在 runtime 外壳层生成预算/风险流转提示：
- A0-A3：默认低摩擦进入既有执行链；
- A4：生成低摩擦确认提示，不阻断；
- A5、凭证/隐私明文、不可逆副作用、发布/激活/合入：强边界保留；
- 预算压力只触发降级/续租建议，不直接扣费、不直接阻断 A0-A4。

真实工具调用、Permit 裁决、预算扣减、质量门仍由 L6.37 执行链负责。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from tiangong_kernel.l6_plugins.common._common import ensure_bool

from .execution_policy import ExecutionPolicy, RiskLevel
from .four_path_public_projection import sanitize_text, stable_digest
from .risk_classifier import RiskClassifier
from .tool_invocation import ToolInvocation

L6_44_BUDGET_LOW_FRICTION_SCHEMA = "tiangong.l6_44.budget_low_friction_governance.v1"
SOURCE_VERSION = "L6.44-budget-low-friction-governance"

SENSITIVE_ARG_KEYS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "token",
    "secret",
    "password",
    "credential",
    "credential_value",
    "private_key",
    "raw_memory_body",
    "raw_prompt",
    "full_evidence_body",
    "privacy_body",
}

STRONG_GATE_TOOL_TERMS = (
    "publish",
    "release",
    "activate",
    "register",
    "merge",
    "hot_switch",
    "version_slot",
    "delete",
    "remove",
    "rollback",
    "credential",
    "secret",
)

IRREVERSIBLE_ARG_TERMS = (
    "delete",
    "remove",
    "permanent",
    "irreversible",
    "overwrite_system",
    "production",
    "deploy",
    "publish",
    "activate",
    "merge",
)


@dataclass(frozen=True)
class BudgetPressureSignal:
    """预算压力读数。只读投影，不直接扣预算、不阻断。"""

    signal_id: str
    step_pressure_score: float = 0.0
    timeout_pressure_score: float = 0.0
    failure_pressure_score: float = 0.0
    resource_exhausted: bool = False
    degradation_recommended: bool = False
    lease_renewal_recommended: bool = False
    lease_extension_steps: int = 0
    hint: str = ""
    no_budget_mutation: bool = True
    no_execution_block: bool = True

    def __post_init__(self) -> None:
        for name in ("resource_exhausted", "degradation_recommended", "lease_renewal_recommended", "no_budget_mutation", "no_execution_block"):
            ensure_bool(getattr(self, name), f"BudgetPressureSignal.{name}")
        for name in ("step_pressure_score", "timeout_pressure_score", "failure_pressure_score"):
            value = getattr(self, name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0.0 <= float(value) <= 1.0:
                raise ValueError(f"{name} must be a float in [0, 1] and cannot be bool")
        if self.lease_extension_steps < 0:
            raise ValueError("lease_extension_steps must be non-negative")
        if not (self.no_budget_mutation and self.no_execution_block):
            raise ValueError("BudgetPressureSignal cannot mutate budget or block execution")

    @property
    def pressure_level(self) -> str:
        score = max(self.step_pressure_score, self.timeout_pressure_score, self.failure_pressure_score)
        if self.resource_exhausted:
            return "exhausted_recoverable"
        if score >= 0.80:
            return "high"
        if score >= 0.55:
            return "medium"
        if score >= 0.30:
            return "low"
        return "normal"

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_44_BUDGET_LOW_FRICTION_SCHEMA,
            "signal_id": sanitize_text(self.signal_id, limit=160),
            "step_pressure_score": round(float(self.step_pressure_score), 4),
            "timeout_pressure_score": round(float(self.timeout_pressure_score), 4),
            "failure_pressure_score": round(float(self.failure_pressure_score), 4),
            "pressure_level": self.pressure_level,
            "resource_exhausted": self.resource_exhausted,
            "degradation_recommended": self.degradation_recommended,
            "lease_renewal_recommended": self.lease_renewal_recommended,
            "lease_extension_steps": self.lease_extension_steps,
            "hint": sanitize_text(self.hint, limit=520),
            "no_budget_mutation": self.no_budget_mutation,
            "no_execution_block": self.no_execution_block,
        }


@dataclass(frozen=True)
class BudgetLowFrictionDecision:
    """预算治理决策。决策本身不执行，只供 Planner/Permit/QualityGate 消费。"""

    decision_id: str
    pressure_signal: BudgetPressureSignal
    low_friction_steps: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    confirmation_steps: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    strong_gate_steps: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    hard_blocked_steps: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    degradation_hints: tuple[str, ...] = field(default_factory=tuple)
    lease_hints: tuple[str, ...] = field(default_factory=tuple)
    issues: tuple[str, ...] = field(default_factory=tuple)
    a0_a4_low_friction_preserved: bool = True
    a5_hard_boundary_preserved: bool = True
    credential_privacy_hard_gate_preserved: bool = True
    irreversible_release_activation_merge_gate_preserved: bool = True
    no_permit_override: bool = True
    no_budget_mutation: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_quality_gate_override: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for name in (
            "a0_a4_low_friction_preserved",
            "a5_hard_boundary_preserved",
            "credential_privacy_hard_gate_preserved",
            "irreversible_release_activation_merge_gate_preserved",
            "no_permit_override",
            "no_budget_mutation",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_quality_gate_override",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, name), f"BudgetLowFrictionDecision.{name}")
        if not all(
            (
                self.a0_a4_low_friction_preserved,
                self.a5_hard_boundary_preserved,
                self.credential_privacy_hard_gate_preserved,
                self.irreversible_release_activation_merge_gate_preserved,
                self.no_permit_override,
                self.no_budget_mutation,
                self.no_direct_execution,
                self.no_tool_dispatch,
                self.no_quality_gate_override,
                self.no_kernel_mutation,
            )
        ):
            raise ValueError("BudgetLowFrictionDecision must preserve all hard boundaries")

    @property
    def passed(self) -> bool:
        return not self.hard_blocked_steps

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_44_BUDGET_LOW_FRICTION_SCHEMA,
            "source_version": SOURCE_VERSION,
            "decision_id": sanitize_text(self.decision_id, limit=180),
            "passed": self.passed,
            "pressure_signal": self.pressure_signal.public_dict(),
            "low_friction_steps": list(self.low_friction_steps),
            "confirmation_steps": list(self.confirmation_steps),
            "strong_gate_steps": list(self.strong_gate_steps),
            "hard_blocked_steps": list(self.hard_blocked_steps),
            "degradation_hints": [sanitize_text(item, limit=360) for item in self.degradation_hints],
            "lease_hints": [sanitize_text(item, limit=360) for item in self.lease_hints],
            "issues": [sanitize_text(item, limit=360) for item in self.issues],
            "a0_a4_low_friction_preserved": self.a0_a4_low_friction_preserved,
            "a5_hard_boundary_preserved": self.a5_hard_boundary_preserved,
            "credential_privacy_hard_gate_preserved": self.credential_privacy_hard_gate_preserved,
            "irreversible_release_activation_merge_gate_preserved": self.irreversible_release_activation_merge_gate_preserved,
            "no_permit_override": self.no_permit_override,
            "no_budget_mutation": self.no_budget_mutation,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_quality_gate_override": self.no_quality_gate_override,
            "no_kernel_mutation": self.no_kernel_mutation,
        }

    def planner_hint(self) -> str:
        return sanitize_text(
            "L6.44预算治理："
            f"pressure={self.pressure_signal.pressure_level}; "
            f"low_friction={len(self.low_friction_steps)}; confirm={len(self.confirmation_steps)}; "
            f"strong_gate={len(self.strong_gate_steps)}; blocked={len(self.hard_blocked_steps)}; "
            "A0-A4保持低摩擦，A5/凭证/隐私/不可逆/发布激活合入保留硬边界；"
            "预算压力只生成降级/续租建议，不直接扣费、不越过Permit/QualityGate。",
            limit=1200,
        )


@dataclass(frozen=True)
class BudgetLowFrictionReport:
    report_id: str
    status: str
    decision: BudgetLowFrictionDecision
    report_digest: str = ""
    planner_consumable: bool = True
    no_second_runtime: bool = True
    no_permit_override: bool = True
    no_budget_mutation: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for name in (
            "planner_consumable",
            "no_second_runtime",
            "no_permit_override",
            "no_budget_mutation",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, name), f"BudgetLowFrictionReport.{name}")
        if not all(
            (
                self.planner_consumable,
                self.no_second_runtime,
                self.no_permit_override,
                self.no_budget_mutation,
                self.no_direct_execution,
                self.no_tool_dispatch,
                self.no_kernel_mutation,
            )
        ):
            raise ValueError("BudgetLowFrictionReport must remain non-executing")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_44_BUDGET_LOW_FRICTION_SCHEMA,
            "source_version": SOURCE_VERSION,
            "report_id": sanitize_text(self.report_id, limit=180),
            "status": sanitize_text(self.status, limit=120),
            "decision": self.decision.public_dict(),
            "planner_hint": self.decision.planner_hint(),
            "report_digest": sanitize_text(self.report_digest, limit=80),
            "planner_consumable": self.planner_consumable,
            "no_second_runtime": self.no_second_runtime,
            "no_permit_override": self.no_permit_override,
            "no_budget_mutation": self.no_budget_mutation,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_kernel_mutation": self.no_kernel_mutation,
        }

    def summary_text(self) -> str:
        return self.decision.planner_hint()


class BudgetLowFrictionGovernanceBridge:
    """生成低摩擦预算治理报告；不执行、不扣费、不改策略。"""

    def __init__(self, *, risk_classifier: RiskClassifier | None = None, policy: ExecutionPolicy | None = None) -> None:
        self._risk_classifier = risk_classifier or RiskClassifier()
        self._policy = policy or ExecutionPolicy.default()
        self._last_report: BudgetLowFrictionReport | None = None

    @property
    def last_report(self) -> BudgetLowFrictionReport | None:
        return self._last_report

    def build_pressure_signal(self, budget_snapshot: Any | None = None) -> BudgetPressureSignal:
        data = _to_public_dict(budget_snapshot)
        step_pressure = _step_pressure(data)
        timeout_pressure = _timeout_pressure(data)
        failure_pressure = _failure_pressure(data)
        resource_exhausted = bool(data.get("resource_exhausted") is True)
        pressure = max(step_pressure, timeout_pressure, failure_pressure)
        degradation = bool(data.get("downgrade_required") is True or pressure >= 0.70 or resource_exhausted)
        lease_recommended = bool(_lease_requested(data) or pressure >= 0.55 or resource_exhausted)
        lease_extension = _safe_int(_nested(data, "chain_lease", "requested_extension"), default=0)
        if lease_recommended and lease_extension == 0:
            lease_extension = 5 if pressure < 0.80 else 10
        hint = _budget_hint(data, pressure=pressure, degradation=degradation, lease_recommended=lease_recommended)
        signal = BudgetPressureSignal(
            signal_id=f"budget_pressure:l6_44_{stable_digest(data or {'empty': True}, length=16)}",
            step_pressure_score=step_pressure,
            timeout_pressure_score=timeout_pressure,
            failure_pressure_score=failure_pressure,
            resource_exhausted=resource_exhausted,
            degradation_recommended=degradation,
            lease_renewal_recommended=lease_recommended,
            lease_extension_steps=lease_extension,
            hint=hint,
        )
        return signal

    def evaluate(self, plan: Iterable[ToolInvocation] | None = None, *, budget_snapshot: Any | None = None) -> BudgetLowFrictionReport:
        signal = self.build_pressure_signal(budget_snapshot)
        low: list[dict[str, Any]] = []
        confirm: list[dict[str, Any]] = []
        strong: list[dict[str, Any]] = []
        blocked: list[dict[str, Any]] = []
        issues: list[str] = []
        for index, step in enumerate(list(plan or [])):
            if not isinstance(step, ToolInvocation):
                blocked.append({"index": index, "reason": "step is not ToolInvocation"})
                issues.append("non_tool_invocation_step")
                continue
            sensitive_issue = _sensitive_argument_issue(step)
            risk, reason = self._risk_classifier.classify(step)
            item = _step_item(step, risk=risk, reason=reason, index=index)
            if sensitive_issue:
                blocked.append({**item, "reason": sanitize_text(sensitive_issue, limit=360), "hard_boundary": "credential_or_privacy"})
                issues.append(sensitive_issue)
                continue
            if risk in self._policy.blocked_levels or risk == RiskLevel.A5:
                blocked.append({**item, "hard_boundary": "A5"})
                issues.append(f"A5 blocked before execution: {step.tool_name}")
                continue
            if _requires_strong_gate(step):
                strong.append({**item, "requires_quality_gate": True, "requires_confirmation": True, "hard_boundary": "release_activation_merge_or_irreversible"})
                continue
            if risk in self._policy.confirmation_levels:
                confirm.append({**item, "requires_confirmation": True, "low_friction_confirmation": True})
                continue
            low.append({**item, "low_friction": True, "budget_pressure_action": _pressure_action(signal)})
        degradation_hints = _degradation_hints(signal)
        lease_hints = _lease_hints(signal)
        digest_payload = {"pressure": signal.public_dict(), "low": low, "confirm": confirm, "strong": strong, "blocked": blocked, "issues": issues}
        decision = BudgetLowFrictionDecision(
            decision_id=f"budget_low_friction_decision:l6_44_{stable_digest(digest_payload, length=16)}",
            pressure_signal=signal,
            low_friction_steps=tuple(low),
            confirmation_steps=tuple(confirm),
            strong_gate_steps=tuple(strong),
            hard_blocked_steps=tuple(blocked),
            degradation_hints=tuple(degradation_hints),
            lease_hints=tuple(lease_hints),
            issues=tuple(issues),
        )
        status = "budget_low_friction_ready" if decision.passed else "budget_low_friction_blocked"
        report = BudgetLowFrictionReport(
            report_id=f"budget_low_friction_report:l6_44_{stable_digest(decision.public_dict(), length=16)}",
            status=status,
            decision=decision,
        )
        digest = stable_digest({k: v for k, v in report.public_dict().items() if k != "report_digest"}, length=24)
        report = BudgetLowFrictionReport(**{**report.__dict__, "report_digest": digest})
        self._last_report = report
        return report

    def build_planner_hint(self) -> str:
        if self._last_report is None:
            return ""
        return self._last_report.summary_text()

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": L6_44_BUDGET_LOW_FRICTION_SCHEMA, "status": "empty"}
        return self._last_report.public_dict()


def _to_public_dict(value: Any | None) -> dict[str, Any]:
    if value is None:
        return {}
    if hasattr(value, "public_dict") and callable(value.public_dict):
        maybe = value.public_dict()
        return dict(maybe) if isinstance(maybe, dict) else {}
    if isinstance(value, dict):
        return dict(value)
    return {}


def _nested(data: dict[str, Any], *keys: str) -> Any:
    current: Any = data
    for key in keys:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _safe_int(value: Any, *, default: int = 0) -> int:
    if isinstance(value, bool):
        return default
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, *, default: float = 0.0) -> float:
    if isinstance(value, bool):
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ratio(used: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return max(0.0, min(1.0, used / total))


def _step_pressure(data: dict[str, Any]) -> float:
    ledger = data.get("step_ledger") if isinstance(data.get("step_ledger"), dict) else {}
    max_steps = _safe_float(ledger.get("max_steps"), default=0.0)
    remaining = _safe_float(ledger.get("remaining_steps"), default=max_steps)
    planned = _safe_float(ledger.get("planned_steps"), default=0.0)
    if bool(ledger.get("exhausted") is True):
        return 1.0
    if max_steps <= 0:
        return 0.0
    projected_used = max(0.0, max_steps - remaining + planned)
    return _ratio(projected_used, max_steps)


def _timeout_pressure(data: dict[str, Any]) -> float:
    timeout = data.get("timeout_budget") if isinstance(data.get("timeout_budget"), dict) else {}
    default_timeout = _safe_float(timeout.get("default_timeout_seconds"), default=0.0)
    remaining = _safe_float(timeout.get("remaining_timeout_seconds"), default=default_timeout)
    if bool(timeout.get("blocks_execution") is True):
        return 1.0
    if default_timeout <= 0:
        return 0.0
    return max(0.0, min(1.0, 1.0 - remaining / default_timeout))


def _failure_pressure(data: dict[str, Any]) -> float:
    failure = data.get("failure_budget") if isinstance(data.get("failure_budget"), dict) else {}
    max_failures = _safe_float(failure.get("max_failures"), default=0.0)
    observed = _safe_float(failure.get("observed_failures"), default=0.0)
    if bool(failure.get("exhausted") is True):
        return 1.0
    if max_failures <= 0:
        return 0.0
    return _ratio(observed, max_failures)


def _lease_requested(data: dict[str, Any]) -> bool:
    lease = data.get("chain_lease") if isinstance(data.get("chain_lease"), dict) else {}
    return bool(lease.get("renewal_recommended") is True or _safe_int(lease.get("requested_extension"), default=0) > 0)


def _budget_hint(data: dict[str, Any], *, pressure: float, degradation: bool, lease_recommended: bool) -> str:
    base = sanitize_text(data.get("planner_budget_hint") or "", limit=360)
    suffix = []
    if pressure >= 0.80:
        suffix.append("预算压力高：建议分段、压缩上下文、建立恢复点。")
    elif pressure >= 0.55:
        suffix.append("预算压力中：建议优先完成当前闭环，减少探索性步骤。")
    if degradation:
        suffix.append("允许降级建议，但不得默认阻断 A0-A4。")
    if lease_recommended:
        suffix.append("建议生成续租/扩展提示，真实扩展仍由执行链治理。")
    if not suffix:
        suffix.append("预算正常：A0-A4 低摩擦进入执行链。")
    return sanitize_text(" ".join([base, *suffix]).strip(), limit=720)


def _step_item(step: ToolInvocation, *, risk: RiskLevel, reason: str, index: int) -> dict[str, Any]:
    return {
        "index": index,
        "step_id": sanitize_text(step.step_id, limit=100),
        "tool_name": sanitize_text(step.tool_name, limit=120),
        "risk_level": risk.value,
        "reason": sanitize_text(reason or step.reason, limit=360),
    }


def _pressure_action(signal: BudgetPressureSignal) -> str:
    if signal.pressure_level in {"high", "exhausted_recoverable"}:
        return "continue_with_degradation_and_checkpoint"
    if signal.pressure_level == "medium":
        return "continue_with_budget_awareness"
    return "continue_normal"


def _degradation_hints(signal: BudgetPressureSignal) -> list[str]:
    if not signal.degradation_recommended:
        return []
    return [
        "预算压力触发降级建议：压缩上下文、减少探索步骤、分段提交、优先当前闭环。",
        "降级建议不得成为 A0-A4 默认拒绝权；真实执行仍走 ExecutionSpine。",
    ]


def _lease_hints(signal: BudgetPressureSignal) -> list[str]:
    if not signal.lease_renewal_recommended:
        return []
    return [
        f"建议申请链路续租/扩展 {signal.lease_extension_steps} 步；续租只生成提示，不直接改预算。",
    ]


def _requires_strong_gate(step: ToolInvocation) -> bool:
    name = step.tool_name.lower()
    if any(term in name for term in STRONG_GATE_TOOL_TERMS):
        return True
    text = " ".join(str(v).lower() for v in step.arguments.values())
    if any(term in text for term in IRREVERSIBLE_ARG_TERMS):
        return True
    return False


def _sensitive_argument_issue(step: ToolInvocation) -> str:
    def scan(value: Any) -> str:
        if isinstance(value, dict):
            for key, item in value.items():
                clean_key = str(key).lower().strip()
                if clean_key in SENSITIVE_ARG_KEYS or any(marker in clean_key for marker in SENSITIVE_ARG_KEYS):
                    return f"sensitive argument key blocked: {sanitize_text(key, limit=60)}"
                nested = scan(item)
                if nested:
                    return nested
        elif isinstance(value, (list, tuple)):
            for item in value:
                nested = scan(item)
                if nested:
                    return nested
        elif isinstance(value, str):
            lowered = value.lower()
            if any(marker in lowered for marker in ("api_key=", "authorization:", "bearer ", "secret=", "password=", "raw_memory_body", "private_key")):
                return "sensitive argument value blocked"
        return ""

    return scan(step.arguments)
