"""L6.43.1 Planner 消费层统一改造。

本模块把 L6.43 的 ``UnifiedPlannerContextPack`` 变成 Planner 唯一可消费上下文，
并在计划进入执行链前做只读预检。它不调用工具、不调模型 SDK、不改预算、不写记忆、
不修改核心组；真实执行仍由 L6.37 执行链处理。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable

from tiangong_kernel.l6_plugins.common._common import ensure_bool

from .execution_policy import RiskLevel
from .four_path_context_router import FourPathContextReport, UnifiedPlannerContextPack
from .four_path_public_projection import sanitize_text, stable_digest
from .model_planner import ModelPlanner, ModelPlannerResult
from .risk_classifier import RiskClassifier
from .tool_invocation import ToolInvocation

L6_43_1_PLANNER_CONSUMPTION_SCHEMA = "tiangong.l6_43_1.planner_unified_consumption.v1"
SOURCE_VERSION = "L6.43.1-planner-unified-consumption"
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
}


@dataclass(frozen=True)
class PlannerUnifiedContextHint:
    """给 ModelPlanner 的唯一上下文提示。"""

    hint_id: str
    source_pack_id: str
    source_context_digest: str
    model_context_hint: str
    hard_boundaries: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    preflight_passed: bool = True
    planner_consumable: bool = True
    consumes_unified_context_pack_only: bool = True
    rejects_scattered_memory_affective_lifecycle_objects: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_model_dispatch: bool = True
    no_budget_mutation: bool = True
    no_memory_write: bool = True
    no_memory_delete: bool = True
    no_kernel_mutation: bool = True
    no_registry_mutation: bool = True
    no_secret_read: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "preflight_passed",
            "planner_consumable",
            "consumes_unified_context_pack_only",
            "rejects_scattered_memory_affective_lifecycle_objects",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_model_dispatch",
            "no_budget_mutation",
            "no_memory_write",
            "no_memory_delete",
            "no_kernel_mutation",
            "no_registry_mutation",
            "no_secret_read",
        ):
            ensure_bool(getattr(self, field_name), f"PlannerUnifiedContextHint.{field_name}")
        if not all(
            (
                self.preflight_passed,
                self.planner_consumable,
                self.consumes_unified_context_pack_only,
                self.rejects_scattered_memory_affective_lifecycle_objects,
                self.no_direct_execution,
                self.no_tool_dispatch,
                self.no_model_dispatch,
                self.no_budget_mutation,
                self.no_memory_write,
                self.no_memory_delete,
                self.no_kernel_mutation,
                self.no_registry_mutation,
                self.no_secret_read,
            )
        ):
            raise ValueError("PlannerUnifiedContextHint must remain unified, non-executing and non-mutating")
        if not sanitize_text(self.model_context_hint, limit=20_000):
            raise ValueError("model_context_hint must be non-empty")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_43_1_PLANNER_CONSUMPTION_SCHEMA,
            "source_version": SOURCE_VERSION,
            "hint_id": sanitize_text(self.hint_id, limit=220),
            "source_pack_id": sanitize_text(self.source_pack_id, limit=240),
            "source_context_digest": sanitize_text(self.source_context_digest, limit=80),
            "model_context_hint": sanitize_text(self.model_context_hint, limit=5200),
            "hard_boundaries": list(self.hard_boundaries),
            "preflight_passed": self.preflight_passed,
            "planner_consumable": self.planner_consumable,
            "consumes_unified_context_pack_only": self.consumes_unified_context_pack_only,
            "rejects_scattered_memory_affective_lifecycle_objects": self.rejects_scattered_memory_affective_lifecycle_objects,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_model_dispatch": self.no_model_dispatch,
            "no_budget_mutation": self.no_budget_mutation,
            "no_memory_write": self.no_memory_write,
            "no_memory_delete": self.no_memory_delete,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_registry_mutation": self.no_registry_mutation,
            "no_secret_read": self.no_secret_read,
        }


@dataclass(frozen=True)
class PlannerPlanPreflightDecision:
    """计划进入执行链前的只读预检。"""

    decision_id: str
    passed: bool
    allowed_steps: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    confirmation_steps: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    blocked_steps: tuple[dict[str, Any], ...] = field(default_factory=tuple)
    issues: tuple[str, ...] = field(default_factory=tuple)
    a0_a4_low_friction_preserved: bool = True
    a5_hard_boundary_preserved: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_budget_mutation: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "passed",
            "a0_a4_low_friction_preserved",
            "a5_hard_boundary_preserved",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_budget_mutation",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"PlannerPlanPreflightDecision.{field_name}")
        if not (
            self.a0_a4_low_friction_preserved
            and self.a5_hard_boundary_preserved
            and self.no_direct_execution
            and self.no_tool_dispatch
            and self.no_budget_mutation
            and self.no_kernel_mutation
        ):
            raise ValueError("PlannerPlanPreflightDecision must remain non-executing and boundary-preserving")
        if self.blocked_steps and self.passed:
            raise ValueError("plan preflight cannot pass with blocked steps")

    def public_dict(self) -> dict[str, Any]:
        return {
            "decision_id": sanitize_text(self.decision_id, limit=220),
            "passed": self.passed,
            "allowed_steps": list(self.allowed_steps),
            "confirmation_steps": list(self.confirmation_steps),
            "blocked_steps": list(self.blocked_steps),
            "issues": [sanitize_text(issue, limit=260) for issue in self.issues],
            "a0_a4_low_friction_preserved": self.a0_a4_low_friction_preserved,
            "a5_hard_boundary_preserved": self.a5_hard_boundary_preserved,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_budget_mutation": self.no_budget_mutation,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


@dataclass(frozen=True)
class PlannerConsumptionReport:
    """Planner 消费层报告。"""

    report_id: str
    status: str
    context_hint: PlannerUnifiedContextHint
    plan_preflight: PlannerPlanPreflightDecision
    planner_result_summary: str = ""
    planner_result_ok: bool | None = None
    report_digest: str = ""
    planner_consumable: bool = True
    no_second_runtime: bool = True
    no_direct_execution: bool = True
    no_tool_dispatch: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        for field_name in (
            "planner_consumable",
            "no_second_runtime",
            "no_direct_execution",
            "no_tool_dispatch",
            "no_kernel_mutation",
        ):
            ensure_bool(getattr(self, field_name), f"PlannerConsumptionReport.{field_name}")
        if not (self.planner_consumable and self.no_second_runtime and self.no_direct_execution and self.no_tool_dispatch and self.no_kernel_mutation):
            raise ValueError("PlannerConsumptionReport must remain non-executing")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": L6_43_1_PLANNER_CONSUMPTION_SCHEMA,
            "source_version": SOURCE_VERSION,
            "report_id": sanitize_text(self.report_id, limit=220),
            "status": sanitize_text(self.status, limit=120),
            "context_hint": self.context_hint.public_dict(),
            "plan_preflight": self.plan_preflight.public_dict(),
            "planner_result_summary": sanitize_text(self.planner_result_summary, limit=600),
            "planner_result_ok": self.planner_result_ok,
            "report_digest": sanitize_text(self.report_digest, limit=80),
            "planner_consumable": self.planner_consumable,
            "no_second_runtime": self.no_second_runtime,
            "no_direct_execution": self.no_direct_execution,
            "no_tool_dispatch": self.no_tool_dispatch,
            "no_kernel_mutation": self.no_kernel_mutation,
        }

    def summary_text(self) -> str:
        return (
            "L6.43.1 Planner消费层："
            f"status={self.status}; context={self.context_hint.source_context_digest}; "
            f"preflight={self.plan_preflight.passed}; blocked={len(self.plan_preflight.blocked_steps)}; "
            "single_context_pack=True; no_second_runtime=True; no_core_pollution=True。"
        )


class PlannerUnifiedConsumptionBridge:
    """把 FourPathContextReport 转成 Planner 唯一消费入口。"""

    def __init__(self, *, risk_classifier: RiskClassifier | None = None) -> None:
        self._risk_classifier = risk_classifier or RiskClassifier()
        self._last_report: PlannerConsumptionReport | None = None

    @property
    def last_report(self) -> PlannerConsumptionReport | None:
        return self._last_report

    def build_context_hint(self, four_path_report: FourPathContextReport, *, max_chars: int = 5200) -> PlannerUnifiedContextHint:
        _ensure_four_path_report(four_path_report)
        pack = four_path_report.context_pack
        hint_text = _render_context_hint(pack, max_chars=max_chars)
        hint = PlannerUnifiedContextHint(
            hint_id=f"planner_unified_context_hint:{stable_digest([pack.pack_id, pack.context_digest], length=16)}",
            source_pack_id=pack.pack_id,
            source_context_digest=pack.context_digest,
            model_context_hint=hint_text,
            hard_boundaries=pack.hard_boundaries,
        )
        return hint

    def preflight_plan(self, plan: Iterable[ToolInvocation]) -> PlannerPlanPreflightDecision:
        allowed: list[dict[str, Any]] = []
        confirmation: list[dict[str, Any]] = []
        blocked: list[dict[str, Any]] = []
        issues: list[str] = []
        for index, step in enumerate(list(plan)):
            if not isinstance(step, ToolInvocation):
                blocked.append({"index": index, "reason": "step is not ToolInvocation"})
                issues.append("non_tool_invocation_step")
                continue
            sensitive_issue = _sensitive_argument_issue(step)
            risk, reason = self._risk_classifier.classify(step)
            item = {
                "step_id": sanitize_text(step.step_id, limit=100),
                "tool_name": sanitize_text(step.tool_name, limit=120),
                "risk_level": risk.value,
                "reason": sanitize_text(reason, limit=360),
            }
            if sensitive_issue:
                item = {**item, "reason": sanitize_text(sensitive_issue, limit=360)}
                blocked.append(item)
                issues.append(sensitive_issue)
                continue
            if risk == RiskLevel.A5:
                blocked.append(item)
                issues.append(f"A5 blocked before execution: {step.tool_name}")
            elif risk == RiskLevel.A4:
                confirmation.append({**item, "requires_confirmation": True})
            else:
                allowed.append({**item, "low_friction": True})
        digest = stable_digest({"allowed": allowed, "confirmation": confirmation, "blocked": blocked, "issues": issues}, length=16)
        return PlannerPlanPreflightDecision(
            decision_id=f"planner_plan_preflight:l6_43_1_{digest}",
            passed=not blocked,
            allowed_steps=tuple(allowed),
            confirmation_steps=tuple(confirmation),
            blocked_steps=tuple(blocked),
            issues=tuple(issues),
        )

    def consume(
        self,
        four_path_report: FourPathContextReport,
        *,
        plan: Iterable[ToolInvocation] | None = None,
        planner_result: ModelPlannerResult | None = None,
    ) -> PlannerConsumptionReport:
        hint = self.build_context_hint(four_path_report)
        if planner_result is not None:
            preflight = self.preflight_plan(planner_result.plan if planner_result.ok else [])
            planner_summary = planner_result.message
            planner_ok = planner_result.ok
        else:
            preflight = self.preflight_plan(plan or [])
            planner_summary = "plan_preflight_only"
            planner_ok = None
        status = "planner_consumption_ready" if preflight.passed else "planner_consumption_blocked"
        report = PlannerConsumptionReport(
            report_id=f"planner_consumption_report:{stable_digest([hint.public_dict(), preflight.public_dict(), planner_summary], length=16)}",
            status=status,
            context_hint=hint,
            plan_preflight=preflight,
            planner_result_summary=planner_summary,
            planner_result_ok=planner_ok,
        )
        digest = stable_digest({k: v for k, v in report.public_dict().items() if k != "report_digest"}, length=24)
        report = PlannerConsumptionReport(**{**report.__dict__, "report_digest": digest})
        self._last_report = report
        return report

    def build_model_plan(
        self,
        planner: ModelPlanner,
        user_message: str,
        *,
        four_path_report: FourPathContextReport,
        model_config: Any,
        model_client: Any,
        max_steps: int = 80,
    ) -> tuple[ModelPlannerResult, PlannerConsumptionReport]:
        hint = self.build_context_hint(four_path_report)
        result = planner.build_plan(
            user_message,
            model_config=model_config,
            model_client=model_client,
            max_steps=max_steps,
            context_hint=hint.model_context_hint,
        )
        report = self.consume(four_path_report, planner_result=result)
        return result, report

    def build_planner_hint(self) -> str:
        if self._last_report is None:
            return ""
        return self._last_report.summary_text()[:1800]

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": L6_43_1_PLANNER_CONSUMPTION_SCHEMA, "status": "empty"}
        return self._last_report.public_dict()


def _ensure_four_path_report(report: FourPathContextReport) -> None:
    if not isinstance(report, FourPathContextReport):
        raise TypeError("PlannerUnifiedConsumptionBridge only accepts FourPathContextReport")
    if not report.preflight.passed:
        raise ValueError("FourPathContextReport preflight must pass before Planner consumption")
    pack = report.context_pack
    if not isinstance(pack, UnifiedPlannerContextPack):
        raise TypeError("FourPathContextReport.context_pack must be UnifiedPlannerContextPack")
    if not (pack.planner_consumable and pack.unified_projection and pack.no_second_runtime and pack.no_direct_execution):
        raise ValueError("UnifiedPlannerContextPack is not safe for Planner consumption")
    if not (pack.summary_only and pack.evidence_ref_only and pack.no_memory_write and pack.no_memory_delete):
        raise ValueError("UnifiedPlannerContextPack must remain summary/evidence-ref only")


def _render_context_hint(pack: UnifiedPlannerContextPack, *, max_chars: int) -> str:
    lines: list[str] = [
        "[L6.43.1 UnifiedPlannerContextPack ONLY]",
        f"pack_id: {sanitize_text(pack.pack_id, limit=220)}",
        f"context_digest: {sanitize_text(pack.context_digest, limit=80)}",
        f"execution_contract_ref: {sanitize_text(pack.execution_contract_ref, limit=220)}",
        f"user_task_summary: {sanitize_text(pack.user_task_summary, limit=520)}",
        "hard_rule: Planner 只能消费本包；不得直接消费 Memory、Affective、Lifecycle 散对象。",
        "hard_rule: 本包只做上下文提示，不授权、不拒绝、不调工具、不改预算、不写记忆、不改内核。",
        "hard_rule: A0-A4 低摩擦进入既有执行链；A5、凭证、隐私、不可逆副作用、发布、激活、合入必须保留硬边界。",
        "",
        "[memory_top_hints summary_only top<=5]",
    ]
    for item in pack.top_memory_hints:
        lines.append(
            "- "
            + sanitize_text(item.get("memory_id"), limit=100)
            + ": "
            + sanitize_text(item.get("sanitized_summary"), limit=260)
        )
    lines.extend(["", "[affective_language_and_doing_hints]"])
    lines.append(f"style: {sanitize_text(pack.affective_style_hint, limit=360)}")
    lines.append(f"candidate_bias: {sanitize_text(pack.affective_candidate_bias, limit=520)}")
    lines.extend(["", "[lifecycle_candidate_hints top<=3]"])
    for item in pack.lifecycle_next_action_hints:
        lines.append(
            "- "
            + sanitize_text(item.get("hint_id"), limit=100)
            + ": "
            + sanitize_text(item.get("hint_text"), limit=320)
        )
    lines.extend(["", "[constraints]"])
    for title, items in (
        ("quality", pack.quality_gate_constraints),
        ("budget", pack.budget_constraints),
        ("provider", pack.provider_constraints),
        ("skill", pack.skill_hints),
        ("handoff", pack.handoff_hints),
    ):
        if not items:
            continue
        lines.append(f"{title}:")
        for item in items[:3]:
            lines.append("- " + sanitize_text(item, limit=320))
    lines.extend(["", "[hard_boundaries]"])
    for item in pack.hard_boundaries[:8]:
        lines.append("- " + sanitize_text(item, limit=320))
    lines.extend(["", "[evidence_refs redacted only]"])
    for item in pack.redacted_evidence_refs[:8]:
        lines.append("- " + sanitize_text(item.get("evidence_ref"), limit=180) + " digest=" + sanitize_text(item.get("digest"), limit=80))
    return sanitize_text("\n".join(lines), limit=max_chars)


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
            if any(marker in lowered for marker in ("api_key=", "authorization:", "bearer ", "secret=", "password=", "raw_memory_body")):
                return "sensitive argument value blocked"
        return ""

    return scan(step.arguments)
