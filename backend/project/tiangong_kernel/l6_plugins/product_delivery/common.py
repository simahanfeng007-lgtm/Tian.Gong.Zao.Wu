"""L6 phase6 product-delivery common declarations.

This package models product-grade delivery candidates and long-chain production
handoffs only. It deliberately remains inert: no file materialization, archive
creation, test execution, model invocation, tool invocation, L4 adapter access,
state mutation, memory mutation, audit write, budget charge, credential access or
parallel runtime creation happens here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from tiangong_kernel.l6_plugins.common._common import (
    L6_COMMON_SCHEMA_VERSION,
    ensure_bool,
    ensure_score,
    ensure_no_live_or_sensitive_text,
    ensure_ref_items,
    ensure_ref_text,
    ensure_schema_version,
    stable_digest,
)

L6_PHASE6 = "L6_PHASE6_PRODUCT_DELIVERY"
PRODUCT_EXECUTION_FIRST_POLICY = "ProductExecutionFirstWithinHardBoundaries"


class ProductDeliveryPluginKind(str, Enum):
    PRODUCT_SPEC_SEED = "product_spec_seed"
    REQUIREMENT_CLARIFICATION = "requirement_clarification"
    PRODUCT_PLAN_CANDIDATE = "product_plan_candidate"
    ARTIFACT_STRUCTURE_CANDIDATE = "artifact_structure_candidate"
    LONG_CHAIN_PRODUCTION = "long_chain_production"
    PRODUCT_QUALITY_GATE = "product_quality_gate"
    PRODUCT_GOVERNANCE_BRIDGE = "product_governance_bridge"
    PRODUCT_DISPATCH_INTENT = "product_dispatch_intent"
    DELIVERY_PACKAGE_CANDIDATE = "delivery_package_candidate"
    PRODUCT_ITERATION_FEEDBACK = "product_iteration_feedback"
    PRODUCT_PUBLIC_PROJECTION = "product_public_projection"
    PRODUCT_HANDOFF = "product_handoff"


class ProductOutputKind(str, Enum):
    CANDIDATE = "candidate"
    REQUIREMENT = "requirement"
    INTENT = "intent"
    HINT = "hint"
    SUGGESTION = "suggestion"
    REPORT = "report"
    SUMMARY = "summary"
    HANDOFF = "handoff"


class ProductRiskTier(str, Enum):
    A0 = "a0"
    A1 = "a1"
    A2 = "a2"
    A3 = "a3"
    A4 = "a4"
    A5 = "a5"


class ProductRedactionState(str, Enum):
    NOT_NEEDED = "not_needed"
    APPLIED_SUMMARY_ONLY = "applied_summary_only"
    REQUIRED = "required"
    BLOCKED_PUBLIC_DETAIL = "blocked_public_detail"


class ProductPrivacyClass(str, Enum):
    PUBLIC_SUMMARY = "public_summary"
    INTERNAL_REF_ONLY = "internal_ref_only"
    SENSITIVE_SUMMARY_ONLY = "sensitive_summary_only"
    BLOCKED_FROM_PUBLIC = "blocked_from_public"


def ensure_score(value: float, field_name: str) -> None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{field_name} must be numeric score")
    if value < 0.0 or value > 1.0:
        raise ValueError(f"{field_name} must be within [0, 1]")


def ensure_non_negative_int(value: int, field_name: str) -> None:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field_name} must be non-negative integer")


@dataclass(frozen=True)
class ProductArtifactBase:
    object_ref: str
    source_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_source",))
    input_summary_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_input",))
    requirement_refs: tuple[str, ...] = field(default_factory=tuple)
    risk_refs: tuple[str, ...] = field(default_factory=tuple)
    governance_refs: tuple[str, ...] = field(default_factory=lambda: ("review:l6_phase5_governance_required",))
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase6_evidence",))
    trace_ref: str = "ref:l6_phase6_trace"
    responsibility_chain_ref: str = "responsibility:l6_phase6_chain"
    tamper_evidence_ref: str = "evidence:l6_phase6_tamper"
    redaction_state: ProductRedactionState | str = ProductRedactionState.APPLIED_SUMMARY_ONLY
    privacy_class: ProductPrivacyClass | str = ProductPrivacyClass.INTERNAL_REF_ONLY
    ttl_ref: str = "ref:l6_phase6_ttl"
    expiry_ref: str = "ref:l6_phase6_expiry"
    confidence_score: float = 0.75
    uncertainty_score: float = 0.25
    assumption_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_assumption",))
    dependency_refs: tuple[str, ...] = field(default_factory=tuple)
    acceptance_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_acceptance",))
    quality_refs: tuple[str, ...] = field(default_factory=lambda: ("quality:l6_phase6_candidate_quality",))
    continuation_hint_refs: tuple[str, ...] = field(default_factory=lambda: ("hint:l6_phase6_continue_when_safe",))
    public_summary: str = "summary:l6_phase6_minimal_public_summary"
    not_executed: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.object_ref, f"{self.__class__.__name__}.object_ref")
        for field_name in (
            "source_refs", "input_summary_refs", "requirement_refs", "risk_refs", "governance_refs",
            "evidence_refs", "assumption_refs", "dependency_refs", "acceptance_refs", "quality_refs",
            "continuation_hint_refs",
        ):
            ensure_ref_items(getattr(self, field_name), f"{self.__class__.__name__}.{field_name}", required=field_name in ("source_refs", "input_summary_refs", "evidence_refs", "governance_refs"))
        for field_name in ("trace_ref", "responsibility_chain_ref", "tamper_evidence_ref", "ttl_ref", "expiry_ref"):
            ensure_ref_text(getattr(self, field_name), f"{self.__class__.__name__}.{field_name}")
        object.__setattr__(self, "redaction_state", ProductRedactionState(self.redaction_state))
        object.__setattr__(self, "privacy_class", ProductPrivacyClass(self.privacy_class))
        ensure_score(self.confidence_score, f"{self.__class__.__name__}.confidence_score")
        ensure_score(self.uncertainty_score, f"{self.__class__.__name__}.uncertainty_score")
        ensure_no_live_or_sensitive_text(self.public_summary, f"{self.__class__.__name__}.public_summary")
        ensure_bool(self.not_executed, f"{self.__class__.__name__}.not_executed")
        if not self.not_executed:
            raise ValueError("L6 phase6 product artifacts must remain candidate or requirement objects, not executed results")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class ProductDeliveryPluginDeclaration:
    plugin_ref: str
    plugin_kind: ProductDeliveryPluginKind | str
    summary: str
    output_kinds: tuple[ProductOutputKind | str, ...] = field(default_factory=lambda: (ProductOutputKind.CANDIDATE, ProductOutputKind.HINT))
    source_refs: tuple[str, ...] = field(default_factory=lambda: ("summary:l6_phase6_plugin_input",))
    evidence_refs: tuple[str, ...] = field(default_factory=lambda: ("evidence:l6_phase6_plugin_declaration",))
    is_executor: bool = False
    materializes_files: bool = False
    materializes_archive: bool = False
    runs_test_process: bool = False
    dispatches_model: bool = False
    dispatches_tool: bool = False
    calls_l4_adapter: bool = False
    reads_credentials: bool = False
    writes_l2_fact: bool = False
    writes_memory: bool = False
    deletes_memory: bool = False
    writes_audit_store: bool = False
    charges_budget: bool = False
    creates_parallel_runtime: bool = False
    direct_plugin_link: bool = False
    overasks_by_default: bool = False
    blocks_low_risk_by_default: bool = False
    governance_review_required: bool = True
    execution_first_within_hard_boundaries: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.plugin_ref, "ProductDeliveryPluginDeclaration.plugin_ref")
        object.__setattr__(self, "plugin_kind", ProductDeliveryPluginKind(self.plugin_kind))
        ensure_no_live_or_sensitive_text(self.summary, "ProductDeliveryPluginDeclaration.summary")
        if not isinstance(self.output_kinds, tuple) or not self.output_kinds:
            raise ValueError("ProductDeliveryPluginDeclaration.output_kinds must be non-empty tuple")
        object.__setattr__(self, "output_kinds", tuple(ProductOutputKind(kind) for kind in self.output_kinds))
        ensure_ref_items(self.source_refs, "ProductDeliveryPluginDeclaration.source_refs", required=True)
        ensure_ref_items(self.evidence_refs, "ProductDeliveryPluginDeclaration.evidence_refs", required=True)
        bool_fields = (
            "is_executor", "materializes_files", "materializes_archive", "runs_test_process", "dispatches_model", "dispatches_tool",
            "calls_l4_adapter", "reads_credentials", "writes_l2_fact", "writes_memory", "deletes_memory", "writes_audit_store",
            "charges_budget", "creates_parallel_runtime", "direct_plugin_link", "overasks_by_default", "blocks_low_risk_by_default",
            "governance_review_required", "execution_first_within_hard_boundaries",
        )
        for field_name in bool_fields:
            ensure_bool(getattr(self, field_name), f"ProductDeliveryPluginDeclaration.{field_name}")
        forbidden_flags = (
            self.is_executor,
            self.materializes_files,
            self.materializes_archive,
            self.runs_test_process,
            self.dispatches_model,
            self.dispatches_tool,
            self.calls_l4_adapter,
            self.reads_credentials,
            self.writes_l2_fact,
            self.writes_memory,
            self.deletes_memory,
            self.writes_audit_store,
            self.charges_budget,
            self.creates_parallel_runtime,
            self.direct_plugin_link,
            self.overasks_by_default,
            self.blocks_low_risk_by_default,
        )
        if any(forbidden_flags):
            raise ValueError("L6 phase6 product delivery plugins must stay inert, candidate-only, and execution-first")
        if not self.governance_review_required or not self.execution_first_within_hard_boundaries:
            raise ValueError("Product delivery candidates must pass governance review while preserving execution-first continuity")
        ensure_schema_version(self.schema_version)

    @property
    def product_delivery_plugin_is_not_executor(self) -> bool:
        return not self.is_executor and not self.materializes_files and not self.materializes_archive and not self.runs_test_process

    @property
    def digest(self) -> str:
        return stable_digest(self)


@dataclass(frozen=True)
class ProductDeliveryGroupArchitecture:
    group_ref: str = "l6:phase6_product_delivery_group"
    phase: str = L6_PHASE6
    policy_ref: str = "policy:product_execution_first_within_hard_boundaries"
    plugin_refs: tuple[str, ...] = field(default_factory=lambda: tuple(f"l6:phase6_{kind.value}" for kind in ProductDeliveryPluginKind))
    l3_orchestration_required: bool = True
    l5_governance_required: bool = True
    l4_action_required_for_real_effect: bool = True
    materializes_real_artifact: bool = False
    creates_parallel_runtime: bool = False
    supports_long_chain_delivery: bool = True
    minimizes_clarification: bool = True
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.group_ref, "ProductDeliveryGroupArchitecture.group_ref")
        if self.phase != L6_PHASE6:
            raise ValueError("ProductDeliveryGroupArchitecture.phase must be L6 phase6")
        ensure_ref_text(self.policy_ref, "ProductDeliveryGroupArchitecture.policy_ref")
        ensure_ref_items(self.plugin_refs, "ProductDeliveryGroupArchitecture.plugin_refs", required=True)
        for field_name in (
            "l3_orchestration_required", "l5_governance_required", "l4_action_required_for_real_effect", "materializes_real_artifact",
            "creates_parallel_runtime", "supports_long_chain_delivery", "minimizes_clarification",
        ):
            ensure_bool(getattr(self, field_name), f"ProductDeliveryGroupArchitecture.{field_name}")
        if not self.l3_orchestration_required or not self.l5_governance_required or not self.l4_action_required_for_real_effect:
            raise ValueError("Phase6 must route real effects through L3/L5/L4")
        if self.materializes_real_artifact or self.creates_parallel_runtime:
            raise ValueError("Phase6 product delivery group is not a real executor or runtime")
        if not self.supports_long_chain_delivery or not self.minimizes_clarification:
            raise ValueError("Phase6 must preserve long-chain delivery and minimal clarification")
        ensure_schema_version(self.schema_version)


@dataclass(frozen=True)
class ProductExecutionFirstPolicy:
    policy_ref: str = "policy:product_execution_first_within_hard_boundaries"
    produce_candidate_when_low_risk: bool = True
    continue_without_clarification_when_safe: bool = True
    checkpoint_long_chain: bool = True
    recover_after_failure: bool = True
    degrade_before_abort: bool = True
    hard_boundaries_preserved: bool = True
    bypasses_governance: bool = False
    bypasses_l3: bool = False
    bypasses_l4: bool = False
    bypasses_l5: bool = False
    schema_version: str = L6_COMMON_SCHEMA_VERSION

    def __post_init__(self) -> None:
        ensure_ref_text(self.policy_ref, "ProductExecutionFirstPolicy.policy_ref")
        for field_name in (
            "produce_candidate_when_low_risk", "continue_without_clarification_when_safe", "checkpoint_long_chain", "recover_after_failure",
            "degrade_before_abort", "hard_boundaries_preserved", "bypasses_governance", "bypasses_l3", "bypasses_l4", "bypasses_l5",
        ):
            ensure_bool(getattr(self, field_name), f"ProductExecutionFirstPolicy.{field_name}")
        if not all((self.produce_candidate_when_low_risk, self.continue_without_clarification_when_safe, self.checkpoint_long_chain, self.recover_after_failure, self.degrade_before_abort, self.hard_boundaries_preserved)):
            raise ValueError("Product execution-first policy must support delivery continuity within hard boundaries")
        if any((self.bypasses_governance, self.bypasses_l3, self.bypasses_l4, self.bypasses_l5)):
            raise ValueError("Product execution-first policy cannot bypass L3/L4/L5 governance chain")
        ensure_schema_version(self.schema_version)

    @property
    def digest(self) -> str:
        return stable_digest(self)


def default_product_delivery_plugin_declarations() -> tuple[ProductDeliveryPluginDeclaration, ...]:
    summaries = {
        ProductDeliveryPluginKind.PRODUCT_SPEC_SEED: "从需求、上下文、目标和约束生成产品规格种子候选；不生成最终规格。",
        ProductDeliveryPluginKind.REQUIREMENT_CLARIFICATION: "识别缺口、冲突和最小澄清点；低风险时先记录假设继续推进。",
        ProductDeliveryPluginKind.PRODUCT_PLAN_CANDIDATE: "生成阶段、任务、依赖和里程碑候选；不调度执行。",
        ProductDeliveryPluginKind.ARTIFACT_STRUCTURE_CANDIDATE: "生成产物结构、清单和交付目录候选；不创建真实文件树。",
        ProductDeliveryPluginKind.LONG_CHAIN_PRODUCTION: "生成超长链阶段、checkpoint、续接和降级继续提示；不自建调度器。",
        ProductDeliveryPluginKind.PRODUCT_QUALITY_GATE: "生成完整性、一致性、验收和风险候选；不伪造验收通过。",
        ProductDeliveryPluginKind.PRODUCT_GOVERNANCE_BRIDGE: "把生产候选转入第五阶段治理预审；不签发许可。",
        ProductDeliveryPluginKind.PRODUCT_DISPATCH_INTENT: "生成工具、模型、文件、测试和打包能力需求；不执行。",
        ProductDeliveryPluginKind.DELIVERY_PACKAGE_CANDIDATE: "生成交付包、报告、修改清单、测试结果和风险清单候选；不打包。",
        ProductDeliveryPluginKind.PRODUCT_ITERATION_FEEDBACK: "根据反馈、测试摘要和失败归因生成迭代候选；不自动修复。",
        ProductDeliveryPluginKind.PRODUCT_PUBLIC_PROJECTION: "生成最小公开产品交付摘要；不泄露完整上下文或敏感材料。",
        ProductDeliveryPluginKind.PRODUCT_HANDOFF: "生成给 L3、L5、状态回流、测试和未来执行阶段的交接提示；不自动合并。",
    }
    return tuple(
        ProductDeliveryPluginDeclaration(
            plugin_ref=f"l6:phase6_{kind.value}",
            plugin_kind=kind,
            summary=summaries[kind],
        )
        for kind in ProductDeliveryPluginKind
    )
