"""L6.38 P0 系统接入一：Provider / Budget / Skill / Handoff。

本模块只在 ``tiangong_agent_runtime`` 外壳层工作，把四个 P0 系统的输出压缩为
Planner 可消费的 ``Hint / Ticket / Envelope / Evidence / Report``。所有入口都以
Runtime 工具注册的方式接入，真实执行仍由 ``PlannerExecutionController``、
``LongChainRunner``、``ExecutionSpine``、``PermitGateway`` 和 ``AuditBridge`` 负责。

边界：
- 不修改 ``tiangong_kernel``；
- 不新增第二 Runtime；
- 不直接调用 provider SDK / 网络；
- 不读取凭证明文；
- 不直接注册或激活 Skill；
- 不自动派生子任务；
- 不直接修改预算，只生成预算账本与续租建议。
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any, Iterable

from tiangong_agent_shell.safe_logging import redact_text

from .tool_invocation import ToolInvocation
from .tool_result import ToolResult, ToolResultStatus
from .turn_context import TurnContext

L6_38_SCHEMA = "tiangong.l6_38.p0_system_integration.v1"
L6_38_SOURCE_VERSION = "L6.38-P0-provider-budget-skill-handoff"
PROVIDER_IDS = ("deepseek_v4", "mimo", "glm_5_1", "minimax_m3", "gpt_5_5")
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)


@dataclass(frozen=True)
class CredentialRef:
    """凭证只读引用。只保存句柄，不保存、不读取、不展开密钥。"""

    ref_id: str
    provider_id: str
    scope: str = "provider_runtime"
    source: str = "config_or_secret_manager_handle"
    plaintext_available: bool = False
    read_attempted: bool = False
    value_preview: str = "<redacted>"

    def __post_init__(self) -> None:
        if self.provider_id not in PROVIDER_IDS:
            raise ValueError(f"unsupported provider_id: {self.provider_id}")
        if self.plaintext_available or self.read_attempted:
            raise ValueError("CredentialRef cannot expose or read plaintext credentials")
        rendered = repr(self.public_dict()).lower()
        if "mockkey_" in rendered or "bearer " in rendered or "secret=" in rendered:
            raise ValueError("CredentialRef cannot contain plaintext secret material")

    def public_dict(self) -> dict[str, Any]:
        return {
            "ref_id": self.ref_id,
            "provider_id": self.provider_id,
            "scope": self.scope,
            "source": self.source,
            "plaintext_available": self.plaintext_available,
            "read_attempted": self.read_attempted,
            "value_preview": self.value_preview,
        }


@dataclass(frozen=True)
class ProviderProfile:
    """L6.38 ProviderProfile：面向执行链的最小画像。"""

    provider_id: str
    display_name: str
    default_model_id: str
    supported_surfaces: list[str] = field(default_factory=list)
    credential_ref: CredentialRef | None = None
    dry_run_supported: bool = True
    sample_replay_supported: bool = True
    real_call_supported_by_runtime: bool = True
    plugin_sdk_call_allowed: bool = False
    direct_network_call_allowed: bool = False
    disabled_without_ticket: bool = True

    def __post_init__(self) -> None:
        if self.provider_id not in PROVIDER_IDS:
            raise ValueError(f"unsupported provider_id: {self.provider_id}")
        if self.plugin_sdk_call_allowed or self.direct_network_call_allowed:
            raise ValueError("ProviderProfile forbids plugin SDK calls and direct network calls")
        if not (self.dry_run_supported and self.sample_replay_supported and self.disabled_without_ticket):
            raise ValueError("ProviderProfile must keep dry-run/sample-replay/ticket gating enabled")

    def public_dict(self) -> dict[str, Any]:
        return {
            "provider_id": self.provider_id,
            "display_name": self.display_name,
            "default_model_id": self.default_model_id,
            "supported_surfaces": list(self.supported_surfaces),
            "credential_ref": self.credential_ref.public_dict() if self.credential_ref else None,
            "dry_run_supported": self.dry_run_supported,
            "sample_replay_supported": self.sample_replay_supported,
            "real_call_supported_by_runtime": self.real_call_supported_by_runtime,
            "plugin_sdk_call_allowed": self.plugin_sdk_call_allowed,
            "direct_network_call_allowed": self.direct_network_call_allowed,
            "disabled_without_ticket": self.disabled_without_ticket,
        }


@dataclass(frozen=True)
class ProviderExecutionTicket:
    """Provider 执行票据。票据可以被 Planner 消费，但不能绕过 Runtime 执行链。"""

    ticket_id: str
    provider_id: str
    profile_ref: str
    credential_ref: CredentialRef
    request_kind: str = "plan_smoke"
    requested_call_mode: str = "dry_run"
    effective_call_mode: str = "sample_replay"
    smoke_case_id: str = "deepseek_plan_shape_sample_replay"
    fallback_mode: str = "rule_only_or_sample_replay"
    planner_consumable: bool = True
    requires_runtime_governance: bool = True
    requires_l5_permit_for_real_call: bool = True
    real_call_attempted: bool = False
    credential_plaintext_read: bool = False
    imports_provider_sdk: bool = False
    direct_provider_call: bool = False
    plugin_direct_call: bool = False

    def __post_init__(self) -> None:
        if self.provider_id not in PROVIDER_IDS:
            raise ValueError(f"unsupported provider_id: {self.provider_id}")
        required = (self.planner_consumable, self.requires_runtime_governance, self.requires_l5_permit_for_real_call)
        if not all(required):
            raise ValueError("ProviderExecutionTicket must be planner-consumable and runtime-governed")
        forbidden = (
            self.real_call_attempted,
            self.credential_plaintext_read,
            self.imports_provider_sdk,
            self.direct_provider_call,
            self.plugin_direct_call,
        )
        if any(forbidden):
            raise ValueError("ProviderExecutionTicket cannot call provider/read credentials/import SDK/bypass runtime")

    def public_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "provider_id": self.provider_id,
            "profile_ref": self.profile_ref,
            "credential_ref": self.credential_ref.public_dict(),
            "request_kind": self.request_kind,
            "requested_call_mode": self.requested_call_mode,
            "effective_call_mode": self.effective_call_mode,
            "smoke_case_id": self.smoke_case_id,
            "fallback_mode": self.fallback_mode,
            "planner_consumable": self.planner_consumable,
            "requires_runtime_governance": self.requires_runtime_governance,
            "requires_l5_permit_for_real_call": self.requires_l5_permit_for_real_call,
            "real_call_attempted": self.real_call_attempted,
            "credential_plaintext_read": self.credential_plaintext_read,
            "imports_provider_sdk": self.imports_provider_sdk,
            "direct_provider_call": self.direct_provider_call,
            "plugin_direct_call": self.plugin_direct_call,
        }


@dataclass(frozen=True)
class ProviderIntegrationEnvelope:
    """Provider 系统给 Planner 的 Envelope。"""

    envelope_id: str
    provider_profiles: list[ProviderProfile]
    execution_tickets: list[ProviderExecutionTicket]
    smoke_result: dict[str, Any]
    fallback_reason: str = "no_live_credential_or_permit; sample_replay_used"
    report_digest: str = ""
    no_sdk_import: bool = True
    no_plain_secret: bool = True
    no_direct_network_call: bool = True
    no_second_runtime: bool = True

    def __post_init__(self) -> None:
        if not (self.no_sdk_import and self.no_plain_secret and self.no_direct_network_call and self.no_second_runtime):
            raise ValueError("ProviderIntegrationEnvelope boundary flags must remain true")
        if not self.provider_profiles or not self.execution_tickets:
            raise ValueError("ProviderIntegrationEnvelope requires profiles and tickets")

    def public_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "provider_profiles": [item.public_dict() for item in self.provider_profiles],
            "execution_tickets": [item.public_dict() for item in self.execution_tickets],
            "smoke_result": dict(self.smoke_result),
            "fallback_reason": self.fallback_reason,
            "report_digest": self.report_digest,
            "no_sdk_import": self.no_sdk_import,
            "no_plain_secret": self.no_plain_secret,
            "no_direct_network_call": self.no_direct_network_call,
            "no_second_runtime": self.no_second_runtime,
        }


@dataclass(frozen=True)
class StepBudgetLedger:
    """单步预算账本。只记录建议，不直接扣费。"""

    ledger_id: str
    max_steps: int
    planned_steps: int
    executed_steps_seen: int = 0
    remaining_steps: int = 0
    exhausted: bool = False
    planner_consumable: bool = True
    mutates_budget: bool = False
    blocks_a0_to_a4_by_default: bool = False

    def __post_init__(self) -> None:
        if self.max_steps < 0 or self.planned_steps < 0 or self.remaining_steps < 0:
            raise ValueError("budget counts must be non-negative")
        if self.mutates_budget or self.blocks_a0_to_a4_by_default:
            raise ValueError("StepBudgetLedger cannot mutate budget or block A0-A4 by default")
        if not self.planner_consumable:
            raise ValueError("StepBudgetLedger must remain planner-consumable")

    def public_dict(self) -> dict[str, Any]:
        return {
            "ledger_id": self.ledger_id,
            "max_steps": self.max_steps,
            "planned_steps": self.planned_steps,
            "executed_steps_seen": self.executed_steps_seen,
            "remaining_steps": self.remaining_steps,
            "exhausted": self.exhausted,
            "planner_consumable": self.planner_consumable,
            "mutates_budget": self.mutates_budget,
            "blocks_a0_to_a4_by_default": self.blocks_a0_to_a4_by_default,
        }


@dataclass(frozen=True)
class ChainBudgetLease:
    lease_id: str
    owner_chain_id: str
    lease_kind: str = "long_chain_execution"
    current_limit: int = 20
    requested_extension: int = 0
    renewal_recommended: bool = False
    renewal_reason: str = ""
    confirmation_required_for_extension: bool = False
    planner_hint: str = ""
    mutates_budget: bool = False

    def __post_init__(self) -> None:
        if self.current_limit < 0 or self.requested_extension < 0:
            raise ValueError("ChainBudgetLease limits must be non-negative")
        if self.mutates_budget:
            raise ValueError("ChainBudgetLease cannot mutate budget directly")

    def public_dict(self) -> dict[str, Any]:
        return {
            "lease_id": self.lease_id,
            "owner_chain_id": self.owner_chain_id,
            "lease_kind": self.lease_kind,
            "current_limit": self.current_limit,
            "requested_extension": self.requested_extension,
            "renewal_recommended": self.renewal_recommended,
            "renewal_reason": self.renewal_reason,
            "confirmation_required_for_extension": self.confirmation_required_for_extension,
            "planner_hint": self.planner_hint,
            "mutates_budget": self.mutates_budget,
        }


@dataclass(frozen=True)
class TimeoutBudget:
    timeout_id: str
    default_timeout_seconds: float
    remaining_timeout_seconds: float
    timeout_risk: str = "normal"
    degradation_action: str = "none"
    blocks_execution: bool = False

    def __post_init__(self) -> None:
        if self.default_timeout_seconds < 0 or self.remaining_timeout_seconds < 0:
            raise ValueError("TimeoutBudget values must be non-negative")
        if self.blocks_execution and self.degradation_action == "none":
            raise ValueError("TimeoutBudget can block only with a degradation action")

    def public_dict(self) -> dict[str, Any]:
        return {
            "timeout_id": self.timeout_id,
            "default_timeout_seconds": self.default_timeout_seconds,
            "remaining_timeout_seconds": self.remaining_timeout_seconds,
            "timeout_risk": self.timeout_risk,
            "degradation_action": self.degradation_action,
            "blocks_execution": self.blocks_execution,
        }


@dataclass(frozen=True)
class FailureBudget:
    failure_budget_id: str
    max_failures: int = 1
    observed_failures: int = 0
    remaining_failures: int = 1
    exhausted: bool = False
    recommended_action: str = "continue"
    blocks_a0_to_a4_by_default: bool = False

    def __post_init__(self) -> None:
        if min(self.max_failures, self.observed_failures, self.remaining_failures) < 0:
            raise ValueError("FailureBudget counts must be non-negative")
        if self.blocks_a0_to_a4_by_default:
            raise ValueError("FailureBudget cannot block A0-A4 by default")

    def public_dict(self) -> dict[str, Any]:
        return {
            "failure_budget_id": self.failure_budget_id,
            "max_failures": self.max_failures,
            "observed_failures": self.observed_failures,
            "remaining_failures": self.remaining_failures,
            "exhausted": self.exhausted,
            "recommended_action": self.recommended_action,
            "blocks_a0_to_a4_by_default": self.blocks_a0_to_a4_by_default,
        }


@dataclass(frozen=True)
class BudgetSnapshot:
    snapshot_id: str
    step_ledger: StepBudgetLedger
    chain_lease: ChainBudgetLease
    timeout_budget: TimeoutBudget
    failure_budget: FailureBudget
    planner_budget_hint: str
    resource_exhausted: bool = False
    downgrade_required: bool = False
    hard_block_reason: str = ""
    mutates_budget: bool = False
    direct_execution_now: bool = False

    def __post_init__(self) -> None:
        if self.mutates_budget or self.direct_execution_now:
            raise ValueError("BudgetSnapshot cannot mutate budget or execute")
        if self.resource_exhausted and not self.hard_block_reason:
            raise ValueError("BudgetSnapshot must explain resource exhaustion")

    def public_dict(self) -> dict[str, Any]:
        return {
            "snapshot_id": self.snapshot_id,
            "step_ledger": self.step_ledger.public_dict(),
            "chain_lease": self.chain_lease.public_dict(),
            "timeout_budget": self.timeout_budget.public_dict(),
            "failure_budget": self.failure_budget.public_dict(),
            "planner_budget_hint": self.planner_budget_hint,
            "resource_exhausted": self.resource_exhausted,
            "downgrade_required": self.downgrade_required,
            "hard_block_reason": self.hard_block_reason,
            "mutates_budget": self.mutates_budget,
            "direct_execution_now": self.direct_execution_now,
        }


@dataclass(frozen=True)
class SkillCandidateRoute:
    route_id: str
    source_draft_ref: str
    skill_name: str
    purpose: str
    planner_hint: str
    draft_consumable_by_planner: bool = True
    can_execute_as_draft: bool = False
    writes_skill_registry: bool = False
    activates_skill: bool = False

    def __post_init__(self) -> None:
        if not self.draft_consumable_by_planner:
            raise ValueError("SkillCandidateRoute must be planner-consumable")
        if self.can_execute_as_draft or self.writes_skill_registry or self.activates_skill:
            raise ValueError("SkillCandidateRoute cannot execute, write registry, or activate skill")

    def public_dict(self) -> dict[str, Any]:
        return {
            "route_id": self.route_id,
            "source_draft_ref": self.source_draft_ref,
            "skill_name": self.skill_name,
            "purpose": self.purpose,
            "planner_hint": self.planner_hint,
            "draft_consumable_by_planner": self.draft_consumable_by_planner,
            "can_execute_as_draft": self.can_execute_as_draft,
            "writes_skill_registry": self.writes_skill_registry,
            "activates_skill": self.activates_skill,
        }


@dataclass(frozen=True)
class SkillReviewTicket:
    ticket_id: str
    route_id: str
    review_policy: str = "quality_gate_plus_human_confirmation_before_activation"
    activation_requires_strong_confirmation: bool = True
    registers_skill: bool = False
    activates_skill: bool = False
    releases_tool_group: bool = False

    def __post_init__(self) -> None:
        if not self.activation_requires_strong_confirmation:
            raise ValueError("SkillReviewTicket must require strong confirmation before activation")
        if self.registers_skill or self.activates_skill or self.releases_tool_group:
            raise ValueError("SkillReviewTicket cannot register/activate/release")

    def public_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "route_id": self.route_id,
            "review_policy": self.review_policy,
            "activation_requires_strong_confirmation": self.activation_requires_strong_confirmation,
            "registers_skill": self.registers_skill,
            "activates_skill": self.activates_skill,
            "releases_tool_group": self.releases_tool_group,
        }


@dataclass(frozen=True)
class SkillActivationIntent:
    intent_id: str
    ticket_id: str
    target_skill_name: str
    activation_state: str = "intent_only"
    formal_activation_allowed_now: bool = False
    requires_quality_gate: bool = True
    requires_rollback_evidence: bool = True
    requires_human_confirmation: bool = True

    def __post_init__(self) -> None:
        if self.activation_state != "intent_only" or self.formal_activation_allowed_now:
            raise ValueError("SkillActivationIntent must remain intent-only")
        if not (self.requires_quality_gate and self.requires_rollback_evidence and self.requires_human_confirmation):
            raise ValueError("Skill activation requires quality gate, rollback evidence and human confirmation")

    def public_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "ticket_id": self.ticket_id,
            "target_skill_name": self.target_skill_name,
            "activation_state": self.activation_state,
            "formal_activation_allowed_now": self.formal_activation_allowed_now,
            "requires_quality_gate": self.requires_quality_gate,
            "requires_rollback_evidence": self.requires_rollback_evidence,
            "requires_human_confirmation": self.requires_human_confirmation,
        }


@dataclass(frozen=True)
class SkillExecutionHint:
    hint_id: str
    route_id: str
    skill_name: str
    hint_text: str
    planner_consumable: bool = True
    maps_to_existing_tools_only: bool = True
    direct_tool_release: bool = False
    bypasses_governance: bool = False

    def __post_init__(self) -> None:
        if not (self.planner_consumable and self.maps_to_existing_tools_only):
            raise ValueError("SkillExecutionHint must be planner-consumable and map to existing tools only")
        if self.direct_tool_release or self.bypasses_governance:
            raise ValueError("SkillExecutionHint cannot release tools directly or bypass governance")

    def public_dict(self) -> dict[str, Any]:
        return {
            "hint_id": self.hint_id,
            "route_id": self.route_id,
            "skill_name": self.skill_name,
            "hint_text": self.hint_text,
            "planner_consumable": self.planner_consumable,
            "maps_to_existing_tools_only": self.maps_to_existing_tools_only,
            "direct_tool_release": self.direct_tool_release,
            "bypasses_governance": self.bypasses_governance,
        }


@dataclass(frozen=True)
class SkillIntegrationEnvelope:
    envelope_id: str
    candidate_routes: list[SkillCandidateRoute]
    review_tickets: list[SkillReviewTicket]
    activation_intents: list[SkillActivationIntent]
    execution_hints: list[SkillExecutionHint]
    report_digest: str = ""
    planner_consumable: bool = True
    writes_skill_registry: bool = False
    activates_skill: bool = False
    releases_tool: bool = False

    def __post_init__(self) -> None:
        if not self.planner_consumable:
            raise ValueError("SkillIntegrationEnvelope must be planner-consumable")
        if self.writes_skill_registry or self.activates_skill or self.releases_tool:
            raise ValueError("SkillIntegrationEnvelope cannot write/activate/release")

    def public_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "candidate_routes": [item.public_dict() for item in self.candidate_routes],
            "review_tickets": [item.public_dict() for item in self.review_tickets],
            "activation_intents": [item.public_dict() for item in self.activation_intents],
            "execution_hints": [item.public_dict() for item in self.execution_hints],
            "report_digest": self.report_digest,
            "planner_consumable": self.planner_consumable,
            "writes_skill_registry": self.writes_skill_registry,
            "activates_skill": self.activates_skill,
            "releases_tool": self.releases_tool,
        }


@dataclass(frozen=True)
class SubtaskTicket:
    ticket_id: str
    parent_chain_id: str
    subtask_title: str
    payload_summary: str
    status: str = "proposed"
    human_confirmation_required_for_spawn: bool = True
    auto_spawn_allowed: bool = False
    recursive_spawn_allowed: bool = False
    direct_execution_now: bool = False

    def __post_init__(self) -> None:
        if not self.human_confirmation_required_for_spawn:
            raise ValueError("SubtaskTicket requires human confirmation before spawn")
        if self.auto_spawn_allowed or self.recursive_spawn_allowed or self.direct_execution_now:
            raise ValueError("SubtaskTicket cannot auto-spawn, recursively spawn, or execute")

    def public_dict(self) -> dict[str, Any]:
        return {
            "ticket_id": self.ticket_id,
            "parent_chain_id": self.parent_chain_id,
            "subtask_title": self.subtask_title,
            "payload_summary": self.payload_summary,
            "status": self.status,
            "human_confirmation_required_for_spawn": self.human_confirmation_required_for_spawn,
            "auto_spawn_allowed": self.auto_spawn_allowed,
            "recursive_spawn_allowed": self.recursive_spawn_allowed,
            "direct_execution_now": self.direct_execution_now,
        }


@dataclass(frozen=True)
class HandoffEnvelope:
    envelope_id: str
    parent_chain_id: str
    subtask_tickets: list[SubtaskTicket]
    return_channel: str = "parent_chain_collect_report"
    planner_consumable: bool = True
    child_must_return_to_parent: bool = True
    auto_recursive_spawn_allowed: bool = False
    direct_child_execution: bool = False

    def __post_init__(self) -> None:
        if not (self.planner_consumable and self.child_must_return_to_parent):
            raise ValueError("HandoffEnvelope must be planner-consumable and parent-returning")
        if self.auto_recursive_spawn_allowed or self.direct_child_execution:
            raise ValueError("HandoffEnvelope cannot auto-recursively spawn or execute child tasks")

    def public_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "parent_chain_id": self.parent_chain_id,
            "subtask_tickets": [item.public_dict() for item in self.subtask_tickets],
            "return_channel": self.return_channel,
            "planner_consumable": self.planner_consumable,
            "child_must_return_to_parent": self.child_must_return_to_parent,
            "auto_recursive_spawn_allowed": self.auto_recursive_spawn_allowed,
            "direct_child_execution": self.direct_child_execution,
        }


@dataclass(frozen=True)
class ParentChainCollectReport:
    report_id: str
    parent_chain_id: str
    collected_ticket_ids: list[str]
    unresolved_ticket_ids: list[str]
    suggested_parent_steps: list[str]
    all_children_returned: bool = False
    merges_without_review: bool = False
    spawns_followup_agent: bool = False

    def __post_init__(self) -> None:
        if self.merges_without_review or self.spawns_followup_agent:
            raise ValueError("ParentChainCollectReport cannot merge without review or spawn follow-up agent")

    def public_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "parent_chain_id": self.parent_chain_id,
            "collected_ticket_ids": list(self.collected_ticket_ids),
            "unresolved_ticket_ids": list(self.unresolved_ticket_ids),
            "suggested_parent_steps": list(self.suggested_parent_steps),
            "all_children_returned": self.all_children_returned,
            "merges_without_review": self.merges_without_review,
            "spawns_followup_agent": self.spawns_followup_agent,
        }


@dataclass(frozen=True)
class HandoffIntegrationEnvelope:
    envelope_id: str
    handoff_envelope: HandoffEnvelope
    parent_collect_report: ParentChainCollectReport
    report_digest: str = ""
    planner_consumable: bool = True
    no_auto_recursive_spawn: bool = True
    parent_chain_required: bool = True
    direct_execution_now: bool = False

    def __post_init__(self) -> None:
        if not (self.planner_consumable and self.no_auto_recursive_spawn and self.parent_chain_required):
            raise ValueError("HandoffIntegrationEnvelope boundary flags must remain true")
        if self.direct_execution_now:
            raise ValueError("HandoffIntegrationEnvelope cannot execute")

    def public_dict(self) -> dict[str, Any]:
        return {
            "envelope_id": self.envelope_id,
            "handoff_envelope": self.handoff_envelope.public_dict(),
            "parent_collect_report": self.parent_collect_report.public_dict(),
            "report_digest": self.report_digest,
            "planner_consumable": self.planner_consumable,
            "no_auto_recursive_spawn": self.no_auto_recursive_spawn,
            "parent_chain_required": self.parent_chain_required,
            "direct_execution_now": self.direct_execution_now,
        }


@dataclass(frozen=True)
class L638P0IntegrationReport:
    """四系统接入总报告。"""

    schema: str
    generated_at: float
    status: str
    summary: str
    provider: ProviderIntegrationEnvelope | None = None
    budget: BudgetSnapshot | None = None
    skill: SkillIntegrationEnvelope | None = None
    handoff: HandoffIntegrationEnvelope | None = None
    report_digest: str = ""
    planner_consumable: bool = True
    runtime_governed: bool = True
    uses_planner_execution_controller: bool = True
    no_second_runtime: bool = True
    no_kernel_mutation: bool = True
    no_provider_sdk_call: bool = True
    no_plain_secret: bool = True
    no_skill_activation: bool = True
    no_auto_recursive_handoff: bool = True
    no_direct_budget_mutation: bool = True

    def __post_init__(self) -> None:
        required = (
            self.planner_consumable,
            self.runtime_governed,
            self.uses_planner_execution_controller,
            self.no_second_runtime,
            self.no_kernel_mutation,
            self.no_provider_sdk_call,
            self.no_plain_secret,
            self.no_skill_activation,
            self.no_auto_recursive_handoff,
            self.no_direct_budget_mutation,
        )
        if not all(required):
            raise ValueError("L6.38 P0 report boundary flags must remain true")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "source_version": L6_38_SOURCE_VERSION,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "provider": self.provider.public_dict() if self.provider else None,
            "budget": self.budget.public_dict() if self.budget else None,
            "skill": self.skill.public_dict() if self.skill else None,
            "handoff": self.handoff.public_dict() if self.handoff else None,
            "report_digest": self.report_digest,
            "planner_consumable": self.planner_consumable,
            "runtime_governed": self.runtime_governed,
            "uses_planner_execution_controller": self.uses_planner_execution_controller,
            "no_second_runtime": self.no_second_runtime,
            "no_kernel_mutation": self.no_kernel_mutation,
            "no_provider_sdk_call": self.no_provider_sdk_call,
            "no_plain_secret": self.no_plain_secret,
            "no_skill_activation": self.no_skill_activation,
            "no_auto_recursive_handoff": self.no_auto_recursive_handoff,
            "no_direct_budget_mutation": self.no_direct_budget_mutation,
        }

    def summary_text(self) -> str:
        provider_ready = self.provider is not None
        budget_ready = self.budget is not None
        skill_ready = self.skill is not None
        handoff_ready = self.handoff is not None
        return (
            "L6.38 P0 系统接入："
            f"status={self.status}；provider={provider_ready}；budget={budget_ready}；"
            f"skill={skill_ready}；handoff={handoff_ready}；"
            "已接入 PlannerExecutionController 统一执行链，不新增 Runtime，不改内核。"
        )

    def markdown_report(self) -> str:
        payload = self.public_dict()
        lines = [
            "# 临渊者 L6.38 P0 系统接入报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- digest: `{self.report_digest}`",
            f"- runtime_governed: `{self.runtime_governed}`",
            f"- uses_planner_execution_controller: `{self.uses_planner_execution_controller}`",
            f"- no_kernel_mutation: `{self.no_kernel_mutation}`",
            "",
            "## 四系统状态",
            "",
            f"- Provider: `{payload['provider']['envelope_id'] if payload.get('provider') else 'missing'}`",
            f"- Budget: `{payload['budget']['snapshot_id'] if payload.get('budget') else 'missing'}`",
            f"- Skill: `{payload['skill']['envelope_id'] if payload.get('skill') else 'missing'}`",
            f"- Handoff: `{payload['handoff']['envelope_id'] if payload.get('handoff') else 'missing'}`",
            "",
            "## 硬边界",
            "",
            "- Provider 不裸调 SDK，不读取明文凭证；无真实凭证/许可时降级为 sample replay。",
            "- Budget 只生成账本、快照和续租建议，不直接扣费，不默认阻断 A0-A4。",
            "- Skill 只生成候选路由、审阅票据、激活意图和执行提示；正式激活必须强确认。",
            "- Handoff 只生成子任务票据和父链回流报告；禁止自动递归派生。",
        ]
        return "\n".join(lines)


class L638P0SystemIntegrationBridge:
    """L6.38 四系统接入桥。"""

    def __init__(self) -> None:
        self.provider: ProviderIntegrationEnvelope | None = None
        self.budget: BudgetSnapshot | None = None
        self.skill: SkillIntegrationEnvelope | None = None
        self.handoff: HandoffIntegrationEnvelope | None = None
        self._last_report: L638P0IntegrationReport | None = None

    @property
    def last_report(self) -> L638P0IntegrationReport | None:
        return self._last_report

    def reset(self) -> None:
        self.provider = None
        self.budget = None
        self.skill = None
        self.handoff = None
        self._last_report = None

    def build_provider(
        self,
        *,
        provider_report: dict[str, Any] | None = None,
        notes: str = "",
        requested_call_mode: str = "dry_run",
    ) -> ProviderIntegrationEnvelope:
        report = provider_report or {}
        provider_items = report.get("provider_profiles") if isinstance(report, dict) else None
        profiles: list[ProviderProfile] = []
        if isinstance(provider_items, list) and provider_items:
            for item in provider_items[:5]:
                if not isinstance(item, dict):
                    continue
                provider_id = _normalize_provider_id(item.get("provider_id"))
                if provider_id not in PROVIDER_IDS:
                    continue
                credential = CredentialRef(ref_id=f"credential_ref:{provider_id}:runtime", provider_id=provider_id)
                surfaces = _surface_hints(provider_id, report)
                profiles.append(
                    ProviderProfile(
                        provider_id=provider_id,
                        display_name=_safe_text(item.get("display_name"), 80) or provider_id,
                        default_model_id=_safe_text(item.get("default_model_id"), 120) or provider_id,
                        supported_surfaces=surfaces,
                        credential_ref=credential,
                    )
                )
        if not profiles:
            profiles = _default_provider_profiles()

        deepseek = next((item for item in profiles if item.provider_id == "deepseek_v4"), profiles[0])
        ticket = ProviderExecutionTicket(
            ticket_id=_ref("provider_ticket", deepseek.provider_id, requested_call_mode, notes),
            provider_id=deepseek.provider_id,
            profile_ref=_ref("provider_profile", deepseek.provider_id, deepseek.default_model_id),
            credential_ref=deepseek.credential_ref or CredentialRef(ref_id="credential_ref:deepseek_v4:runtime", provider_id="deepseek_v4"),
            requested_call_mode=_safe_text(requested_call_mode, 40) or "dry_run",
            effective_call_mode="sample_replay" if _safe_text(requested_call_mode, 40) != "real_call_permitted" else "dry_run_pending_l5_permit",
        )
        smoke = {
            "case_id": ticket.smoke_case_id,
            "provider_id": ticket.provider_id,
            "mode": ticket.effective_call_mode,
            "sample_replay_ok": True,
            "real_call_attempted": False,
            "fallback_to_rule_only_available": True,
            "summary": "DeepSeek plan-shape smoke 使用离线样本回放；未读取凭证，未触网。",
        }
        envelope = ProviderIntegrationEnvelope(
            envelope_id=_ref("provider_envelope", [p.provider_id for p in profiles], notes),
            provider_profiles=profiles,
            execution_tickets=[ticket],
            smoke_result=smoke,
            fallback_reason="missing_l5_permit_or_live_credential; sample_replay_used",
        )
        envelope = ProviderIntegrationEnvelope(
            envelope_id=envelope.envelope_id,
            provider_profiles=envelope.provider_profiles,
            execution_tickets=envelope.execution_tickets,
            smoke_result=envelope.smoke_result,
            fallback_reason=envelope.fallback_reason,
            report_digest=stable_l6_38_digest(envelope.public_dict()),
        )
        self.provider = envelope
        self._last_report = self._build_report()
        return envelope

    def build_budget(
        self,
        *,
        planner_execution_report: dict[str, Any] | None = None,
        max_steps: int = 20,
        planned_steps: int = 0,
        notes: str = "",
    ) -> BudgetSnapshot:
        source = planner_execution_report or {}
        executed = int(source.get("executed_steps") or 0) if isinstance(source, dict) else 0
        failures = int(source.get("failed_steps") or source.get("timeout_steps") or 0) if isinstance(source, dict) else 0
        max_steps = max(0, int(max_steps))
        planned_steps = max(0, int(planned_steps or source.get("total_steps") or 0))
        remaining = max(0, max_steps - max(planned_steps, executed))
        exhausted = max_steps > 0 and remaining == 0 and planned_steps >= max_steps
        needs_renewal = planned_steps >= max_steps or (max_steps > 0 and remaining <= max(1, max_steps // 10))
        requested_extension = max(0, planned_steps - max_steps) if planned_steps > max_steps else (5 if needs_renewal else 0)
        ledger = StepBudgetLedger(
            ledger_id=_ref("step_budget_ledger", max_steps, planned_steps, executed, notes),
            max_steps=max_steps,
            planned_steps=planned_steps,
            executed_steps_seen=executed,
            remaining_steps=remaining,
            exhausted=exhausted,
        )
        lease = ChainBudgetLease(
            lease_id=_ref("chain_budget_lease", max_steps, planned_steps, notes),
            owner_chain_id=_safe_text(source.get("run_id"), 120) if isinstance(source, dict) else "",
            current_limit=max_steps,
            requested_extension=requested_extension,
            renewal_recommended=needs_renewal,
            renewal_reason="long_chain_near_limit" if needs_renewal else "",
            confirmation_required_for_extension=bool(requested_extension > 0 and max_steps > 100),
            planner_hint="预算接近上限时建议续租；A0-A4 不因普通预算提示被默认阻断。",
        )
        timeout = TimeoutBudget(
            timeout_id=_ref("timeout_budget", max_steps, notes),
            default_timeout_seconds=120.0,
            remaining_timeout_seconds=120.0,
            timeout_risk="normal" if not needs_renewal else "watch",
            degradation_action="none" if not exhausted else "degrade_to_shorter_plan_or_request_budget_lease",
            blocks_execution=exhausted,
        )
        failure_budget = FailureBudget(
            failure_budget_id=_ref("failure_budget", failures, notes),
            max_failures=1,
            observed_failures=failures,
            remaining_failures=max(0, 1 - failures),
            exhausted=failures >= 1,
            recommended_action="continue" if failures == 0 else "produce_recovery_hint_before_continuing",
        )
        hard_reason = "step_budget_exhausted" if exhausted else ""
        snapshot = BudgetSnapshot(
            snapshot_id=_ref("budget_snapshot", ledger.ledger_id, lease.lease_id, timeout.timeout_id, failure_budget.failure_budget_id),
            step_ledger=ledger,
            chain_lease=lease,
            timeout_budget=timeout,
            failure_budget=failure_budget,
            planner_budget_hint=(
                "StepBudgetLedger/ChainBudgetLease/TimeoutBudget/FailureBudget 已生成；"
                "仅在资源耗尽或策略命中时建议降级，不随意阻断 A0-A4。"
            ),
            resource_exhausted=exhausted,
            downgrade_required=exhausted or failure_budget.exhausted,
            hard_block_reason=hard_reason,
        )
        self.budget = snapshot
        self._last_report = self._build_report()
        return snapshot

    def build_skill(
        self,
        *,
        skill_queue: dict[str, Any] | None = None,
        notes: str = "",
        max_items: int = 5,
    ) -> SkillIntegrationEnvelope:
        source = skill_queue or {}
        drafts = source.get("draft_versions") if isinstance(source, dict) else None
        candidate_routes: list[SkillCandidateRoute] = []
        for item in (drafts or [])[: max(1, min(int(max_items), 20))]:
            if not isinstance(item, dict):
                continue
            route = _build_skill_route(item, notes=notes)
            candidate_routes.append(route)
        if not candidate_routes:
            candidate_routes = [_default_skill_route(notes)]
        review_tickets = [
            SkillReviewTicket(
                ticket_id=_ref("skill_review_ticket", route.route_id, route.skill_name),
                route_id=route.route_id,
            )
            for route in candidate_routes
        ]
        activation_intents = [
            SkillActivationIntent(
                intent_id=_ref("skill_activation_intent", ticket.ticket_id, route.skill_name),
                ticket_id=ticket.ticket_id,
                target_skill_name=route.skill_name,
            )
            for route, ticket in zip(candidate_routes, review_tickets)
        ]
        hints = [
            SkillExecutionHint(
                hint_id=_ref("skill_execution_hint", route.route_id, route.skill_name),
                route_id=route.route_id,
                skill_name=route.skill_name,
                hint_text=route.planner_hint,
            )
            for route in candidate_routes
        ]
        envelope = SkillIntegrationEnvelope(
            envelope_id=_ref("skill_envelope", [route.route_id for route in candidate_routes], notes),
            candidate_routes=candidate_routes,
            review_tickets=review_tickets,
            activation_intents=activation_intents,
            execution_hints=hints,
        )
        envelope = SkillIntegrationEnvelope(
            envelope_id=envelope.envelope_id,
            candidate_routes=envelope.candidate_routes,
            review_tickets=envelope.review_tickets,
            activation_intents=envelope.activation_intents,
            execution_hints=envelope.execution_hints,
            report_digest=stable_l6_38_digest(envelope.public_dict()),
        )
        self.skill = envelope
        self._last_report = self._build_report()
        return envelope

    def build_handoff(
        self,
        *,
        parent_chain_id: str = "",
        notes: str = "",
        max_subtasks: int = 3,
    ) -> HandoffIntegrationEnvelope:
        parent = _safe_text(parent_chain_id, 120) or "parent_chain:l6_38_runtime"
        notes_clean = _safe_text(notes, 500) or "P0 系统接入后续人工确认子任务。"
        count = max(1, min(int(max_subtasks), 5))
        titles = _derive_subtask_titles(notes_clean, count)
        tickets = [
            SubtaskTicket(
                ticket_id=_ref("subtask_ticket", parent, title, index),
                parent_chain_id=parent,
                subtask_title=title,
                payload_summary=f"候选子任务：{title}。必须人工确认后派生，并回流父链。",
            )
            for index, title in enumerate(titles, start=1)
        ]
        handoff = HandoffEnvelope(
            envelope_id=_ref("handoff_envelope", parent, [ticket.ticket_id for ticket in tickets]),
            parent_chain_id=parent,
            subtask_tickets=tickets,
        )
        collect = ParentChainCollectReport(
            report_id=_ref("parent_collect", parent, [ticket.ticket_id for ticket in tickets]),
            parent_chain_id=parent,
            collected_ticket_ids=[],
            unresolved_ticket_ids=[ticket.ticket_id for ticket in tickets],
            suggested_parent_steps=[
                "等待用户确认是否派生子任务。",
                "子任务完成后必须提交 ParentChainCollectReport。",
                "父链只消费摘要、证据引用和下一步建议，不自动合并真实变更。",
            ],
        )
        envelope = HandoffIntegrationEnvelope(
            envelope_id=_ref("handoff_integration", handoff.envelope_id, collect.report_id),
            handoff_envelope=handoff,
            parent_collect_report=collect,
        )
        envelope = HandoffIntegrationEnvelope(
            envelope_id=envelope.envelope_id,
            handoff_envelope=envelope.handoff_envelope,
            parent_collect_report=envelope.parent_collect_report,
            report_digest=stable_l6_38_digest(envelope.public_dict()),
        )
        self.handoff = envelope
        self._last_report = self._build_report()
        return envelope

    def build_report(self, *, notes: str = "") -> L638P0IntegrationReport:
        if self.provider is None:
            self.build_provider(notes=notes)
        if self.budget is None:
            self.build_budget(notes=notes)
        if self.skill is None:
            self.build_skill(notes=notes)
        if self.handoff is None:
            self.build_handoff(notes=notes)
        self._last_report = self._build_report(notes=notes)
        return self._last_report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {"schema": L6_38_SCHEMA, "status": "empty", "message": "暂无 L6.38 P0 系统接入报告。"}
        return self._last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if self._last_report is None:
            return ""
        payload = self._last_report.public_dict()
        return (
            "L6.38 P0 接入摘要："
            f"status={payload.get('status')}；provider={bool(payload.get('provider'))}；"
            f"budget={bool(payload.get('budget'))}；skill={bool(payload.get('skill'))}；"
            f"handoff={bool(payload.get('handoff'))}；"
            "四系统均只能输出 Hint/Ticket/Envelope/Evidence/Report 并进入 PlannerExecutionController。"
        )[:1200]

    def _build_report(self, *, notes: str = "") -> L638P0IntegrationReport:
        present = [self.provider is not None, self.budget is not None, self.skill is not None, self.handoff is not None]
        status = "p0_systems_ready" if all(present) else "partial"
        missing = [name for name, ok in zip(("provider", "budget", "skill", "handoff"), present) if not ok]
        safe_notes = _safe_text(notes, 500)
        summary = "Provider / Budget / Skill / Handoff 已按 L6.37 冻结执行链接入。" if not missing else f"P0 接入部分完成，缺失：{', '.join(missing)}。"
        if safe_notes:
            summary += f" 备注：{safe_notes}"
        report = L638P0IntegrationReport(
            schema=L6_38_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            provider=self.provider,
            budget=self.budget,
            skill=self.skill,
            handoff=self.handoff,
        )
        return L638P0IntegrationReport(
            schema=report.schema,
            generated_at=report.generated_at,
            status=report.status,
            summary=report.summary,
            provider=report.provider,
            budget=report.budget,
            skill=report.skill,
            handoff=report.handoff,
            report_digest=stable_l6_38_digest(report.public_dict()),
        )


def build_l6_38_provider_adapter(bridge: L638P0SystemIntegrationBridge, provider_source: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            envelope = bridge.build_provider(
                provider_report=_public_dict(provider_source),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                requested_call_mode=str(invocation.arguments.get("call_mode") or invocation.arguments.get("requested_call_mode") or "dry_run"),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"L6.38 Provider 接入失败：{exc}", error_code="l6_38_provider_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="L6.38 Provider 接入完成：ProviderProfile / ProviderExecutionTicket / CredentialRef 已生成；使用 sample replay fallback，未触网未读密钥。",
            data=envelope.public_dict(),
        )

    return adapter


def build_l6_38_budget_adapter(bridge: L638P0SystemIntegrationBridge, planner_execution_source: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            planned_steps = int(invocation.arguments.get("planned_steps") or invocation.arguments.get("step_budget") or 0)
            snapshot = bridge.build_budget(
                planner_execution_report=_public_dict(planner_execution_source),
                max_steps=int(invocation.arguments.get("max_steps") or context.max_steps),
                planned_steps=planned_steps,
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"L6.38 Budget 接入失败：{exc}", error_code="l6_38_budget_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="L6.38 Budget 接入完成：StepBudgetLedger / ChainBudgetLease / TimeoutBudget / FailureBudget / BudgetSnapshot 已生成；不直接改预算，不默认阻断 A0-A4。",
            data=snapshot.public_dict(),
        )

    return adapter


def build_l6_38_skill_adapter(bridge: L638P0SystemIntegrationBridge, skill_queue_source: Any):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            envelope = bridge.build_skill(
                skill_queue=_public_dict(skill_queue_source),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
                max_items=int(invocation.arguments.get("max_items") or 5),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"L6.38 Skill 接入失败：{exc}", error_code="l6_38_skill_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="L6.38 Skill 接入完成：SkillCandidateRoute / SkillReviewTicket / SkillActivationIntent / SkillExecutionHint 已生成；正式激活仍需强确认。",
            data=envelope.public_dict(),
        )

    return adapter


def build_l6_38_handoff_adapter(bridge: L638P0SystemIntegrationBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            envelope = bridge.build_handoff(
                parent_chain_id=str(invocation.arguments.get("parent_chain_id") or context.turn_id),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or context.user_message or ""),
                max_subtasks=int(invocation.arguments.get("max_subtasks") or 3),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"L6.38 Handoff 接入失败：{exc}", error_code="l6_38_handoff_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary="L6.38 Handoff 接入完成：SubtaskTicket / HandoffEnvelope / ParentChainCollectReport 已生成；禁止自动递归派生，子任务必须回流父链。",
            data=envelope.public_dict(),
        )

    return adapter


def build_l6_38_p0_report_adapter(bridge: L638P0SystemIntegrationBridge):
    def adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            report = bridge.build_report(notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""))
        except (TypeError, ValueError) as exc:
            return ToolResult(invocation.step_id, invocation.tool_name, ToolResultStatus.FAILED, f"L6.38 P0 总报告生成失败：{exc}", error_code="l6_38_p0_report_failed")
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return adapter


def stable_l6_38_digest(payload: Any) -> str:
    data = json.loads(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
    if isinstance(data, dict):
        data.pop("report_digest", None)
        data.pop("generated_at", None)
    text = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]


def _public_dict(source: Any) -> dict[str, Any]:
    if source is None:
        return {}
    if hasattr(source, "public_dict"):
        value = source.public_dict()
        return dict(value) if isinstance(value, dict) else {}
    if isinstance(source, dict):
        return dict(source)
    return {}


def _default_provider_profiles() -> list[ProviderProfile]:
    display = {
        "deepseek_v4": ("DeepSeek V4", "deepseek-v4"),
        "mimo": ("MiMo", "mimo-default"),
        "glm_5_1": ("GLM 5.1", "glm-5.1"),
        "minimax_m3": ("MiniMax M3", "minimax-m3"),
        "gpt_5_5": ("GPT 5.5", "gpt-5.5"),
    }
    result: list[ProviderProfile] = []
    for provider_id in PROVIDER_IDS:
        name, model_id = display[provider_id]
        result.append(
            ProviderProfile(
                provider_id=provider_id,
                display_name=name,
                default_model_id=model_id,
                supported_surfaces=_surface_hints(provider_id, {}),
                credential_ref=CredentialRef(ref_id=f"credential_ref:{provider_id}:runtime", provider_id=provider_id),
            )
        )
    return result


def _surface_hints(provider_id: str, report: dict[str, Any]) -> list[str]:
    surfaces = []
    routes = report.get("api_surface_routes") if isinstance(report, dict) else None
    if isinstance(routes, list):
        for item in routes:
            if isinstance(item, dict) and _normalize_provider_id(item.get("provider_id")) == provider_id:
                surface = _safe_text(item.get("surface_id"), 80)
                if surface:
                    surfaces.append(surface)
    if surfaces:
        return sorted(set(surfaces))
    if provider_id == "mimo":
        return ["ordinary_api", "token_plan_api"]
    if provider_id == "gpt_5_5":
        return ["responses_api"]
    return ["ordinary_api"]


def _normalize_provider_id(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", "_").replace(".", "_")
    aliases = {
        "deepseek": "deepseek_v4",
        "deepseek_v4": "deepseek_v4",
        "glm": "glm_5_1",
        "glm_5_1": "glm_5_1",
        "gpt": "gpt_5_5",
        "gpt_5_5": "gpt_5_5",
        "minimax": "minimax_m3",
        "minimax_m3": "minimax_m3",
        "mimo": "mimo",
    }
    return aliases.get(text, text)


def _build_skill_route(item: dict[str, Any], *, notes: str) -> SkillCandidateRoute:
    draft_ref = _safe_text(item.get("draft_ref") or item.get("source_candidate_ref"), 160) or _ref("skill_draft", item)
    skill_name = _safe_text(item.get("skill_name"), 100) or "未命名 Skill 草案"
    purpose = _safe_text(item.get("purpose"), 400) or _safe_text(notes, 300) or "待审阅 Skill 草案。"
    hint = f"可作为 Planner 草案提示消费：{skill_name}。用途：{purpose}。正式激活前必须强确认。"
    return SkillCandidateRoute(
        route_id=_ref("skill_candidate_route", draft_ref, skill_name, purpose),
        source_draft_ref=draft_ref,
        skill_name=skill_name,
        purpose=purpose,
        planner_hint=hint[:800],
    )


def _default_skill_route(notes: str) -> SkillCandidateRoute:
    purpose = _safe_text(notes, 300) or "把重复执行链经验转成 Planner 可消费 Skill 草案。"
    return SkillCandidateRoute(
        route_id=_ref("skill_candidate_route", "default", purpose),
        source_draft_ref="skill_draft:l6_38_default_candidate",
        skill_name="L6.38 P0 执行链接入草案",
        purpose=purpose,
        planner_hint=f"Planner 可消费草案：{purpose}；不注册、不激活、不释放工具。",
    )


def _derive_subtask_titles(notes: str, count: int) -> list[str]:
    base = [
        "Provider / Budget / Skill / Handoff 接入回归复查",
        "父链回流报告补充",
        "P0 系统接入证据归档",
        "下一阶段回滚自修复接入准备",
        "GUI 驾驶舱展示字段预留",
    ]
    text = notes.strip()
    if text and len(text) > 8:
        base[0] = text[:80]
    return base[:count]


def _safe_text(value: Any, limit: int = 240) -> str:
    text = str(value or "").replace("\x00", "").strip()
    text = SENSITIVE_PATTERN.sub(lambda match: f"{match.group(1)}=<redacted>", text)
    text = redact_text(text)
    return text[:limit]


def _ref(prefix: str, *parts: Any) -> str:
    safe = json.dumps(parts, ensure_ascii=False, sort_keys=True, default=str)
    digest = hashlib.sha256(safe.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"
