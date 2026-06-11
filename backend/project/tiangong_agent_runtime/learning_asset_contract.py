"""L6.70.2-R16 future Tool/Skill asset contract.

This module standardizes every future asset produced from autonomous learning,
experience synthesis, Tool gap mining, or Skill drafting.  It is metadata-only:
it does not write Skill registries, produce Tool code, register tools, call models,
start loops, or mutate Runtime policy.  It gives LLM a single format to review,
validate, route, and later hand to governed production chains.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from time import time
from typing import Any

from tiangong_agent_shell.safe_logging import redact_text

from .runtime_tool_registry import ToolDescriptor
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext

LEARNING_ASSET_CONTRACT_SCHEMA = "tiangong.l6702.r16.learning_asset_contract.v1"
CONTRACT_TOOL_NAMES = {
    "learning_asset_contract_guide",
    "learning_asset_contract_normalize",
    "learning_asset_contract_validate",
}
ASSET_KINDS = {"skill", "tool", "toolpackage", "ability", "workflow", "usage_card", "chain_recipe"}
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


REQUIRED_CONTRACT_FIELDS = [
    "schema",
    "asset_ref",
    "asset_kind",
    "namespace",
    "name",
    "version",
    "status",
    "source_trace",
    "purpose",
    "trigger_rules",
    "input_contract",
    "output_contract",
    "runtime_binding",
    "usage_card",
    "chain_recipe",
    "risk_profile",
    "validation_contract",
    "rollback_contract",
    "audit_contract",
    "llm_policy",
    "lifecycle",
]


@dataclass(frozen=True)
class UnifiedLearningAssetContract:
    """统一 Tool/Skill/能力候选资产格式。"""

    asset_ref: str
    asset_kind: str
    namespace: str
    name: str
    version: str
    status: str
    source_trace: dict[str, Any]
    purpose: str
    trigger_rules: list[str]
    input_contract: dict[str, Any]
    output_contract: dict[str, Any]
    runtime_binding: dict[str, Any]
    usage_card: dict[str, Any]
    chain_recipe: list[str]
    risk_profile: dict[str, Any]
    validation_contract: dict[str, Any]
    rollback_contract: dict[str, Any]
    audit_contract: dict[str, Any]
    llm_policy: dict[str, Any]
    lifecycle: dict[str, Any]
    generated_at: float = field(default_factory=time)
    candidate_only: bool = True
    review_before_activation: bool = True
    no_direct_execution: bool = True
    no_skill_registry_write: bool = True
    no_tool_code_write: bool = True
    no_tool_registration: bool = True
    no_tool_invocation: bool = True
    no_model_dispatch: bool = True
    no_kernel_mutation: bool = True

    def __post_init__(self) -> None:
        if self.asset_kind not in ASSET_KINDS:
            raise ValueError(f"unsupported asset_kind: {self.asset_kind}")
        required_truth = (
            self.candidate_only,
            self.review_before_activation,
            self.no_direct_execution,
            self.no_skill_registry_write,
            self.no_tool_code_write,
            self.no_tool_registration,
            self.no_tool_invocation,
            self.no_model_dispatch,
            self.no_kernel_mutation,
        )
        if not all(required_truth):
            raise ValueError("learning asset contract must remain candidate-only and review-gated")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": LEARNING_ASSET_CONTRACT_SCHEMA,
            "generated_at": self.generated_at,
            "asset_ref": _safe_text(self.asset_ref, limit=220),
            "asset_kind": _safe_text(self.asset_kind, limit=60),
            "namespace": _safe_text(self.namespace, limit=160),
            "name": _safe_text(self.name, limit=160),
            "version": _safe_text(self.version, limit=60),
            "status": _safe_text(self.status, limit=80),
            "source_trace": _safe_dict(self.source_trace),
            "purpose": _safe_text(self.purpose, limit=900),
            "trigger_rules": [_safe_text(item, limit=280) for item in self.trigger_rules[:12]],
            "input_contract": _safe_dict(self.input_contract),
            "output_contract": _safe_dict(self.output_contract),
            "runtime_binding": _safe_dict(self.runtime_binding),
            "usage_card": _safe_dict(self.usage_card),
            "chain_recipe": [_safe_text(item, limit=280) for item in self.chain_recipe[:20]],
            "risk_profile": _safe_dict(self.risk_profile),
            "validation_contract": _safe_dict(self.validation_contract),
            "rollback_contract": _safe_dict(self.rollback_contract),
            "audit_contract": _safe_dict(self.audit_contract),
            "llm_policy": _safe_dict(self.llm_policy),
            "lifecycle": _safe_dict(self.lifecycle),
            "candidate_only": self.candidate_only,
            "review_before_activation": self.review_before_activation,
            "no_direct_execution": self.no_direct_execution,
            "no_skill_registry_write": self.no_skill_registry_write,
            "no_tool_code_write": self.no_tool_code_write,
            "no_tool_registration": self.no_tool_registration,
            "no_tool_invocation": self.no_tool_invocation,
            "no_model_dispatch": self.no_model_dispatch,
            "no_kernel_mutation": self.no_kernel_mutation,
        }


@dataclass(frozen=True)
class ContractValidationIssue:
    field: str
    severity: str
    message: str

    def public_dict(self) -> dict[str, str]:
        return {"field": self.field, "severity": self.severity, "message": self.message}


@dataclass(frozen=True)
class LearningAssetContractReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    contracts: list[UnifiedLearningAssetContract] = field(default_factory=list)
    validation_issues: list[ContractValidationIssue] = field(default_factory=list)
    source_counts: dict[str, int] = field(default_factory=dict)
    future_enforcement_policy: dict[str, Any] = field(default_factory=dict)
    candidate_only: bool = True
    writes_skill_registry: bool = False
    writes_tool_code: bool = False
    registers_tool: bool = False
    activates_skill: bool = False
    invokes_tool: bool = False
    dispatches_model: bool = False
    mutates_kernel: bool = False

    def __post_init__(self) -> None:
        if not self.candidate_only:
            raise ValueError("learning asset report must be candidate-only")
        if any((
            self.writes_skill_registry,
            self.writes_tool_code,
            self.registers_tool,
            self.activates_skill,
            self.invokes_tool,
            self.dispatches_model,
            self.mutates_kernel,
        )):
            raise ValueError("learning asset report cannot perform production or Runtime side effects")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "contracts": [item.public_dict() for item in self.contracts],
            "contract_count": len(self.contracts),
            "validation_issues": [item.public_dict() for item in self.validation_issues],
            "issue_count": len(self.validation_issues),
            "source_counts": dict(self.source_counts),
            "future_enforcement_policy": _safe_dict(self.future_enforcement_policy),
            "candidate_only": self.candidate_only,
            "writes_skill_registry": self.writes_skill_registry,
            "writes_tool_code": self.writes_tool_code,
            "registers_tool": self.registers_tool,
            "activates_skill": self.activates_skill,
            "invokes_tool": self.invokes_tool,
            "dispatches_model": self.dispatches_model,
            "mutates_kernel": self.mutates_kernel,
        }

    def summary_text(self) -> str:
        return (
            "R16 未来 Tool/Skill 统一资产契约："
            f"status={self.status}；contracts={len(self.contracts)}；issues={len(self.validation_issues)}。{self.summary}"
        )


class LearningAssetContractBridge:
    """Holds last normalized Tool/Skill contract report."""

    def __init__(self) -> None:
        self._last_report: LearningAssetContractReport | None = None

    @property
    def last_report(self) -> LearningAssetContractReport | None:
        return self._last_report

    def guide(self) -> dict[str, Any]:
        return build_contract_guide()

    def normalize(
        self,
        *,
        experience_report: dict[str, Any] | None = None,
        skill_queue: dict[str, Any] | None = None,
        tool_requests: dict[str, Any] | None = None,
        registry_descriptors: Iterable[ToolDescriptor] | None = None,
        notes: str = "",
        max_items: int = 24,
    ) -> LearningAssetContractReport:
        contracts: list[UnifiedLearningAssetContract] = []
        source_counts = {
            "experience_skill_candidates": 0,
            "experience_tool_gap_candidates": 0,
            "skill_draft_versions": 0,
            "tool_production_requests": 0,
            "runtime_descriptors": 0,
        }
        limit = max(1, min(int(max_items), 200))
        exp = experience_report or {}
        if isinstance(exp, dict):
            skill_candidates = _as_list(exp.get("skill_candidates"))
            tool_gaps = _as_list(exp.get("tool_gap_candidates"))
            source_counts["experience_skill_candidates"] = len(skill_candidates)
            source_counts["experience_tool_gap_candidates"] = len(tool_gaps)
            for item in skill_candidates[:limit]:
                if isinstance(item, dict):
                    contracts.append(_contract_from_skill_candidate(item, source_kind="experience.skill_candidate"))
            for item in tool_gaps[:limit]:
                if isinstance(item, dict):
                    contracts.append(_contract_from_tool_gap(item, source_kind="experience.tool_gap_candidate"))
        sq = skill_queue or {}
        if isinstance(sq, dict):
            drafts = _as_list(sq.get("draft_versions"))
            source_counts["skill_draft_versions"] = len(drafts)
            for item in drafts[:limit]:
                if isinstance(item, dict):
                    contracts.append(_contract_from_skill_draft(item))
        tr = tool_requests or {}
        if isinstance(tr, dict):
            requests = _as_list(tr.get("production_requests"))
            source_counts["tool_production_requests"] = len(requests)
            for item in requests[:limit]:
                if isinstance(item, dict):
                    contracts.append(_contract_from_tool_request(item))
        descriptors = list(registry_descriptors or [])
        source_counts["runtime_descriptors"] = len(descriptors)
        # Runtime descriptors are not converted to production candidates; they only prove the current
        # registry can expose future contract tools for LLM use.
        deduped = _dedupe_contracts(contracts)[:limit]
        if notes and not deduped:
            deduped.append(_manual_contract(notes))
        issues = []
        for contract in deduped:
            issues.extend(validate_contract_dict(contract.public_dict()))
        status = "pass" if deduped and not issues else ("empty" if not deduped else "needs_review")
        summary = _build_report_summary(deduped, issues, source_counts)
        report = LearningAssetContractReport(
            schema=LEARNING_ASSET_CONTRACT_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            contracts=deduped,
            validation_issues=issues,
            source_counts=source_counts,
            future_enforcement_policy=build_future_enforcement_policy(),
        )
        self._last_report = report
        return report

    def validate(self, payload: dict[str, Any] | None = None) -> LearningAssetContractReport:
        if payload is None and self._last_report is not None:
            payloads = [item.public_dict() for item in self._last_report.contracts]
            source_counts = {"validated_from": len(payloads)}
        elif payload is None:
            payloads = []
            source_counts = {"validated_from": 0}
        elif payload.get("schema") == LEARNING_ASSET_CONTRACT_SCHEMA and "contracts" in payload:
            payloads = [item for item in _as_list(payload.get("contracts")) if isinstance(item, dict)]
            source_counts = {"validated_from": len(payloads)}
        else:
            payloads = [payload]
            source_counts = {"validated_from": 1}
        contracts: list[UnifiedLearningAssetContract] = []
        issues: list[ContractValidationIssue] = []
        for item in payloads:
            issues.extend(validate_contract_dict(item))
            try:
                contracts.append(_contract_from_dict(item))
            except (TypeError, ValueError) as exc:
                issues.append(ContractValidationIssue("contract", "P1", f"无法恢复为统一契约对象：{exc}"))
        status = "pass" if payloads and not issues else ("empty" if not payloads else "needs_review")
        summary = f"已校验 {len(payloads)} 个候选契约；问题 {len(issues)} 个。"
        report = LearningAssetContractReport(
            schema=LEARNING_ASSET_CONTRACT_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            contracts=contracts,
            validation_issues=issues,
            source_counts=source_counts,
            future_enforcement_policy=build_future_enforcement_policy(),
        )
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": LEARNING_ASSET_CONTRACT_SCHEMA, "status": "empty", "guide": build_contract_guide()}
        return self._last_report.public_dict()


def build_contract_guide() -> dict[str, Any]:
    return {
        "schema": LEARNING_ASSET_CONTRACT_SCHEMA,
        "purpose": "统一未来所有自主学习、经验总结、Skill 草案、Tool 生产请求和能力候选的资产格式。",
        "required_fields": list(REQUIRED_CONTRACT_FIELDS),
        "asset_kinds": sorted(ASSET_KINDS),
        "canonical_pipeline": [
            "synthesize_experience_candidates 只产出经验/Skill/Tool 缺口候选",
            "queue_skill_candidates 转成 Skill 审阅队列",
            "queue_tool_production_requests 使用已存在 L6.22 ToolProductionRequestBridge / SandboxValidationPlan 生成 Tool 沙箱验证前置队列",
            "learning_asset_contract_normalize 归一化为统一契约",
            "learning_asset_contract_validate 做字段、边界、LLM 可用性与 no-pollution 校验",
            "learning_asset_sandbox_align / learning_asset_sandbox_validate 把 Tool 契约绑定到 L6.22 沙箱前置链",
            "质量门 + 发布门 + 回滚证据通过后，才允许后续生产链生成真实 Tool/Skill",
        ],
        "llm_rule": "LLM 是主脑；Planner 只建议；统一契约只提供可审阅资产说明，不自动激活、不写代码、不注册工具。",
        "future_enforcement_policy": build_future_enforcement_policy(),
        "minimal_usage_card": {
            "when_to_use": "什么用户意图或运行信号触发该资产",
            "how_to_call": "工具调用 JSON 或 Skill 使用入口",
            "do_not_use_when": "禁止条件和边界",
            "next_action_hint": "工具/Skill 返回后 LLM 应进入的下一步",
        },
    }


def build_future_enforcement_policy() -> dict[str, Any]:
    return {
        "policy_ref": "policy:r16_learning_asset_contract_enforcement",
        "mandatory_for_future_assets": True,
        "applies_to": [
            "autonomous_learning_outputs",
            "experience_synthesis_outputs",
            "skill_candidates",
            "skill_draft_versions",
            "tool_gap_candidates",
            "tool_production_requests",
            "ability_or_workflow_candidates",
        ],
        "activation_gate": [
            "learning_asset_contract_validate status=pass",
            "tool assets require learning_asset_sandbox_validate status=pass before future sandbox production",
            "quality_gate evidence present",
            "rollback_contract present",
            "audit_contract present",
            "runtime_binding present",
            "usage_card present",
            "chain_recipe present",
            "no v1 source/import/registry/executor/provider/self-iteration reuse",
        ],
        "side_effect_boundary": {
            "candidate_stage": "A2 metadata only; no code write, no Skill activation, no Tool registration",
            "future_sandbox_stage": "A3 governed sandbox only after LLM decision and quality gates; R17 binds this to existing L6.22 ToolProductionRequestBridge/SandboxValidationPlan preflight",
            "release_stage": "A3/A4 governed release with rollback and audit evidence",
            "a5_boundary": "destructive, credential, private key, uncontrolled shell/network, monkey patch, background loop",
        },
    }


def validate_contract_dict(payload: dict[str, Any]) -> list[ContractValidationIssue]:
    issues: list[ContractValidationIssue] = []
    if not isinstance(payload, dict):
        return [ContractValidationIssue("contract", "P0", "契约必须是 dict。")]
    for field_name in REQUIRED_CONTRACT_FIELDS:
        if field_name not in payload:
            issues.append(ContractValidationIssue(field_name, "P1", "缺少统一契约必填字段。"))
    if payload.get("schema") != LEARNING_ASSET_CONTRACT_SCHEMA:
        issues.append(ContractValidationIssue("schema", "P1", "schema 必须使用 R16 统一契约版本。"))
    if payload.get("asset_kind") not in ASSET_KINDS:
        issues.append(ContractValidationIssue("asset_kind", "P1", "asset_kind 不在允许集合内。"))
    for bool_field in (
        "candidate_only",
        "review_before_activation",
        "no_direct_execution",
        "no_skill_registry_write",
        "no_tool_code_write",
        "no_tool_registration",
        "no_tool_invocation",
        "no_model_dispatch",
        "no_kernel_mutation",
    ):
        if payload.get(bool_field) is not True:
            issues.append(ContractValidationIssue(bool_field, "P0", "候选阶段安全布尔字段必须为 True。"))
    usage = payload.get("usage_card") if isinstance(payload.get("usage_card"), dict) else {}
    for key in ("when_to_use", "how_to_call", "do_not_use_when", "next_action_hint"):
        if not _safe_text(usage.get(key), limit=40):
            issues.append(ContractValidationIssue(f"usage_card.{key}", "P1", "usage_card 缺少 LLM 可用字段。"))
    if not _as_list(payload.get("chain_recipe")):
        issues.append(ContractValidationIssue("chain_recipe", "P1", "必须提供至少一条链路步骤。"))
    for section in ("risk_profile", "validation_contract", "rollback_contract", "audit_contract", "runtime_binding"):
        if not isinstance(payload.get(section), dict) or not payload.get(section):
            issues.append(ContractValidationIssue(section, "P1", "必须提供非空治理/运行段。"))
    raw = json.dumps(payload, ensure_ascii=False, default=str).lower()
    # Only flag affirmative pollution signals. Negated guard terms such as
    # "do_not_monkey_patch" are required by the contract and must not fail scan.
    forbidden_patterns = (
        '"imports_v1": true',
        '"copies_v1_source": true',
        '"uses_v1_registry": true',
        '"uses_v1_executor": true',
        '"uses_v1_provider": true',
        '"monkey_patch_allowed": true',
        '"background_loop_allowed": true',
        'allow_monkey_patch',
        'allow_background_loop',
        'reuse_v1_registry": true',
    )
    for marker in forbidden_patterns:
        if marker in raw:
            issues.append(ContractValidationIssue("no_pollution", "P0", f"命中污染标记：{marker}"))
    return issues


def build_learning_asset_contract_guide_adapter():
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        guide = build_contract_guide()
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="R16 未来 Tool/Skill 统一资产契约指南已生成；后续自主学习和经验总结候选必须按该格式归一化与校验。",
            data=guide,
        )

    return adapter


def build_learning_asset_contract_normalize_adapter(
    bridge: LearningAssetContractBridge,
    experience: Any,
    skill_queue: Any,
    tool_requests: Any,
    descriptor_provider: Any,
):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            max_items = int(invocation.arguments.get("max_items") or 24)
            report = bridge.normalize(
                experience_report=experience.public_dict(),
                skill_queue=skill_queue.public_dict(),
                tool_requests=tool_requests.public_dict(),
                registry_descriptors=descriptor_provider(),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=max_items,
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"统一资产契约归一化失败：{exc}",
                error_code="learning_asset_contract_normalize_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return adapter


def build_learning_asset_contract_validate_adapter(bridge: LearningAssetContractBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        payload = invocation.arguments.get("contract") or invocation.arguments.get("payload")
        if isinstance(payload, str) and payload.strip():
            try:
                parsed = json.loads(payload)
                payload = parsed if isinstance(parsed, dict) else {"value": parsed}
            except json.JSONDecodeError:
                payload = {"raw": payload}
        if payload is not None and not isinstance(payload, dict):
            payload = {"value": payload}
        try:
            report = bridge.validate(payload)
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"统一资产契约校验失败：{exc}",
                error_code="learning_asset_contract_validate_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return adapter


def _contract_from_skill_candidate(item: dict[str, Any], *, source_kind: str) -> UnifiedLearningAssetContract:
    name = _safe_text(item.get("skill_name"), limit=140) or "unnamed_skill_candidate"
    purpose = _safe_text(item.get("purpose"), limit=900) or "待审阅 Skill 候选。"
    trigger = _safe_text(item.get("trigger_hint"), limit=320) or "经验沉淀命中可复用工作流。"
    source_ref = _safe_text(item.get("candidate_ref"), limit=220) or _ref("source", item)
    return UnifiedLearningAssetContract(
        asset_ref=_ref("asset_skill", source_ref, name, purpose),
        asset_kind="skill",
        namespace="skill.autonomous_learning",
        name=_slug_name(name),
        version="0.1.0-candidate",
        status="candidate_review_required",
        source_trace={"source_kind": source_kind, "source_ref": source_ref, "lesson_refs": _as_list(item.get("source_lesson_refs"))[:20]},
        purpose=purpose,
        trigger_rules=[trigger],
        input_contract={"input_type": "user_goal_or_runtime_evidence", "required": ["goal_or_evidence_summary"]},
        output_contract={"output_type": "LLM-readable workflow guidance", "required": ["steps", "next_action_hint", "validation_refs"]},
        runtime_binding={"binding_type": "SkillCandidate", "registry_write": False, "activation": False},
        usage_card=_usage_card("skill", name, trigger, purpose),
        chain_recipe=["read evidence", "apply Skill guidance", "select governed Runtime tools", "validate result", "handoff digest"],
        risk_profile=_risk_profile("A2_candidate"),
        validation_contract=_validation_contract(_as_list(item.get("validation_refs"))),
        rollback_contract=_rollback_contract(_as_list(item.get("rollback_refs"))),
        audit_contract=_audit_contract(source_ref),
        llm_policy=_llm_policy(),
        lifecycle=_lifecycle("candidate_review_required"),
    )


def _contract_from_skill_draft(item: dict[str, Any]) -> UnifiedLearningAssetContract:
    name = _safe_text(item.get("skill_name"), limit=140) or "unnamed_skill_draft"
    purpose = _safe_text(item.get("purpose"), limit=900) or "待审阅 Skill 草案版本。"
    trigger = _safe_text(item.get("trigger_hint"), limit=320) or "Skill 审阅队列触发。"
    source_ref = _safe_text(item.get("draft_ref"), limit=220) or _ref("skill_draft", item)
    return UnifiedLearningAssetContract(
        asset_ref=_ref("asset_skill_draft", source_ref, name, purpose),
        asset_kind="skill",
        namespace="skill.review_queue",
        name=_slug_name(name),
        version=_safe_text(item.get("version"), limit=60) or "0.1.0-draft",
        status="draft_review_queue",
        source_trace={"source_kind": "skill_review_queue.draft", "source_ref": source_ref, "candidate_ref": _safe_text(item.get("source_candidate_ref"), limit=220)},
        purpose=purpose,
        trigger_rules=[trigger],
        input_contract={"input_type": "LLM task context", "required": ["goal", "constraints", "evidence_refs"]},
        output_contract={"output_type": "Skill usage instructions", "required": ["usage_card", "chain_recipe", "validation_contract"]},
        runtime_binding={"binding_type": "SkillDraftVersion", "registry_write": False, "activation": False},
        usage_card=_usage_card("skill", name, trigger, purpose),
        chain_recipe=["review draft", "check trigger", "map to Runtime tool cards", "execute governed chain", "record outcome"],
        risk_profile=_risk_profile("A2_candidate"),
        validation_contract=_validation_contract(_as_list(item.get("validation_refs"))),
        rollback_contract=_rollback_contract(_as_list(item.get("rollback_refs"))),
        audit_contract=_audit_contract(source_ref),
        llm_policy=_llm_policy(),
        lifecycle=_lifecycle("draft_review_queue"),
    )


def _contract_from_tool_gap(item: dict[str, Any], *, source_kind: str) -> UnifiedLearningAssetContract:
    name = _safe_text(item.get("tool_gap_name"), limit=140) or "unnamed_tool_gap"
    purpose = _safe_text(item.get("capability_need"), limit=900) or "待审阅 Tool 缺口。"
    gov = _safe_text(item.get("governance_requirement"), limit=500) or "必须经沙箱、质量门、回滚和审计。"
    source_ref = _safe_text(item.get("candidate_ref"), limit=220) or _ref("tool_gap", item)
    return UnifiedLearningAssetContract(
        asset_ref=_ref("asset_tool_gap", source_ref, name, purpose),
        asset_kind="tool",
        namespace="tool.autonomous_learning",
        name=_slug_name(name),
        version="0.1.0-candidate",
        status="tool_gap_review_required",
        source_trace={"source_kind": source_kind, "source_ref": source_ref, "lesson_refs": _as_list(item.get("source_lesson_refs"))[:20]},
        purpose=purpose,
        trigger_rules=["现有 Runtime 工具无法稳定完成该能力缺口时触发。"],
        input_contract={"input_type": "ToolPackageCandidateSpec", "required": ["args_schema", "risk", "tests"]},
        output_contract={"output_type": "ToolResult", "required": ["status", "output_summary", "data", "error_code"]},
        runtime_binding={
            "binding_type": "ToolGapCandidate",
            "tool_registry_write": False,
            "tool_handle_release": False,
            "existing_sandbox_bridge": "L6.22 ToolProductionRequestBridge/SandboxValidationPlan",
            "sandbox_profile": "isolated_workspace_candidate_only",
            "sandbox_preflight_tool": "queue_tool_production_requests",
            "sandbox_alignment_tool": "learning_asset_sandbox_align",
        },
        usage_card=_usage_card("tool", name, "能力缺口命中且用户目标需要该工具。", purpose),
        chain_recipe=["confirm gap", "queue_tool_production_requests", "learning_asset_contract_normalize", "learning_asset_contract_validate", "learning_asset_sandbox_align", "learning_asset_sandbox_validate", "quality gate", "release with rollback evidence"],
        risk_profile=_risk_profile("A2_candidate/A3_future_sandbox", governance_requirement=gov),
        validation_contract=_validation_contract(_as_list(item.get("validation_refs"))),
        rollback_contract=_rollback_contract([]),
        audit_contract=_audit_contract(source_ref),
        llm_policy=_llm_policy(),
        lifecycle=_lifecycle("tool_gap_review_required"),
    )


def _contract_from_tool_request(item: dict[str, Any]) -> UnifiedLearningAssetContract:
    name = _safe_text(item.get("tool_name_hint"), limit=140) or "unnamed_tool_request"
    purpose = _safe_text(item.get("capability_need"), limit=900) or "Tool 生产请求。"
    gov = _safe_text(item.get("governance_requirement"), limit=500) or "必须经沙箱、质量门、回滚和审计。"
    source_ref = _safe_text(item.get("request_ref"), limit=220) or _ref("tool_request", item)
    return UnifiedLearningAssetContract(
        asset_ref=_ref("asset_tool_request", source_ref, name, purpose),
        asset_kind="tool",
        namespace="tool.production_request",
        name=_slug_name(name),
        version="0.1.0-request",
        status=_safe_text(item.get("status"), limit=80) or "request_ready",
        source_trace={"source_kind": "tool_production_request", "source_ref": source_ref, "candidate_ref": _safe_text(item.get("source_candidate_ref"), limit=220)},
        purpose=purpose,
        trigger_rules=["Tool 缺口已进入生产请求队列，但仍未生产/注册/释放。"],
        input_contract={"input_type": _safe_text(item.get("requested_interface"), limit=160) or "ToolPackageCandidateSpec", "required": ["args_schema", "risk", "tests", "audit"]},
        output_contract={"output_type": "ToolResult", "required": ["status", "output_summary", "data", "artifacts", "error_code"]},
        runtime_binding={
            "binding_type": "ToolProductionRequest",
            "tool_registry_write": False,
            "tool_handle_release": False,
            "existing_sandbox_bridge": "L6.22 ToolProductionRequestBridge/SandboxValidationPlan",
            "sandbox_profile": "isolated_workspace_candidate_only",
            "sandbox_preflight_tool": "queue_tool_production_requests",
            "sandbox_alignment_tool": "learning_asset_sandbox_align",
        },
        usage_card=_usage_card("tool", name, "审阅队列批准并进入未来沙箱生产时使用。", purpose),
        chain_recipe=["spec review", "learning_asset_sandbox_align", "learning_asset_sandbox_validate", "sandbox implement", "static scan", "smoke tests", "quality gate", "release gate", "runtime registration review"],
        risk_profile=_risk_profile(_safe_text(item.get("risk_level_hint"), limit=120) or "A2_request/A3_future_sandbox", governance_requirement=gov),
        validation_contract=_validation_contract(_as_list(item.get("validation_refs")) + _as_list(item.get("required_tests"))),
        rollback_contract=_rollback_contract(["rollback_evidence_required"]),
        audit_contract=_audit_contract(source_ref),
        llm_policy=_llm_policy(),
        lifecycle=_lifecycle(_safe_text(item.get("status"), limit=80) or "request_ready"),
    )


def _manual_contract(notes: str) -> UnifiedLearningAssetContract:
    note = _safe_text(notes, limit=700) or "手动统一资产契约规划。"
    return UnifiedLearningAssetContract(
        asset_ref=_ref("asset_manual", note),
        asset_kind="workflow",
        namespace="workflow.learning_asset_standard",
        name="manual_learning_asset_standardization",
        version="0.1.0-candidate",
        status="manual_candidate",
        source_trace={"source_kind": "manual_notes", "source_ref": _ref("manual", note)},
        purpose=note,
        trigger_rules=["用户要求统一未来自主学习和经验沉淀产生的 Tool/Skill 格式。"],
        input_contract={"input_type": "learning_or_experience_candidate", "required": REQUIRED_CONTRACT_FIELDS},
        output_contract={"output_type": "UnifiedLearningAssetContract", "required": REQUIRED_CONTRACT_FIELDS},
        runtime_binding={"binding_type": "contract_standard", "registry_write": False, "activation": False},
        usage_card=_usage_card("workflow", "manual_learning_asset_standardization", "未来资产候选入队前后均调用。", note),
        chain_recipe=["experience synthesis", "skill/tool queue", "normalize contract", "validate contract", "quality/release gate"],
        risk_profile=_risk_profile("A2_metadata"),
        validation_contract=_validation_contract(["contract_field_check", "usage_card_check", "no_pollution_check"]),
        rollback_contract=_rollback_contract(["candidate_drop_or_requeue"]),
        audit_contract=_audit_contract(_ref("manual", note)),
        llm_policy=_llm_policy(),
        lifecycle=_lifecycle("manual_candidate"),
    )


def _contract_from_dict(item: dict[str, Any]) -> UnifiedLearningAssetContract:
    return UnifiedLearningAssetContract(
        asset_ref=str(item.get("asset_ref") or _ref("asset", item)),
        asset_kind=str(item.get("asset_kind") or "workflow"),
        namespace=str(item.get("namespace") or "unknown"),
        name=str(item.get("name") or "unknown_asset"),
        version=str(item.get("version") or "0.1.0-candidate"),
        status=str(item.get("status") or "candidate_review_required"),
        source_trace=dict(item.get("source_trace") or {}),
        purpose=str(item.get("purpose") or ""),
        trigger_rules=[str(x) for x in _as_list(item.get("trigger_rules"))],
        input_contract=dict(item.get("input_contract") or {}),
        output_contract=dict(item.get("output_contract") or {}),
        runtime_binding=dict(item.get("runtime_binding") or {}),
        usage_card=dict(item.get("usage_card") or {}),
        chain_recipe=[str(x) for x in _as_list(item.get("chain_recipe"))],
        risk_profile=dict(item.get("risk_profile") or {}),
        validation_contract=dict(item.get("validation_contract") or {}),
        rollback_contract=dict(item.get("rollback_contract") or {}),
        audit_contract=dict(item.get("audit_contract") or {}),
        llm_policy=dict(item.get("llm_policy") or {}),
        lifecycle=dict(item.get("lifecycle") or {}),
    )


def _usage_card(kind: str, name: str, trigger: str, purpose: str) -> dict[str, str]:
    return {
        "title": _safe_text(name, limit=160),
        "asset_kind": kind,
        "when_to_use": _safe_text(trigger, limit=360) or "用户目标或 Runtime 证据命中该资产用途时使用。",
        "how_to_call": "先由 LLM 读取 usage_card 和 chain_recipe，再选择已注册 Runtime 工具；候选阶段不得直接调用未注册工具。",
        "do_not_use_when": "涉及 A5 高危、凭证、私钥、裸 shell/network、monkey patch、后台 loop、v1 源码/import/registry/executor/provider/self-iteration 复用时禁止。",
        "next_action_hint": "执行后进入 validation_contract；失败进入归因/回滚；通过后生成 handoff_digest。",
        "purpose": _safe_text(purpose, limit=420),
    }


def _risk_profile(level: str, *, governance_requirement: str = "") -> dict[str, Any]:
    return {
        "default_risk": _safe_text(level, limit=120),
        "a5_hard_block": True,
        "a0_a4_default_allow_with_audit": True,
        "governance_requirement": _safe_text(governance_requirement, limit=600) or "候选阶段只读元数据；真实生产必须经沙箱、质量门、发布门、回滚证据和审计。",
        "no_pollution": [
            "do_not_copy_v1_source",
            "do_not_import_v1",
            "do_not_reuse_v1_registry_executor_terminal_provider_self_iteration",
            "do_not_monkey_patch",
            "do_not_start_background_loop",
        ],
    }


def _validation_contract(refs: list[Any]) -> dict[str, Any]:
    normalized = [_safe_text(item, limit=220) for item in refs if _safe_text(item, limit=220)]
    return {
        "required": [
            "contract_field_check",
            "usage_card_check",
            "chain_recipe_check",
            "runtime_binding_check",
            "risk_profile_check",
            "no_pollution_scan",
            "quality_gate_before_activation",
            "l6_22_sandbox_alignment_before_tool_production",
        ],
        "evidence_refs": normalized[:20],
        "pass_condition": "learning_asset_contract_validate status=pass and zero P0/P1 issues before activation/release",
    }


def _rollback_contract(refs: list[Any]) -> dict[str, Any]:
    normalized = [_safe_text(item, limit=220) for item in refs if _safe_text(item, limit=220)]
    return {
        "strategy": "候选阶段可丢弃/重排/退回审阅；真实生产阶段必须提供 checkpoint/restore/manifest。",
        "required_refs": normalized[:20] or ["rollback_evidence_required_before_release"],
    }


def _audit_contract(source_ref: str) -> dict[str, Any]:
    return {
        "source_ref": _safe_text(source_ref, limit=220),
        "required_events": ["candidate_created", "contract_normalized", "contract_validated", "quality_gate", "release_gate"],
        "redaction_required": True,
    }


def _llm_policy() -> dict[str, Any]:
    return {
        "llm_is_final_decider": True,
        "planner_is_advisor_only": True,
        "subagents_evidence_only": True,
        "tool_executes_only_via_runtime": True,
        "activation_requires_explicit_llm_decision": True,
    }


def _lifecycle(status: str) -> dict[str, Any]:
    return {
        "current_status": _safe_text(status, limit=100),
        "allowed_transitions": [
            "candidate_review_required",
            "draft_review_queue",
            "sandbox_spec_review",
            "sandbox_validation",
            "quality_gate_review",
            "release_gate_review",
            "runtime_registration_review",
            "active",
            "retired",
        ],
        "default_next_action": "learning_asset_contract_validate_then_learning_asset_sandbox_validate_for_tool_assets",
    }


def _build_report_summary(contracts: list[UnifiedLearningAssetContract], issues: list[ContractValidationIssue], source_counts: dict[str, int]) -> str:
    if not contracts:
        return "当前没有可归一化的 Skill/Tool 候选；已返回未来强制契约与执行策略。"
    kinds: dict[str, int] = {}
    for item in contracts:
        kinds[item.asset_kind] = kinds.get(item.asset_kind, 0) + 1
    return (
        "已将现有经验候选、Skill 草案、Tool 请求归一为同一资产契约；"
        f"kinds={kinds}；source_counts={source_counts}；"
        f"validation_issues={len(issues)}。未来新资产必须先 normalize 再 validate。"
    )


def _dedupe_contracts(contracts: list[UnifiedLearningAssetContract]) -> list[UnifiedLearningAssetContract]:
    seen: set[str] = set()
    result: list[UnifiedLearningAssetContract] = []
    for item in contracts:
        key = f"{item.asset_kind}:{item.namespace}:{item.name}:{item.purpose}"
        if key in seen:
            continue
        seen.add(key)
        result.append(item)
    return result


def _safe_text(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    text = SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    for word in SENSITIVE_WORDS:
        text = re.sub(re.escape(word), f"{word[:2]}***", text, flags=re.IGNORECASE)
    return text.replace("\x00", "").strip()[:limit]


def _safe_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    raw = json.dumps(value, ensure_ascii=False, default=str)
    safe = _safe_text(raw, limit=8000)
    try:
        parsed = json.loads(safe)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {"summary": safe[:1000]}


def _as_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value in (None, ""):
        return []
    return [value]


def _ref(prefix: str, *parts: Any) -> str:
    material = "|".join(_safe_text(part, limit=800) for part in parts)
    digest = hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:r16_{digest}"


def _slug_name(value: str) -> str:
    text = _safe_text(value, limit=140).lower()
    text = re.sub(r"[^0-9a-zA-Z_\u4e00-\u9fff]+", "_", text).strip("_")
    return text or "unnamed_asset"
