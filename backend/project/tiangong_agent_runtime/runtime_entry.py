"""L6.10-L6.32 运行入口。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from time import time
from typing import Any

from tiangong_agent_shell.tool_bridge import ToolExecutionMode
from tiangong_agent_shell.safe_logging import redact_text

from .adapters.model_chat_adapter import model_chat_adapter
from .adapters.diagnose_project_adapter import build_diagnose_project_adapter
from .adapters.project_scan_adapter import build_scan_project_adapter
from .adapters.quality_gate_adapter import build_evaluate_quality_gate_adapter
from .adapters.python_test_adapter import run_python_quality_check_adapter
from .adapters.readonly_file_adapter import list_dir_adapter, read_file_adapter
from .adapters.workspace_write_adapter import write_workspace_file_adapter
from .adapters.virtual_return_adapter import return_analysis_adapter, return_code_adapter
from .adapters.zip_package_adapter import create_zip_package_adapter
from .affective_execution_route import AffectiveExecutionRoute, AffectiveExecutionRouter
from .affective_state import AffectiveState, AffectiveStateEngine, SevenEmotionSignalSources, SixDesireSignalSources, clamp01
from .audit_bridge import AuditBridge
from .audit_replay import AuditReplaySummary, replay_audit_events
from .budget_low_friction_governance import BudgetLowFrictionGovernanceBridge
from .confirmation_ticket import ConfirmationTicketStore
from .context_memory_bridge import ContextMemoryBridge
from .delivery_manifest import DeliveryManifestBridge, build_create_release_bundle_adapter
from .experience_synthesis import ExperienceSynthesisBridge, build_synthesize_experience_adapter
from .skill_review_queue import SkillReviewQueueBridge, build_queue_skill_candidates_adapter
from .tool_production_request import ToolProductionRequestBridge, build_queue_tool_production_requests_adapter
from .execution_exoskeleton import ExecutionExoskeletonBridge, build_execution_exoskeleton_adapter
from .shell_system_mount import ShellSystemMountBridge, build_shell_system_mount_adapter, discover_runtime_module_files
from .project_repair_plan import ProjectRepairPlanBridge, build_project_repair_plan_adapter
from .delivery_standardization import DeliveryStandardizationBridge, build_delivery_standardization_adapter
from .provider_adaptation_shell import ProviderAdaptationBridge, build_provider_adaptation_adapter
from .learning_convergence import LearningConvergenceBridge, build_learning_convergence_adapter
from .lifecycle_coordinator import LifecycleRouteBundle, LifecycleCoordinator
from .recovery_coordination import RecoveryCoordinationBridge, build_recovery_coordination_adapter
from .governance_execution import GovernanceExecutionBridge, build_governance_execution_adapter
from .planner_context_integration import PlannerContextIntegrationBridge, build_planner_context_integration_adapter
from .p0_system_integration import (
    L638P0SystemIntegrationBridge,
    build_l6_38_budget_adapter,
    build_l6_38_handoff_adapter,
    build_l6_38_p0_report_adapter,
    build_l6_38_provider_adapter,
    build_l6_38_skill_adapter,
)
from .p0_system_integration_two import (
    L639P0SystemIntegrationBridge,
    build_l6_39_audit_adapter,
    build_l6_39_memory_adapter,
    build_l6_39_p0_report_adapter,
    build_l6_39_quality_gate_adapter,
    build_l6_39_recovery_adapter,
)
from .planner_execution_controller import PlannerExecutionController, PlannerExecutionReport
from .diagnostic_bridge import EngineeringDiagnosticBridge
from .execution_spine import ExecutionSpine
from .forgetting_review_router import ForgetReviewDecision, ForgetReviewRouter
from .four_path_context_router import FourPathContextReport, FourPathContextRouter
from .intent_bridge import IntentBridge, IntentResult
from .long_chain_runner import LongChainRunSummary, LongChainRunner
from .memory_math_core import DecayKernel, ForgettingScoreVector, MemoryLevel
from .memory_recall_router import L640MemoryRecallRoute, MemoryRecallRouter
from .memory_store_bridge import MemoryRecord, MemoryStoreBridge
from .model_planner import ModelPlanner, ModelPlannerResult
from .model_plan_compat_replay import replay_deepseek_plan_samples
from .recovery_replay_quality import run_l6_36_replay_corpus
from .execution_chain_freeze import build_execution_chain_freeze_report, build_default_execution_chain_contract
from .plan_bridge import PlanBridge
from .plan_schema import plan_to_public_dict
from .planner_mode import PlannerMode, normalize_planner_mode
from .planner_unified_consumption import PlannerConsumptionReport, PlannerUnifiedConsumptionBridge
from .plugin_suggestion_bridge import PluginSuggestionBridge, SuggestionBridgeResult
from .project_index_bridge import ProjectIndexBridge
from .quality_gate_bridge import QualityGateBridge
from .public_projection_bridge import RuntimeProjection, build_public_projection
from .runtime_report import export_runtime_report
from .runtime_tool_registry import RuntimeToolRegistry, ToolDescriptor
from .suggestions import HandoffSuggestion, PlanSuggestion, QualityGateSuggestion, RepairSuggestion
from .tool_invocation import ToolInvocation
from .tool_result import ToolResult
from .turn_context import TurnContext
from .code_x_runtime_adapters import register_code_x_runtime_tools
from .v1_clean_import_adapters import register_v1_clean_import_tools
from .runtime_tool_alignment import build_runtime_llm_drill_adapter, build_runtime_tool_alignment_adapter
from .learning_asset_contract import (
    LearningAssetContractBridge,
    build_learning_asset_contract_guide_adapter,
    build_learning_asset_contract_normalize_adapter,
    build_learning_asset_contract_validate_adapter,
)
from .learning_asset_sandbox_alignment import (
    LearningAssetSandboxAlignmentBridge,
    build_learning_asset_sandbox_guide_adapter,
    build_learning_asset_sandbox_align_adapter,
    build_learning_asset_sandbox_validate_adapter,
)
from .learning_asset_candidate_sandbox import (
    LearningAssetCandidateSandboxBridge,
    build_learning_asset_candidate_sandbox_guide_adapter,
    build_learning_asset_candidate_sandbox_build_adapter,
    build_learning_asset_candidate_sandbox_validate_adapter,
    build_learning_asset_candidate_sandbox_review_adapter,
)
from .learning_asset_release_gate import (
    LearningAssetReleaseGateBridge,
    build_learning_asset_release_gate_guide_adapter,
    build_learning_asset_release_gate_check_adapter,
)
from .learning_asset_activation import (
    LearningAssetActivationBridge,
    build_learning_asset_activation_guide_adapter,
    build_learning_asset_activation_apply_adapter,
    build_learning_asset_activation_status_adapter,
    build_learning_asset_activation_smoke_adapter,
)
from .learning_asset_adapter import (
    LearningAssetAdapterBridge,
    build_learning_asset_adapter_guide_adapter,
    build_learning_asset_adapter_template_list_adapter,
    build_learning_asset_adapter_template_normalize_adapter,
    build_learning_asset_adapter_template_validate_adapter,
    build_learning_asset_adapter_template_smoke_adapter,
    build_learning_asset_adapter_drill_adapter,
)


@dataclass(frozen=True)
class RuntimeRunResult:
    intent: IntentResult
    plan: list[ToolInvocation]
    results: list[ToolResult]
    projection: RuntimeProjection
    audit_events: list[dict]
    chain_summary: LongChainRunSummary | None = None
    suggestion_bridge: SuggestionBridgeResult | None = None
    pending_confirmations: list[dict[str, Any]] | None = None
    planner_result: ModelPlannerResult | None = None
    planner_execution_report: PlannerExecutionReport | None = None

    @property
    def has_plan(self) -> bool:
        return bool(self.plan)


class RuntimeEntry:
    def __init__(
        self,
        registry: RuntimeToolRegistry | None = None,
        audit: AuditBridge | None = None,
        ticket_store: ConfirmationTicketStore | None = None,
        memory_store: MemoryStoreBridge | None = None,
    ) -> None:
        self.audit = audit or AuditBridge()
        self.ticket_store = ticket_store or ConfirmationTicketStore()
        self.registry = registry or build_default_registry()
        self.spine = ExecutionSpine(self.registry, audit=self.audit, ticket_store=self.ticket_store)
        self.intent_bridge = IntentBridge()
        self.plan_bridge = PlanBridge()
        self.model_planner = ModelPlanner()
        self.suggestion_bridge = PluginSuggestionBridge()
        self.context_memory = ContextMemoryBridge()
        self.project_index = ProjectIndexBridge()
        self.diagnostics = EngineeringDiagnosticBridge()
        self.quality_gate = QualityGateBridge()
        self.delivery = DeliveryManifestBridge()
        self.experience = ExperienceSynthesisBridge()
        self.skill_queue = SkillReviewQueueBridge()
        self.tool_requests = ToolProductionRequestBridge()
        self.exoskeleton = ExecutionExoskeletonBridge()
        self.shell_mount = ShellSystemMountBridge()
        self.project_repair = ProjectRepairPlanBridge()
        self.delivery_standardization = DeliveryStandardizationBridge()
        self.provider_adaptation = ProviderAdaptationBridge()
        self.learning_convergence = LearningConvergenceBridge()
        self.learning_asset_contract = LearningAssetContractBridge()
        self.learning_asset_sandbox = LearningAssetSandboxAlignmentBridge()
        self.learning_asset_candidate_sandbox = LearningAssetCandidateSandboxBridge()
        self.learning_asset_release_gate = LearningAssetReleaseGateBridge()
        self.learning_asset_activation = LearningAssetActivationBridge(self.registry)
        self.learning_asset_adapter = LearningAssetAdapterBridge(self.learning_asset_activation)
        self.recovery_coordination = RecoveryCoordinationBridge()
        self.governance_execution = GovernanceExecutionBridge()
        self.planner_context = PlannerContextIntegrationBridge()
        self.planner_execution = PlannerExecutionController()
        self.p0_system_integration = L638P0SystemIntegrationBridge()
        self.p0_system_integration_two = L639P0SystemIntegrationBridge()
        # L6.49.3：Runtime 级接口接线体检后，将已存在但未被 Runtime 接活的
        # 只读/候选类引擎挂到 Planner 上下文。以下组件均不得执行工具、改预算、写记忆或改内核。
        self.budget_low_friction = BudgetLowFrictionGovernanceBridge()
        self.lifecycle_coordinator = LifecycleCoordinator()
        self.four_path_context = FourPathContextRouter()
        self.planner_unified_consumption = PlannerUnifiedConsumptionBridge()
        # L6.49.2：Runtime 级情志/遗忘接线。
        # 只维护 Runtime 内部投影状态，不授权、不拒绝、不派发工具、不直接修改长期记忆。
        self._affective_engine = AffectiveStateEngine()
        self._affective_router = AffectiveExecutionRouter()
        self._affective_state: AffectiveState | None = None
        self._affective_route: AffectiveExecutionRoute | None = None
        self._last_affective_update_at: float | None = None
        self._affective_turn_count = 0
        self._forget_review_router = ForgetReviewRouter()
        self._memory_store = memory_store
        self._last_memory_recall_route: L640MemoryRecallRoute | None = None
        self._last_memory_recall_error: str = ""
        self._last_forget_review_decisions: tuple[ForgetReviewDecision, ...] = tuple()
        self._last_forget_review_error: str = ""
        self._last_lifecycle_bundle: LifecycleRouteBundle | None = None
        self._last_four_path_report: FourPathContextReport | None = None
        self._last_planner_consumption_report: PlannerConsumptionReport | None = None
        # L6.16: 项目雷达 adapter 需要共享当前 RuntimeEntry 的 project_index 快照。
        self.registry.register(
            ToolDescriptor("scan_project", "只读扫描工作区项目结构并生成安全索引。", "A1"),
            build_scan_project_adapter(self.project_index),
        )
        self.registry.register(
            ToolDescriptor("diagnose_project", "基于项目雷达和质量检查摘要生成工程诊断。", "A1/A2"),
            build_diagnose_project_adapter(self.project_index, self.diagnostics),
        )
        self.registry.register(
            ToolDescriptor("evaluate_quality_gate", "根据质量检查与工程诊断生成 L6.18 质量门裁决。", "A2"),
            build_evaluate_quality_gate_adapter(self.quality_gate),
        )
        self.registry.register(
            ToolDescriptor("create_release_bundle", "生成 L6.19 标准 Release Bundle 与交付 Manifest。", "A3"),
            build_create_release_bundle_adapter(self.delivery, self.quality_gate, self.diagnostics, self.audit),
        )
        self.registry.register(
            ToolDescriptor("synthesize_experience_candidates", "生成 L6.20 经验沉淀与 Skill/Tool 候选，不注册不生产。", "A2"),
            build_synthesize_experience_adapter(self.experience, self.context_memory, self.diagnostics, self.quality_gate, self.delivery),
        )
        self.registry.register(
            ToolDescriptor("queue_skill_candidates", "生成 L6.21 Skill 草案版本与审阅队列，不注册不激活。", "A2"),
            build_queue_skill_candidates_adapter(self.skill_queue, self.experience),
        )
        self.registry.register(
            ToolDescriptor("queue_tool_production_requests", "生成 L6.22 Tool 生产请求与沙箱验证前置队列，不生产不注册不释放。", "A2"),
            build_queue_tool_production_requests_adapter(self.tool_requests, self.experience),
        )
        self.registry.register(
            ToolDescriptor("build_execution_exoskeleton", "生成 L6.23 LLM 外骨骼执行提示与最小 Tool 候选票据，不注册不生产。", "A2"),
            build_execution_exoskeleton_adapter(self.exoskeleton, self.experience, self.skill_queue, self.tool_requests),
        )
        self.registry.register(
            ToolDescriptor("build_shell_system_mount", "生成 L6.24 十八系统 Runtime 外壳挂载报告，只读映射已装系统，不改内核。", "A2"),
            build_shell_system_mount_adapter(self.shell_mount, self._shell_mount_state),
        )
        self.registry.register(
            ToolDescriptor("build_project_repair_plan", "生成 L6.25 项目雷达 + 工程修复 PatchPlan/RegressionHint/RollbackEvidence，不应用补丁不改内核。", "A2"),
            build_project_repair_plan_adapter(self.project_repair, self.project_index, self.diagnostics, self._shell_mount_state),
        )
        self.registry.register(
            ToolDescriptor("build_delivery_standardization", "生成 L6.26 标准化交付证据：ChangeSet/TestEvidence/Manifest/Integrity/Todo，不打包不写文件不改内核。", "A2"),
            build_delivery_standardization_adapter(
                self.delivery_standardization,
                self.quality_gate,
                self.diagnostics,
                self.delivery,
                self.project_repair,
                self.shell_mount,
                self.audit,
            ),
        )
        self.registry.register(
            ToolDescriptor("build_provider_adaptation", "生成 L6.27 Provider 适配外壳：ProviderProfile/CapabilityMatrix/API Surface/GovernanceMount，不触网不读密钥不注册正式适配器。", "A2"),
            build_provider_adaptation_adapter(
                self.provider_adaptation,
                self.shell_mount,
                self.delivery_standardization,
                self.audit,
            ),
        )
        self.registry.register(
            ToolDescriptor("build_learning_convergence", "生成 L6.28 经验/Skill/Tool 执行合流：PlannerHintRoute/SkillDraftRoute/ToolCandidateRoute/ConsumptionCard，不写记忆不注册不生产。", "A2"),
            build_learning_convergence_adapter(
                self.learning_convergence,
                self.experience,
                self.skill_queue,
                self.tool_requests,
                self.exoskeleton,
            ),
        )
        self.registry.register(
            ToolDescriptor("build_recovery_coordination", "生成 L6.29 自修复/多智能体/预算联动恢复协调：FailureSignal/RepairCandidate/HandoffDigest/BudgetUpdate/ResumePlan，不派生不执行不改预算不改内核。", "A2"),
            build_recovery_coordination_adapter(
                self.recovery_coordination,
                self.diagnostics,
                self.quality_gate,
                self.project_repair,
                self.learning_convergence,
                self.delivery_standardization,
                self.audit,
            ),
        )
        self.registry.register(
            ToolDescriptor("build_governance_execution", "生成 L6.30 治理执行力化报告：A0-A4 草案/分析/smoke/续接快车道，A5 硬边界，发布/注册/激活护栏；不改策略不执行不改内核。", "A2"),
            build_governance_execution_adapter(
                self.governance_execution,
                self.recovery_coordination,
                self.learning_convergence,
                self.provider_adaptation,
                self.delivery_standardization,
                self.project_repair,
                self.shell_mount,
                self.audit,
                self.ticket_store,
            ),
        )
        self.registry.register(
            ToolDescriptor("build_planner_context", "生成 L6.31 统一 Planner 上下文：聚合 L6.24-L6.30 外壳输出为 UnifiedPlannerContext / ExecutionStepDraft / ResumeEnvelope，不执行不注册不改内核。", "A2"),
            build_planner_context_integration_adapter(
                self.planner_context,
                self.shell_mount,
                self.project_repair,
                self.delivery_standardization,
                self.provider_adaptation,
                self.learning_convergence,
                self.recovery_coordination,
                self.governance_execution,
            ),
        )
        self.registry.register(
            ToolDescriptor("build_l6_38_provider_integration", "生成 L6.38 ProviderProfile/ProviderExecutionTicket/CredentialRef，Provider smoke 无许可时降级 sample replay。", "A2"),
            build_l6_38_provider_adapter(self.p0_system_integration, self.provider_adaptation),
        )
        self.registry.register(
            ToolDescriptor("build_l6_38_budget_snapshot", "生成 L6.38 StepBudgetLedger/ChainBudgetLease/TimeoutBudget/FailureBudget/BudgetSnapshot，不直接改预算。", "A2"),
            build_l6_38_budget_adapter(self.p0_system_integration, self.planner_execution),
        )
        self.registry.register(
            ToolDescriptor("build_l6_38_skill_integration", "生成 L6.38 SkillCandidateRoute/SkillReviewTicket/SkillActivationIntent/SkillExecutionHint，不注册不激活。", "A2"),
            build_l6_38_skill_adapter(self.p0_system_integration, self.skill_queue),
        )
        self.registry.register(
            ToolDescriptor("build_l6_38_handoff_integration", "生成 L6.38 SubtaskTicket/HandoffEnvelope/ParentChainCollectReport，禁止自动递归派生。", "A2"),
            build_l6_38_handoff_adapter(self.p0_system_integration),
        )
        self.registry.register(
            ToolDescriptor("build_l6_38_p0_integration", "生成 L6.38 Provider/Budget/Skill/Handoff 四系统接入总报告，统一进入 PlannerExecutionController。", "A2"),
            build_l6_38_p0_report_adapter(self.p0_system_integration),
        )
        self.registry.register(
            ToolDescriptor("build_l6_39_memory_integration", "生成 L6.39 MemoryRecallRoute，只读当前上下文安全摘要，不写长期记忆。", "A2"),
            build_l6_39_memory_adapter(self.p0_system_integration_two, self.context_memory),
        )
        self.registry.register(
            ToolDescriptor("build_l6_39_audit_integration", "生成 L6.39 AuditEvidenceEnvelope，只读审计安全摘要，不删除不重写。", "A2"),
            build_l6_39_audit_adapter(self.p0_system_integration_two, self.audit),
        )
        self.registry.register(
            ToolDescriptor("build_l6_39_recovery_integration", "生成 L6.39 RecoveryResumeTicket，只给恢复续接票据，不执行补丁不派生子智能体。", "A2"),
            build_l6_39_recovery_adapter(self.p0_system_integration_two, self.recovery_coordination),
        )
        self.registry.register(
            ToolDescriptor("build_l6_39_quality_gate_integration", "生成 L6.39 QualityGateEvidence，只引用质量门裁决，不自动放行发布。", "A2"),
            build_l6_39_quality_gate_adapter(self.p0_system_integration_two, self.quality_gate),
        )
        self.registry.register(
            ToolDescriptor("build_l6_39_p0_integration", "生成 L6.39 Memory/Audit/Recovery/QualityGate 四系统接入二总报告，统一进入 PlannerExecutionController。", "A2"),
            build_l6_39_p0_report_adapter(self.p0_system_integration_two),
        )
        # L6.70.2-R15：全局工具注册表 / Skill / LLM 路由对齐。
        # 仅做元数据检查和路由演练，不执行目标工具、不改注册表、不让 Planner 夺权。
        self.registry.register(
            ToolDescriptor("runtime_tool_alignment_check", "全局 Runtime 工具注册表、风险、Skill 使用卡和 LLM 入口对齐检查。", "A2"),
            build_runtime_tool_alignment_adapter(self.registry.describe),
        )
        self.registry.register(
            ToolDescriptor("runtime_llm_operational_drill", "模拟 LLM 从用户意图到 PlanBridge 到 Runtime 工具名的可用性演练。", "A2"),
            build_runtime_llm_drill_adapter(self.registry.describe, self.plan_bridge.build_plan),
        )
        # L6.70.2-R16：未来自主学习/经验沉淀生产的 Tool/Skill 统一资产契约。
        # 仅做契约指南、归一化和校验；不写 Skill 注册表、不生产 Tool、不注册、不激活。
        self.registry.register(
            ToolDescriptor("learning_asset_contract_guide", "返回未来自主学习与经验总结产生 Tool/Skill 的统一资产契约格式。", "A2"),
            build_learning_asset_contract_guide_adapter(),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_contract_normalize", "把经验候选、Skill 草案、Tool 请求归一为 R16 统一资产契约。", "A2"),
            build_learning_asset_contract_normalize_adapter(
                self.learning_asset_contract,
                self.experience,
                self.skill_queue,
                self.tool_requests,
                self.registry.describe,
            ),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_contract_validate", "校验 R16 统一资产契约字段、usage card、chain recipe、风险和 no-pollution 边界。", "A2"),
            build_learning_asset_contract_validate_adapter(self.learning_asset_contract),
        )
        # L6.70.2-R17：对齐已存在的 L6.22 Tool 生产请求沙箱化与验证前置链。
        # 不新建真实执行沙箱，不生产 Tool，不注册 Tool，不释放句柄。
        self.registry.register(
            ToolDescriptor("learning_asset_sandbox_guide", "说明 R16 统一资产契约应如何接入已存在的 L6.22 Tool 生产请求沙箱化与验证前置链。", "A2"),
            build_learning_asset_sandbox_guide_adapter(),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_sandbox_align", "把 R16 Tool 类统一资产契约映射到 L6.22 ToolProductionRequest / SandboxValidationPlan。", "A2"),
            build_learning_asset_sandbox_align_adapter(self.learning_asset_sandbox, self.learning_asset_contract, self.tool_requests),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_sandbox_validate", "复核 R16 Tool 类统一资产契约是否已绑定 L6.22 沙箱前置计划；只校验不生产不注册。", "A2"),
            build_learning_asset_sandbox_validate_adapter(self.learning_asset_sandbox, self.learning_asset_contract, self.tool_requests),
        )
        # L6.70.2-R18：真实候选包生产沙箱。
        # 只在隔离 workspace 写候选包/扫描/smoke/回滚/审阅证据；不注册、不激活、不调用候选工具。
        self.registry.register(
            ToolDescriptor("learning_asset_candidate_sandbox_guide", "说明 R18 Tool/Skill 候选包生产沙箱的边界、链路和命令。", "A2"),
            build_learning_asset_candidate_sandbox_guide_adapter(),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_candidate_sandbox_build", "把已通过 R16/R17 的 Tool/Skill 契约落盘为隔离候选包，并生成静态扫描、smoke、回滚与审阅证据。", "A3"),
            build_learning_asset_candidate_sandbox_build_adapter(
                self.learning_asset_candidate_sandbox,
                self.learning_asset_contract,
                self.learning_asset_sandbox,
            ),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_candidate_sandbox_validate", "复核 R18 候选包 manifest、静态扫描、smoke 与边界断言；不注册不激活。", "A2"),
            build_learning_asset_candidate_sandbox_validate_adapter(self.learning_asset_candidate_sandbox),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_candidate_sandbox_review", "生成 R18 候选包注册审阅结论，仅供 LLM 决定后续质量门/发布门，不自动注册。", "A2"),
            build_learning_asset_candidate_sandbox_review_adapter(self.learning_asset_candidate_sandbox),
        )
        # L6.70.2-R19：执行力优先的轻量发布门。
        # 只生成质量门/发布门/回滚证据/注册申请四项结论；不注册、不激活。
        self.registry.register(
            ToolDescriptor("learning_asset_release_gate_guide", "说明 R19 候选 Tool/Skill 轻量发布门：四项直检，LLM 裁决，不自动注册。", "A2"),
            build_learning_asset_release_gate_guide_adapter(),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_release_gate_check", "把 R18 候选包审阅证据压成质量门、发布门、回滚证据和注册申请 ready 结论。", "A2"),
            build_learning_asset_release_gate_check_adapter(self.learning_asset_release_gate, self.learning_asset_candidate_sandbox),
        )
        # L6.70.2-R20：学习成功后的受控注册/激活闭环。
        # 通过 R19 后写 workspace active asset registry，并把 learned_* 注册到当前 Runtime，可立即 smoke 调用；不覆盖内置工具，不复制/导入 v1。
        self.registry.register(
            ToolDescriptor("learning_asset_activation_guide", "说明 R20 学习资产激活链：通过 R19 后注册 learned_* 并立即可用。", "A2"),
            build_learning_asset_activation_guide_adapter(),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_activation_apply", "将通过 R19 的 Tool/Skill 候选包写入 active asset registry，并把 learned_* 动态注册到 Runtime。", "A3"),
            build_learning_asset_activation_apply_adapter(self.learning_asset_activation, self.learning_asset_release_gate, self.learning_asset_candidate_sandbox),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_activation_status", "读取并加载 workspace 级 active learned assets，确认已激活工具/Skill 是否可用。", "A2"),
            build_learning_asset_activation_status_adapter(self.learning_asset_activation),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_activation_smoke", "对已激活 learned_* 资产执行受控 smoke 调用，证明 LLM 可立即使用。", "A3"),
            build_learning_asset_activation_smoke_adapter(self.learning_asset_activation),
        )
        # L6.70.2-R21：实用型 learned Tool Adapter 模板层。
        # 只提供纯函数/契约校验/项目诊断/文档生产辅助/经验复用模板；drill 仍经 R20 受控激活 learned_tool_*。
        self.registry.register(
            ToolDescriptor("learning_asset_adapter_guide", "说明 R21 学习资产实用型 Adapter 模板、边界和调用链。", "A2"),
            build_learning_asset_adapter_guide_adapter(self.learning_asset_adapter),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_adapter_template_list", "列出 R21 五类实用 learned Tool Adapter 模板及 usage card。", "A2"),
            build_learning_asset_adapter_template_list_adapter(self.learning_asset_adapter),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_adapter_template_normalize", "把模板选择和用户备注归一为 R21 adapter_template_spec。", "A2"),
            build_learning_asset_adapter_template_normalize_adapter(self.learning_asset_adapter),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_adapter_template_validate", "校验 R21 Adapter 模板 spec、AST、usage card、chain recipe 和无污染边界。", "A2"),
            build_learning_asset_adapter_template_validate_adapter(self.learning_asset_adapter),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_adapter_template_smoke", "对 R21 Adapter 模板执行参数内 smoke，验证模板不是空壳。", "A2"),
            build_learning_asset_adapter_template_smoke_adapter(self.learning_asset_adapter),
        )
        self.registry.register(
            ToolDescriptor("learning_asset_adapter_drill", "生成五类 R21 Adapter 候选包并经 R20 激活为可调用 learned_tool_*，再执行 smoke。", "A3"),
            build_learning_asset_adapter_drill_adapter(self.learning_asset_adapter),
        )
        self.last_result: RuntimeRunResult | None = None

    def run_text(
        self,
        user_message: str,
        *,
        workspace: str | Path | None = None,
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 20,
        planner_mode: str | PlannerMode = PlannerMode.RULE_ONLY,
        model_config: Any | None = None,
        model_client: Any | None = None,
        external_context_hint: str = "",
    ) -> RuntimeRunResult:
        context = TurnContext.create(user_message, workspace=workspace, tool_mode=tool_mode, max_steps=max_steps)
        self.learning_asset_activation.load_active_assets(workspace=context.workspace)
        intent = self.intent_bridge.classify(user_message)
        plan, planner_result = self._build_plan_for_text(
            user_message,
            planner_mode=planner_mode,
            model_config=model_config,
            model_client=model_client,
            max_steps=max_steps,
            context_hint=self._build_planner_context_hint(
                external_context_hint="\n\n".join(
                    part
                    for part in (external_context_hint, self._build_live_cognitive_context_hint(user_message, mutate_affective=True))
                    if part
                )
            ),
        )
        if plan:
            results, chain_summary, planner_execution_report = self._execute_plan_with_planner_controller(
                context,
                plan,
                task_id="runtime_text",
                run_id=context.turn_id,
            )
        else:
            results, chain_summary, planner_execution_report = [], None, None
        projection = build_public_projection(
            results,
            len(self.audit.events),
            chain_summary=chain_summary,
            pending_confirmations=self.ticket_store.public_pending(),
        )
        if planner_result is not None and not plan:
            projection = RuntimeProjection(
                status="planner_failed" if not planner_result.ok else "no_plan",
                summary=planner_result.message or projection.summary,
                artifacts=projection.artifacts,
                audit_count=projection.audit_count,
                chain=projection.chain,
                pending_confirmations=projection.pending_confirmations,
            )
        return self._remember(
            RuntimeRunResult(
                intent=intent,
                plan=plan,
                results=results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=chain_summary,
                pending_confirmations=self.ticket_store.public_pending(),
                planner_result=planner_result,
                planner_execution_report=planner_execution_report,
            )
        )


    def preview_plan(
        self,
        user_message: str,
        *,
        planner_mode: str | PlannerMode = PlannerMode.RULE_ONLY,
        model_config: Any | None = None,
        model_client: Any | None = None,
        max_steps: int = 20,
        external_context_hint: str = "",
    ) -> dict[str, Any]:
        plan, planner_result = self._build_plan_for_text(
            user_message,
            planner_mode=planner_mode,
            model_config=model_config,
            model_client=model_client,
            max_steps=max_steps,
            context_hint=self._build_planner_context_hint(
                external_context_hint="\n\n".join(
                    part
                    for part in (external_context_hint, self._build_live_cognitive_context_hint(user_message, mutate_affective=False))
                    if part
                )
            ),
        )
        return {
            "ok": bool(plan),
            "planner_mode": normalize_planner_mode(planner_mode).value,
            "steps": plan_to_public_dict(plan),
            "planner_result": planner_result.public_dict() if planner_result is not None else None,
        }

    def _build_plan_for_text(
        self,
        user_message: str,
        *,
        planner_mode: str | PlannerMode,
        model_config: Any | None,
        model_client: Any | None,
        max_steps: int,
        context_hint: str = "",
    ) -> tuple[list[ToolInvocation], ModelPlannerResult | None]:
        explicit_plan = self.plan_bridge.build_plan(user_message)
        if explicit_plan:
            return explicit_plan, None
        mode = normalize_planner_mode(planner_mode)
        if mode is PlannerMode.RULE_ONLY:
            return [], None
        planner_result = self.model_planner.build_plan(
            user_message,
            model_config=model_config,
            model_client=model_client,
            max_steps=max_steps,
            context_hint=context_hint,
        )
        if planner_result.ok:
            return planner_result.plan, planner_result
        return [], planner_result

    def run_model_chat(
        self,
        messages: list[dict[str, str]],
        *,
        model_config: Any,
        model_client: Any,
        workspace: str | Path | None = None,
        user_message: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 1,
    ) -> RuntimeRunResult:
        """通过 Runtime 执行链调用模型。

        L6.13 起，普通聊天不再直接由 shell 裸调 model_client；而是构造一个
        `model_chat` invocation，经 RiskClassifier、PermitGateway、Registry、Adapter、AuditBridge
        后返回结果。真实 messages/model_config/model_client 只放在 TurnContext，审计只记录安全摘要。
        """
        last_user = ""
        for message in reversed(messages):
            if message.get("role") == "user":
                last_user = str(message.get("content", ""))[:160]
                break
        invocation = ToolInvocation(
            "model_chat",
            {
                "provider": getattr(model_config, "provider", ""),
                "model": getattr(model_config, "model", ""),
                "messages_count": len(messages),
                "last_user_preview": last_user,
                "stream": bool(getattr(model_config, "stream", False)),
                "api_key_configured": bool(getattr(model_config, "has_real_api_key", False)),
            },
        )
        context = TurnContext.create(
            user_message or last_user or "model_chat",
            workspace=workspace,
            tool_mode=tool_mode,
            max_steps=max_steps,
            model_config=model_config,
            model_client=model_client,
            messages=messages,
        )
        results, chain_summary, planner_execution_report = self._execute_plan_with_planner_controller(
            context,
            [invocation],
            task_id="model_chat",
            run_id=context.turn_id,
        )
        projection = build_public_projection(
            results,
            len(self.audit.events),
            chain_summary=chain_summary,
            pending_confirmations=self.ticket_store.public_pending(),
        )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("model_chat", 1.0),
                plan=[invocation],
                results=results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=chain_summary,
                pending_confirmations=self.ticket_store.public_pending(),
                planner_execution_report=planner_execution_report,
            )
        )

    def execute_plan(
        self,
        plan: list[ToolInvocation],
        *,
        workspace: str | Path | None = None,
        user_message: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 20,
    ) -> RuntimeRunResult:
        context = TurnContext.create(user_message, workspace=workspace, tool_mode=tool_mode, max_steps=max_steps)
        self.learning_asset_activation.load_active_assets(workspace=context.workspace)
        results, chain_summary, planner_execution_report = self._execute_plan_with_planner_controller(
            context,
            plan,
            task_id="execute_plan",
            run_id=context.turn_id,
        )
        projection = build_public_projection(
            results,
            len(self.audit.events),
            chain_summary=chain_summary,
            pending_confirmations=self.ticket_store.public_pending(),
        )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("tool_task", 1.0),
                plan=plan,
                results=results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=chain_summary,
                pending_confirmations=self.ticket_store.public_pending(),
                planner_execution_report=planner_execution_report,
            )
        )

    def resume_plan(
        self,
        original_plan: list[ToolInvocation],
        *,
        previous_report: PlannerExecutionReport | dict[str, Any],
        workspace: str | Path | None = None,
        user_message: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 20,
    ) -> RuntimeRunResult:
        context = TurnContext.create(user_message or "resume_plan", workspace=workspace, tool_mode=tool_mode, max_steps=max_steps)
        runner = LongChainRunner(self.spine)
        results, chain_summary, planner_execution_report = self.planner_execution.execute_resume(
            context,
            original_plan,
            runner,
            previous_report=previous_report,
            task_id="resume_plan",
            run_id=context.turn_id,
        )
        projection = build_public_projection(
            results,
            len(self.audit.events),
            chain_summary=chain_summary,
            pending_confirmations=self.ticket_store.public_pending(),
        )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("tool_task_resume", 1.0),
                plan=original_plan,
                results=results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=chain_summary,
                pending_confirmations=self.ticket_store.public_pending(),
                planner_execution_report=planner_execution_report,
            )
        )


    def execute_suggestions(
        self,
        suggestions: list[PlanSuggestion | RepairSuggestion | QualityGateSuggestion | HandoffSuggestion],
        *,
        workspace: str | Path | None = None,
        user_message: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 20,
    ) -> RuntimeRunResult:
        bridge_result = self.suggestion_bridge.to_plan(suggestions)
        base = self.execute_plan(
            bridge_result.plan,
            workspace=workspace,
            user_message=user_message or "插件建议执行",
            tool_mode=tool_mode,
            max_steps=max_steps,
        )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("plugin_suggestion_task", 1.0),
                plan=base.plan,
                results=base.results,
                projection=base.projection,
                audit_events=base.audit_events,
                chain_summary=base.chain_summary,
                suggestion_bridge=bridge_result,
                pending_confirmations=self.ticket_store.public_pending(),
            )
        )

    def confirm_ticket(
        self,
        ticket_id: str,
        *,
        workspace: str | Path | None = None,
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 1,
    ) -> RuntimeRunResult:
        context = TurnContext.create(f"confirm {ticket_id}", workspace=workspace, tool_mode=tool_mode, max_steps=max_steps)
        result = self.spine.execute_confirmed_ticket(context, ticket_id)
        projection = build_public_projection([result], len(self.audit.events), pending_confirmations=self.ticket_store.public_pending())
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("confirm_ticket", 1.0),
                plan=[],
                results=[result],
                projection=projection,
                audit_events=self.audit.recent_summary(),
                pending_confirmations=self.ticket_store.public_pending(),
            )
        )

    def deny_ticket(self, ticket_id: str) -> dict[str, Any]:
        ticket = self.ticket_store.deny(ticket_id)
        if ticket is None:
            return {"ok": False, "ticket_id": ticket_id, "message": "确认票据不存在、已处理或已过期。"}
        return {"ok": True, "ticket": ticket.to_public_dict(), "message": "已拒绝确认票据。"}

    def pending_confirmations(self) -> list[dict[str, Any]]:
        return self.ticket_store.public_pending()

    def export_audit_jsonl(self, path: str | Path) -> Path:
        return self.audit.export_jsonl(path)

    def replay_audit_jsonl(self, path: str | Path) -> AuditReplaySummary:
        return replay_audit_events(AuditBridge.load_jsonl(path))

    def export_report(self, path: str | Path, result: RuntimeRunResult | None = None) -> Path:
        return export_runtime_report(result or self.last_result, path)

    def available_tools(self) -> list[ToolDescriptor]:
        return self.registry.describe()

    def context_snapshot(self) -> dict[str, Any]:
        return self.context_memory.snapshot().public_dict()

    def export_context_json(self, path: str | Path) -> Path:
        return self.context_memory.export_json(path)

    def reset_context_memory(self) -> None:
        self.context_memory.reset()



    def diagnosis_snapshot(self) -> dict[str, Any]:
        return self.diagnostics.public_dict()

    def export_diagnosis_json(self, path: str | Path) -> Path:
        return self.diagnostics.export_json(path)

    def reset_diagnosis(self) -> None:
        self.diagnostics.reset()

    def quality_gate_snapshot(self) -> dict[str, Any]:
        return self.quality_gate.public_dict()

    def export_quality_gate_json(self, path: str | Path) -> Path:
        return self.quality_gate.export_json(path)

    def reset_quality_gate(self) -> None:
        self.quality_gate.reset()

    def run_engineering_diagnosis(
        self,
        *,
        workspace: str | Path | None = None,
        path: str = ".",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 6,
        run_compileall: bool = True,
        run_pytest: bool = False,
    ) -> RuntimeRunResult:
        plan: list[ToolInvocation] = [ToolInvocation("scan_project", {"path": path})]
        if run_compileall:
            plan.append(ToolInvocation("run_python_quality_check", {"command": "compileall", "target": path}))
        if run_pytest:
            plan.append(ToolInvocation("run_python_quality_check", {"command": "pytest", "target": path}))
        plan.append(ToolInvocation("diagnose_project", {"path": path}))
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message=f"engineering_diagnosis {path}",
            tool_mode=tool_mode,
            max_steps=max_steps,
        )


    def run_quality_gate(
        self,
        *,
        workspace: str | Path | None = None,
        path: str = ".",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 10,
        require_pytest: bool = False,
        package_on_pass: bool = False,
        report_path: str = "reports/l6_18_quality_gate.md",
        package_target: str = "dist/l6_18_quality_gate_delivery.zip",
    ) -> RuntimeRunResult:
        """执行 L6.18 质量门。

        质量门本身作为 `evaluate_quality_gate` 工具进入 Runtime 审计链。
        后续打包只在 verdict.allow_package=True 且 package_on_pass=True 时追加执行，
        避免测试失败后仍自动发布交付包。
        """
        diagnosis_result = self.run_engineering_diagnosis(
            workspace=workspace,
            path=path,
            tool_mode=tool_mode,
            max_steps=min(max_steps, 8),
            run_compileall=True,
            run_pytest=require_pytest,
        )
        quality_payload = [
            {
                "tool_name": result.tool_name,
                "status": result.status.value,
                "error_code": result.error_code,
                "summary": result.output_summary,
                "returncode": result.data.get("returncode"),
                "argv": result.data.get("argv") or [],
                "audit_ref": result.audit_ref,
            }
            for result in diagnosis_result.results
            if result.tool_name == "run_python_quality_check"
        ]
        gate_plan = [
            ToolInvocation(
                "evaluate_quality_gate",
                {
                    "gate_name": "l6_18_default",
                    "quality_results": quality_payload,
                    "diagnosis": self.diagnostics.public_dict(),
                    "require_pytest": require_pytest,
                },
            )
        ]
        gate_result = self.execute_plan(
            gate_plan,
            workspace=workspace,
            user_message=f"quality_gate {path}",
            tool_mode=tool_mode,
            max_steps=1,
        )
        combined_results = list(diagnosis_result.results) + list(gate_result.results)
        combined_plan = list(diagnosis_result.plan) + list(gate_result.plan)

        verdict = self.quality_gate.last_verdict
        if verdict is not None:
            followup_plan = [ToolInvocation("write_workspace_file", {"path": report_path, "content": verdict.markdown_report()})]
            if package_on_pass and verdict.allow_package:
                followup_plan.append(ToolInvocation("create_zip_package", {"source": path, "target": package_target}))
            followup_result = self.execute_plan(
                followup_plan,
                workspace=workspace,
                user_message=f"quality_gate_report {path}",
                tool_mode=tool_mode,
                max_steps=max(1, max_steps - len(combined_results)),
            )
            combined_results.extend(followup_result.results)
            combined_plan.extend(followup_result.plan)
            chain_summary = followup_result.chain_summary or gate_result.chain_summary or diagnosis_result.chain_summary
        else:
            chain_summary = gate_result.chain_summary or diagnosis_result.chain_summary

        projection = build_public_projection(
            combined_results,
            len(self.audit.events),
            chain_summary=chain_summary,
            pending_confirmations=self.ticket_store.public_pending(),
        )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("quality_gate", 1.0),
                plan=combined_plan,
                results=combined_results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=chain_summary,
                pending_confirmations=self.ticket_store.public_pending(),
            )
        )

    def run_engineering_repair_loop(
        self,
        *,
        workspace: str | Path | None = None,
        path: str = ".",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 12,
        report_path: str = "reports/l6_17_engineering_diagnosis.md",
        package_target: str = "dist/l6_17_repair_loop_delivery.zip",
        external_context_hint: str = "",
    ) -> RuntimeRunResult:
        # CLI 会传入最近会话摘要；工程诊断/修复循环仍固定走 Runtime 工具链，
        # 这里只保持接口兼容，不把外部上下文写入报告或工具参数。
        _ = external_context_hint
        diagnosis_result = self.run_engineering_diagnosis(
            workspace=workspace,
            path=path,
            tool_mode=tool_mode,
            max_steps=min(max_steps, 8),
            run_pytest=True,
        )
        diagnosis = self.diagnostics.last_diagnosis
        if diagnosis is None:
            return diagnosis_result
        followup_plan = [
            ToolInvocation("write_workspace_file", {"path": report_path, "content": diagnosis.markdown_report()}),
            ToolInvocation("create_zip_package", {"source": path, "target": package_target}),
        ]
        report_result = self.execute_plan(
            followup_plan,
            workspace=workspace,
            user_message=f"engineering_repair_loop_report {path}",
            tool_mode=tool_mode,
            max_steps=max(1, max_steps - len(diagnosis_result.results)),
        )
        combined_results = list(diagnosis_result.results) + list(report_result.results)
        projection = build_public_projection(
            combined_results,
            len(self.audit.events),
            chain_summary=report_result.chain_summary or diagnosis_result.chain_summary,
            pending_confirmations=self.ticket_store.public_pending(),
        )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("engineering_repair_loop", 1.0),
                plan=list(diagnosis_result.plan) + list(report_result.plan),
                results=combined_results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=report_result.chain_summary or diagnosis_result.chain_summary,
                pending_confirmations=self.ticket_store.public_pending(),
            )
        )


    def delivery_snapshot(self) -> dict[str, Any]:
        return self.delivery.public_dict()

    def export_delivery_json(self, path: str | Path) -> Path:
        return self.delivery.export_json(path)

    def reset_delivery(self) -> None:
        self.delivery.reset()

    def run_release(
        self,
        *,
        workspace: str | Path | None = None,
        path: str = ".",
        target: str = "dist/l6_19_release_bundle.zip",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 14,
        require_pytest: bool = True,
        release_name: str = "linyuanzhe_l6_19_release",
        manifest_path: str = "",
    ) -> RuntimeRunResult:
        """执行 L6.19 标准发布流程。

        流程固定为：质量门（不做旧式临时打包）→ Release Gate → 标准 Release Bundle。
        fail / blocked / secret finding 会在 create_release_bundle adapter 内阻断，
        因而不会生成发布 ZIP。
        """
        gate_result = self.run_quality_gate(
            workspace=workspace,
            path=path,
            tool_mode=tool_mode,
            max_steps=min(max_steps, 10),
            require_pytest=require_pytest,
            package_on_pass=False,
            report_path="reports/l6_19_quality_gate.md",
        )
        release_plan = [
            ToolInvocation(
                "create_release_bundle",
                {
                    "source": path,
                    "target": target,
                    "release_name": release_name,
                    "baseline": "L6.18-quality-gate",
                    "manifest_path": manifest_path,
                },
            )
        ]
        release_result = self.execute_plan(
            release_plan,
            workspace=workspace,
            user_message=f"release_bundle {path} -> {target}",
            tool_mode=tool_mode,
            max_steps=1,
        )
        combined_results = list(gate_result.results) + list(release_result.results)
        combined_plan = list(gate_result.plan) + list(release_result.plan)
        projection = build_public_projection(
            combined_results,
            len(self.audit.events),
            chain_summary=release_result.chain_summary or gate_result.chain_summary,
            pending_confirmations=self.ticket_store.public_pending(),
        )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("release_bundle", 1.0),
                plan=combined_plan,
                results=combined_results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=release_result.chain_summary or gate_result.chain_summary,
                pending_confirmations=self.ticket_store.public_pending(),
            )
        )

    def experience_snapshot(self) -> dict[str, Any]:
        return self.experience.public_dict()

    def export_experience_json(self, path: str | Path) -> Path:
        return self.experience.export_json(path)

    def reset_experience(self) -> None:
        self.experience.reset()

    def run_experience_synthesis(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 2,
        max_candidates: int = 12,
    ) -> RuntimeRunResult:
        plan = [
            ToolInvocation(
                "synthesize_experience_candidates",
                {"notes": notes, "max_candidates": max_candidates},
            )
        ]
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="experience_synthesis",
            tool_mode=tool_mode,
            max_steps=max_steps,
        )

    def skill_queue_snapshot(self) -> dict[str, Any]:
        return self.skill_queue.public_dict()

    def export_skill_queue_json(self, path: str | Path) -> Path:
        return self.skill_queue.export_json(path)

    def reset_skill_queue(self) -> None:
        self.skill_queue.reset()

    def run_skill_queue_build(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 3,
        max_items: int = 20,
        refresh_experience: bool = True,
    ) -> RuntimeRunResult:
        plan: list[ToolInvocation] = []
        # 执行力优先：有备注或尚无经验报告时，先补一次经验沉淀，再把 Skill 候选版本化入队。
        if refresh_experience or self.experience.last_report is None:
            plan.append(ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": max_items}))
        plan.append(ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": max_items}))
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="skill_queue_build",
            tool_mode=tool_mode,
            max_steps=max_steps,
        )

    def tool_request_snapshot(self) -> dict[str, Any]:
        return self.tool_requests.public_dict()

    def export_tool_request_json(self, path: str | Path) -> Path:
        return self.tool_requests.export_json(path)

    def reset_tool_requests(self) -> None:
        self.tool_requests.reset()

    def run_tool_request_build(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 3,
        max_items: int = 20,
        refresh_experience: bool = True,
    ) -> RuntimeRunResult:
        plan: list[ToolInvocation] = []
        # 执行力优先：先把缺工具经验转成 ToolGapCandidate，再进入生产请求与沙箱验证前置队列。
        if refresh_experience or self.experience.last_report is None:
            plan.append(ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": max_items}))
        plan.append(ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": max_items}))
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="tool_request_build",
            tool_mode=tool_mode,
            max_steps=max_steps,
        )

    def exoskeleton_snapshot(self) -> dict[str, Any]:
        return self.exoskeleton.public_dict()

    def export_exoskeleton_json(self, path: str | Path) -> Path:
        return self.exoskeleton.export_json(path)

    def reset_exoskeleton(self) -> None:
        self.exoskeleton.reset()

    def project_repair_snapshot(self) -> dict[str, Any]:
        return self.project_repair.public_dict()

    def export_project_repair_json(self, path: str | Path) -> Path:
        return self.project_repair.export_json(path)

    def reset_project_repair(self) -> None:
        self.project_repair.reset()

    def run_project_repair_plan(
        self,
        *,
        workspace: str | Path | None = None,
        path: str = ".",
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 8,
        run_compileall: bool = True,
        run_pytest: bool = False,
        max_targets: int = 12,
    ) -> RuntimeRunResult:
        # L6.25：项目雷达 + 工程修复外壳闭环。
        # 只生成 PatchPlan / RegressionHint / RollbackEvidence；不应用补丁、不写文件、不注册工具、不改内核。
        pre_plan: list[ToolInvocation] = [ToolInvocation("scan_project", {"path": path})]
        if run_compileall:
            pre_plan.append(ToolInvocation("run_python_quality_check", {"command": "compileall", "target": path}))
        if run_pytest:
            pre_plan.append(ToolInvocation("run_python_quality_check", {"command": "pytest", "target": path}))
        pre_plan.append(ToolInvocation("diagnose_project", {"path": path}))
        pre_result = self.execute_plan(
            pre_plan,
            workspace=workspace,
            user_message=f"project_repair_precheck {path}",
            tool_mode=tool_mode,
            max_steps=min(max_steps, max(1, len(pre_plan))),
        )
        quality_payload = [
            {
                "tool_name": result.tool_name,
                "status": result.status.value,
                "error_code": result.error_code,
                "summary": result.output_summary,
                "returncode": result.data.get("returncode"),
                "argv": result.data.get("argv") or [],
                "audit_ref": result.audit_ref,
            }
            for result in pre_result.results
            if result.tool_name == "run_python_quality_check"
        ]
        repair_plan = [
            ToolInvocation(
                "build_project_repair_plan",
                {
                    "path": path,
                    "notes": notes,
                    "max_targets": max_targets,
                    "quality_results": quality_payload,
                },
            )
        ]
        repair_result = self.execute_plan(
            repair_plan,
            workspace=workspace,
            user_message=f"project_repair_plan {path}",
            tool_mode=tool_mode,
            max_steps=1,
        )
        combined_results = list(pre_result.results) + list(repair_result.results)
        combined_plan = list(pre_result.plan) + list(repair_result.plan)
        projection = build_public_projection(
            combined_results,
            len(self.audit.events),
            chain_summary=repair_result.chain_summary or pre_result.chain_summary,
            pending_confirmations=self.ticket_store.public_pending(),
        )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("project_repair_plan", 1.0),
                plan=combined_plan,
                results=combined_results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=repair_result.chain_summary or pre_result.chain_summary,
                pending_confirmations=self.ticket_store.public_pending(),
            )
        )



    def delivery_standardization_snapshot(self) -> dict[str, Any]:
        return self.delivery_standardization.public_dict()

    def export_delivery_standardization_json(self, path: str | Path) -> Path:
        return self.delivery_standardization.export_json(path)

    def reset_delivery_standardization(self) -> None:
        self.delivery_standardization.reset()

    def provider_adaptation_snapshot(self) -> dict[str, Any]:
        return self.provider_adaptation.public_dict()

    def export_provider_adaptation_json(self, path: str | Path) -> Path:
        return self.provider_adaptation.export_json(path)

    def reset_provider_adaptation(self) -> None:
        self.provider_adaptation.reset()

    def run_provider_adaptation(
        self,
        *,
        workspace: str | Path | None = None,
        path: str = ".",
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 8,
        refresh_shell_mount: bool = True,
        refresh_delivery_standard: bool = False,
    ) -> RuntimeRunResult:
        # L6.27：Provider 适配外壳。
        # 只读取 L4 factsheet/mapper 声明，生成 ProviderProfile/CapabilityMatrix/API Surface/GovernanceMount；
        # 不触网、不读密钥、不导入 provider SDK、不注册正式适配器、不改 tiangong_kernel。
        pre_plan: list[ToolInvocation] = []
        if refresh_shell_mount:
            pre_plan.append(ToolInvocation("build_shell_system_mount", {"notes": notes or "L6.27 Provider 适配前置壳装状态刷新。"}))
        if refresh_delivery_standard:
            pre_plan.append(ToolInvocation("build_delivery_standardization", {"notes": notes, "path": path}))
        pre_result = self.execute_plan(
            pre_plan,
            workspace=workspace,
            user_message=f"provider_adaptation_precheck {path}",
            tool_mode=tool_mode,
            max_steps=min(max_steps, max(1, len(pre_plan))) if pre_plan else 1,
        ) if pre_plan else None
        provider_result = self.execute_plan(
            [ToolInvocation("build_provider_adaptation", {"notes": notes, "path": path})],
            workspace=workspace,
            user_message=f"provider_adaptation {path}",
            tool_mode=tool_mode,
            max_steps=1,
        )
        combined_results = (list(pre_result.results) if pre_result else []) + list(provider_result.results)
        combined_plan = (list(pre_result.plan) if pre_result else []) + list(provider_result.plan)
        projection = build_public_projection(
            combined_results,
            len(self.audit.events),
            chain_summary=provider_result.chain_summary or (pre_result.chain_summary if pre_result else None),
            pending_confirmations=self.ticket_store.public_pending(),
        )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("provider_adaptation", 1.0),
                plan=combined_plan,
                results=combined_results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=provider_result.chain_summary or (pre_result.chain_summary if pre_result else None),
                pending_confirmations=self.ticket_store.public_pending(),
            )
        )

    def learning_convergence_snapshot(self) -> dict[str, Any]:
        return self.learning_convergence.public_dict()

    def export_learning_convergence_json(self, path: str | Path) -> Path:
        return self.learning_convergence.export_json(path)

    def reset_learning_convergence(self) -> None:
        self.learning_convergence.reset()

    def run_learning_convergence_build(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 6,
        max_items: int = 18,
        refresh_sources: bool = True,
    ) -> RuntimeRunResult:
        # L6.28：把经验、Skill 草案、Tool 请求和外骨骼输出合流成下一轮 Planner 可直接消费的执行卡片。
        # 执行力第一：刷新候选链后立即合流；但不写记忆、不注册/激活 Skill、不生产 Tool、不改内核。
        plan: list[ToolInvocation] = []
        if refresh_sources or self.experience.last_report is None:
            plan.append(ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": max_items}))
        if refresh_sources or self.skill_queue.last_report is None:
            plan.append(ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": max_items}))
        if refresh_sources or self.tool_requests.last_report is None:
            plan.append(ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": max_items}))
        if refresh_sources or self.exoskeleton.last_report is None:
            plan.append(ToolInvocation("build_execution_exoskeleton", {"notes": notes, "max_items": max_items}))
        plan.append(ToolInvocation("build_learning_convergence", {"notes": notes, "max_items": max_items}))
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="learning_convergence_build",
            tool_mode=tool_mode,
            max_steps=min(max_steps, max(1, len(plan))),
        )


    def recovery_coordination_snapshot(self) -> dict[str, Any]:
        return self.recovery_coordination.public_dict()

    def export_recovery_coordination_json(self, path: str | Path) -> Path:
        return self.recovery_coordination.export_json(path)

    def reset_recovery_coordination(self) -> None:
        self.recovery_coordination.reset()

    def run_recovery_coordination_build(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 8,
        max_items: int = 12,
        refresh_sources: bool = True,
    ) -> RuntimeRunResult:
        # L6.29：把失败诊断、修复候选、Handoff 摘要、预算投影和续接计划压成恢复路径。
        # 执行力第一：给下一轮可直接消费的恢复顺序；但不派生子智能体、不执行补丁、不改预算、不改内核。
        plan: list[ToolInvocation] = []
        if refresh_sources or self.learning_convergence.last_report is None:
            plan.append(ToolInvocation("build_learning_convergence", {"notes": notes, "max_items": max_items}))
        if refresh_sources or self.project_repair.last_report is None:
            plan.append(ToolInvocation("build_project_repair_plan", {"path": ".", "notes": notes or "L6.29 恢复协调前置工程修复计划。", "max_targets": max_items}))
        plan.append(ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": max_items, "step_budget": max_steps}))
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="recovery_coordination_build",
            tool_mode=tool_mode,
            max_steps=min(max_steps, max(1, len(plan))),
        )


    def governance_execution_snapshot(self) -> dict[str, Any]:
        return self.governance_execution.public_dict()

    def export_governance_execution_json(self, path: str | Path) -> Path:
        return self.governance_execution.export_json(path)

    def reset_governance_execution(self) -> None:
        self.governance_execution.reset()

    def run_governance_execution_build(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 8,
        max_items: int = 12,
        refresh_sources: bool = True,
    ) -> RuntimeRunResult:
        # L6.30：治理执行力化。把治理从“刹车”压成“护栏”：A0-A4 草案/分析/smoke/续接快车道，A5 硬边界。
        # 本阶段只生成治理执行提示，不修改 PermitGateway / ExecutionPolicy，不确认票据，不执行副作用，不改内核。
        plan: list[ToolInvocation] = []
        if refresh_sources or self.recovery_coordination.last_report is None:
            plan.append(ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": max_items, "step_budget": max_steps}))
        if refresh_sources or self.delivery_standardization.last_report is None:
            plan.append(ToolInvocation("build_delivery_standardization", {"path": ".", "notes": notes or "L6.30 治理执行力化前置交付证据。"}))
        if refresh_sources or self.provider_adaptation.last_report is None:
            plan.append(ToolInvocation("build_provider_adaptation", {"path": ".", "notes": notes or "L6.30 Provider 治理声明式约束。"}))
        plan.append(ToolInvocation("build_governance_execution", {"notes": notes, "max_items": max_items}))
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="governance_execution_build",
            tool_mode=tool_mode,
            max_steps=min(max_steps, max(1, len(plan))),
        )


    def planner_context_snapshot(self) -> dict[str, Any]:
        return self.planner_context.public_dict()

    def export_planner_context_json(self, path: str | Path) -> Path:
        return self.planner_context.export_json(path)

    def reset_planner_context(self) -> None:
        self.planner_context.reset()

    def planner_execution_snapshot(self) -> dict[str, Any]:
        return self.planner_execution.public_dict()


    def execution_chain_contract_snapshot(self) -> dict[str, Any]:
        """L6.37：返回执行链冻结契约，不执行工具。"""
        return build_default_execution_chain_contract().public_dict()

    def export_execution_chain_contract_json(self, path: str | Path) -> Path:
        return build_default_execution_chain_contract().export_json(path)

    def execution_chain_freeze_snapshot(self) -> dict[str, Any]:
        """L6.37：基于最近 PlannerExecutionReport 生成冻结验收报告。"""
        return build_execution_chain_freeze_report(self.planner_execution_snapshot()).public_dict()

    def export_execution_chain_freeze_json(self, path: str | Path) -> Path:
        report = build_execution_chain_freeze_report(self.planner_execution_snapshot())
        return report.export_json(path)

    def export_planner_execution_json(self, path: str | Path) -> Path:
        return self.planner_execution.export_json(path)

    def reset_planner_execution(self) -> None:
        self.planner_execution.reset()

    def run_planner_execution_task(
        self,
        user_message: str,
        *,
        workspace: str | Path | None = None,
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 20,
        planner_mode: str | PlannerMode = PlannerMode.RULE_ONLY,
        model_config: Any | None = None,
        model_client: Any | None = None,
        refresh_planner_context: bool = False,
        external_context_hint: str = "",
    ) -> RuntimeRunResult:
        # L6.32：Planner 驱动真实执行主链。模型/规则只生成 plan，执行仍由 LongChainRunner + ExecutionSpine 接管。
        if refresh_planner_context and self.planner_context.last_report is None:
            self.run_planner_context_build(
                workspace=workspace,
                notes="L6.32 Planner 执行主链前置上下文刷新。",
                tool_mode=tool_mode,
                max_steps=min(max_steps, 10),
                max_items=16,
                refresh_sources=True,
            )
        context = TurnContext.create(user_message, workspace=workspace, tool_mode=tool_mode, max_steps=max_steps)
        plan, planner_result = self._build_plan_for_text(
            user_message,
            planner_mode=planner_mode,
            model_config=model_config,
            model_client=model_client,
            max_steps=max_steps,
            context_hint=self._build_planner_context_hint(
                external_context_hint="\n\n".join(
                    part
                    for part in (external_context_hint, self._build_live_cognitive_context_hint(user_message, mutate_affective=True))
                    if part
                )
            ),
        )
        if plan:
            results, chain_summary, planner_execution_report = self._execute_plan_with_planner_controller(
                context,
                plan,
                task_id="l6_32_planner_execution",
                run_id=context.turn_id,
            )
        else:
            results, chain_summary, planner_execution_report = [], None, None
        projection = build_public_projection(
            results,
            len(self.audit.events),
            chain_summary=chain_summary,
            pending_confirmations=self.ticket_store.public_pending(),
        )
        if planner_result is not None and not plan:
            projection = RuntimeProjection(
                status="planner_failed" if not planner_result.ok else "no_plan",
                summary=planner_result.message or projection.summary,
                artifacts=projection.artifacts,
                audit_count=projection.audit_count,
                chain=projection.chain,
                pending_confirmations=projection.pending_confirmations,
            )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("planner_execution", 1.0),
                plan=plan,
                results=results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=chain_summary,
                pending_confirmations=self.ticket_store.public_pending(),
                planner_result=planner_result,
                planner_execution_report=planner_execution_report,
            )
        )

    def run_planner_context_build(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 10,
        max_items: int = 16,
        refresh_sources: bool = True,
    ) -> RuntimeRunResult:
        # L6.31：统一 Planner 接入。把 L6.24-L6.30 外壳输出压缩为单一 UnifiedPlannerContext。
        # 本阶段只生成 Planner 上下文和执行草案，不执行工具、不注册 Tool/Skill/Provider、不读取密钥、不改内核。
        plan: list[ToolInvocation] = []
        if refresh_sources or self.shell_mount.last_report is None:
            plan.append(ToolInvocation("build_shell_system_mount", {"notes": notes or "L6.31 统一 Planner 前置壳装状态刷新。"}))
        if refresh_sources or self.learning_convergence.last_report is None:
            plan.append(ToolInvocation("build_learning_convergence", {"notes": notes, "max_items": max_items}))
        if refresh_sources or self.recovery_coordination.last_report is None:
            plan.append(ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": max_items, "step_budget": max_steps}))
        if refresh_sources or self.delivery_standardization.last_report is None:
            plan.append(ToolInvocation("build_delivery_standardization", {"path": ".", "notes": notes or "L6.31 统一 Planner 前置交付证据。"}))
        if refresh_sources or self.provider_adaptation.last_report is None:
            plan.append(ToolInvocation("build_provider_adaptation", {"path": ".", "notes": notes or "L6.31 Provider 声明式候选汇总。"}))
        if refresh_sources or self.governance_execution.last_report is None:
            plan.append(ToolInvocation("build_governance_execution", {"notes": notes, "max_items": max_items}))
        plan.append(ToolInvocation("build_planner_context", {"notes": notes, "max_items": max_items, "task_id": "l6_31_unified_planner"}))
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="planner_context_build",
            tool_mode=tool_mode,
            max_steps=min(max_steps, max(1, len(plan))),
        )


    def run_delivery_standardization(
        self,
        *,
        workspace: str | Path | None = None,
        path: str = ".",
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 10,
        run_compileall: bool = True,
        run_pytest: bool = False,
    ) -> RuntimeRunResult:
        # L6.26：交付链标准化外壳。
        # 汇总 ChangeSet / TestEvidence / ManifestEvidence / IntegrityEvidence / TodoReport；
        # 不生成正式发布 ZIP、不应用补丁、不写文件、不注册工具、不改 tiangong_kernel。
        pre_plan: list[ToolInvocation] = [ToolInvocation("scan_project", {"path": path})]
        if run_compileall:
            pre_plan.append(ToolInvocation("run_python_quality_check", {"command": "compileall", "target": path}))
        if run_pytest:
            pre_plan.append(ToolInvocation("run_python_quality_check", {"command": "pytest", "target": path}))
        pre_plan.append(ToolInvocation("diagnose_project", {"path": path}))
        pre_result = self.execute_plan(
            pre_plan,
            workspace=workspace,
            user_message=f"delivery_standard_precheck {path}",
            tool_mode=tool_mode,
            max_steps=min(max_steps, max(1, len(pre_plan))),
        )
        quality_payload = [
            {
                "tool_name": result.tool_name,
                "status": result.status.value,
                "error_code": result.error_code,
                "summary": result.output_summary,
                "returncode": result.data.get("returncode"),
                "argv": result.data.get("argv") or [],
                "audit_ref": result.audit_ref,
            }
            for result in pre_result.results
            if result.tool_name == "run_python_quality_check"
        ]
        gate_result = self.execute_plan(
            [
                ToolInvocation(
                    "evaluate_quality_gate",
                    {
                        "gate_name": "l6_26_delivery_standardization",
                        "quality_results": quality_payload,
                        "diagnosis": self.diagnostics.public_dict(),
                        "require_pytest": run_pytest,
                    },
                )
            ],
            workspace=workspace,
            user_message=f"delivery_standard_quality_gate {path}",
            tool_mode=tool_mode,
            max_steps=1,
        )
        repair_result = self.execute_plan(
            [
                ToolInvocation(
                    "build_project_repair_plan",
                    {
                        "path": path,
                        "notes": notes or "L6.26 交付链标准化前置工程修复计划。",
                        "max_targets": 12,
                        "quality_results": quality_payload,
                    },
                )
            ],
            workspace=workspace,
            user_message=f"delivery_standard_repair_plan {path}",
            tool_mode=tool_mode,
            max_steps=1,
        )
        standard_result = self.execute_plan(
            [ToolInvocation("build_delivery_standardization", {"notes": notes, "path": path})],
            workspace=workspace,
            user_message=f"delivery_standardization {path}",
            tool_mode=tool_mode,
            max_steps=1,
        )
        combined_results = list(pre_result.results) + list(gate_result.results) + list(repair_result.results) + list(standard_result.results)
        combined_plan = list(pre_result.plan) + list(gate_result.plan) + list(repair_result.plan) + list(standard_result.plan)
        projection = build_public_projection(
            combined_results,
            len(self.audit.events),
            chain_summary=standard_result.chain_summary or repair_result.chain_summary or gate_result.chain_summary or pre_result.chain_summary,
            pending_confirmations=self.ticket_store.public_pending(),
        )
        return self._remember(
            RuntimeRunResult(
                intent=IntentResult("delivery_standardization", 1.0),
                plan=combined_plan,
                results=combined_results,
                projection=projection,
                audit_events=self.audit.recent_summary(),
                chain_summary=standard_result.chain_summary or repair_result.chain_summary or gate_result.chain_summary or pre_result.chain_summary,
                pending_confirmations=self.ticket_store.public_pending(),
            )
        )

    def shell_mount_snapshot(self) -> dict[str, Any]:
        return self.shell_mount.public_dict()

    def export_shell_mount_json(self, path: str | Path) -> Path:
        return self.shell_mount.export_json(path)

    def reset_shell_mount(self) -> None:
        self.shell_mount.reset()

    def _shell_mount_state(self) -> dict[str, Any]:
        return {
            "available_tools": self.registry.names(),
            "available_modules": discover_runtime_module_files(),
        }

    def run_shell_mount_build(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 1,
    ) -> RuntimeRunResult:
        # L6.24 壳装：只读取 Runtime 已装模块/工具注册表，生成 18 系统挂载报告；
        # 不注册正式工具、不激活 Skill、不释放句柄、不修改 tiangong_kernel。
        plan = [ToolInvocation("build_shell_system_mount", {"notes": notes})]
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="shell_system_mount_build",
            tool_mode=tool_mode,
            max_steps=max_steps,
        )

    def run_exoskeleton_build(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 4,
        max_items: int = 12,
        refresh_candidates: bool = True,
    ) -> RuntimeRunResult:
        plan: list[ToolInvocation] = []
        # L6.23 外骨骼模式：把候选链压缩为 PlannerHint + ToolCandidateTicket；
        # 质量门只卡正式注册/激活/发布，不阻断草案生成和续接。
        if refresh_candidates or self.experience.last_report is None:
            plan.append(ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": max_items}))
        if refresh_candidates or self.skill_queue.last_report is None:
            plan.append(ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": max_items}))
        if refresh_candidates or self.tool_requests.last_report is None:
            plan.append(ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": max_items}))
        plan.append(ToolInvocation("build_execution_exoskeleton", {"notes": notes, "max_items": max_items}))
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="execution_exoskeleton_build",
            tool_mode=tool_mode,
            max_steps=max_steps,
        )

    def project_snapshot(self) -> dict[str, Any]:
        return self.project_index.public_dict()

    def export_project_json(self, path: str | Path) -> Path:
        return self.project_index.export_json(path)

    def reset_project_index(self) -> None:
        self.project_index.reset()

    def _execute_plan_with_planner_controller(
        self,
        context: TurnContext,
        plan: list[ToolInvocation],
        *,
        task_id: str,
        run_id: str,
    ) -> tuple[list[ToolResult], LongChainRunSummary, PlannerExecutionReport]:
        runner = LongChainRunner(self.spine)
        planner_context_digest = ""
        if self.planner_context.last_report is not None:
            planner_context_digest = self.planner_context.last_report.report_digest
        return self.planner_execution.execute(
            context,
            plan,
            runner,
            task_id=task_id,
            run_id=run_id,
            planner_context_digest=planner_context_digest,
        )

    def _build_live_cognitive_context_hint(
        self,
        user_message: str,
        *,
        mutate_affective: bool = True,
        now: float | None = None,
    ) -> str:
        """L6.49.3：Runtime 统一接活四主路径只读/候选接口。

        边界：
        - 情志只产生 Planner hint，不授权、不拒绝、不调工具；
        - 记忆召回只读摘要，不注入原文、不写长期记忆；
        - 遗忘只产生 review decision，不物理删除、不改 MemoryStore；
        - 生命周期/四路径/预算/Planner 消费层只产出候选投影，不执行副作用；
        - 不吞 TypeError。调用失败必须落到 snapshot，便于测试与修理。
        """
        now_ts = float(now if now is not None else time())
        emotion_sources, desire_sources = self._derive_affective_sources(user_message)
        previous = self._affective_state
        elapsed = 0.0
        if self._last_affective_update_at is not None:
            elapsed = max(0.0, now_ts - self._last_affective_update_at)
        state = self._affective_engine.evolve(
            emotion_sources,
            desire_sources,
            previous_state=previous,
            elapsed_seconds=elapsed,
        )
        route = self._affective_router.route(state)
        if mutate_affective:
            self._affective_state = state
            self._affective_route = route
            self._last_affective_update_at = now_ts
            self._affective_turn_count += 1

        memory_route = self._run_memory_recall(user_message, now=now_ts)
        decisions = self._run_forgetting_reviews(limit=10, now=now_ts)
        self._last_forget_review_decisions = tuple(decisions)

        budget_report = self.budget_low_friction.evaluate([], budget_snapshot=self._build_runtime_budget_snapshot())
        lifecycle_bundle = self.lifecycle_coordinator.build_bundle(
            planner_report=self.planner_execution.last_report,
            recovery_ticket=getattr(self.p0_system_integration_two, "recovery", None),
            quality_gate=getattr(self.p0_system_integration_two, "quality_gate", None) or self.quality_gate.public_dict(),
            replay_quality=None,
            learning_report=getattr(self.learning_convergence, "last_report", None),
            memory_evidence=memory_route,
            active_user_task=True,
            user_allowed_autonomy=False,
            user_requested_learning=self._message_has_any(user_message, "学习", "沉淀", "经验", "总结", "skill"),
            user_confirmed_iteration=self._message_has_any(user_message, "确认迭代", "同意迭代", "执行迭代", "热切换"),
            idle_seconds=0.0,
            budget_pressure=float(budget_report.decision.pressure_signal.step_pressure_score),
            context_pressure=self._context_pressure_hint(memory_route),
            safety_or_credential_risk=self._message_has_any(user_message, "a5", "高危", "泄露", "凭证", "密钥", "不可逆"),
            notes="Runtime live context wiring; projection-only.",
        )
        self._last_lifecycle_bundle = lifecycle_bundle

        four_path_report = self.four_path_context.build(
            user_task=user_message,
            memory_route=memory_route,
            affective_route=route,
            lifecycle_bundle=lifecycle_bundle,
            provider_envelope=getattr(self.p0_system_integration, "provider", None) or self.provider_adaptation.public_dict(),
            budget_snapshot=budget_report,
            skill_envelope=getattr(self.p0_system_integration, "skill", None) or self.skill_queue.public_dict(),
            handoff_envelope=getattr(self.p0_system_integration, "handoff", None),
            audit_evidence={"recent_events": self.audit.recent_summary(), "summary_only": True},
            recovery_ticket=getattr(self.p0_system_integration_two, "recovery", None),
            quality_gate=getattr(self.p0_system_integration_two, "quality_gate", None) or self.quality_gate.public_dict(),
            notes="Runtime live four-path context; no execution.",
        )
        self._last_four_path_report = four_path_report
        planner_consumption = self.planner_unified_consumption.consume(four_path_report, plan=[])
        self._last_planner_consumption_report = planner_consumption

        lines = [
            "L6.49.3 RuntimeLiveInterfaceHint：情志/记忆召回/遗忘/生命周期/四路径/预算/Planner消费层已由 Runtime 接线；只输出 Planner hint/review，不执行副作用。",
            f"affective_turn_count={self._affective_turn_count}",
            f"affective_route={route.route_id}",
            f"dominant_emotion={route.dominant_emotion}; dominant_desire={route.dominant_desire}",
            f"risk_attention={route.planner_hint.risk_attention_hint:.3f}; recovery_patience={route.planner_hint.recovery_patience_hint:.3f}; pacing={route.planner_hint.long_chain_pacing_hint:.3f}; memory_modulation={route.planner_hint.memory_modulation_hint:.3f}",
            "affective_boundary=not_authorization/not_refusal/no_tool_dispatch/no_quality_gate_override",
            f"memory_recall_count={len(memory_route.hints) if memory_route is not None else 0}",
            f"forget_review_count={len(decisions)}",
            f"budget_low_friction_status={budget_report.status}",
            f"lifecycle_hint_count={len(lifecycle_bundle.planner_hints)}",
            f"four_path_status={four_path_report.status}; four_path_digest={four_path_report.report_digest}",
            f"planner_consumption_status={planner_consumption.status}",
        ]
        if self._last_memory_recall_error:
            lines.append(f"memory_recall_error={self._last_memory_recall_error[:160]}")
        if self._last_forget_review_error:
            lines.append(f"forget_review_error={self._last_forget_review_error[:160]}")
        for hint in list(memory_route.hints)[:3] if memory_route is not None else []:
            lines.append(f"memory_recall memory={hint.memory_id} score={hint.recall_score:.3f}")
        for decision in decisions[:3]:
            actions = ",".join(decision.recommended_actions)
            lines.append(f"forget_review memory={decision.memory_id} score={decision.forgetting_score:.3f} actions={actions}")
        return "\n".join(lines)[:2600]

    def _derive_affective_sources(self, user_message: str) -> tuple[SevenEmotionSignalSources, SixDesireSignalSources]:
        text = str(user_message or "").lower()

        def has_any(*tokens: str) -> bool:
            return any(token.lower() in text for token in tokens)

        risk = 0.0
        if has_any("风险", "危险", "高危", "a5", "失败", "崩溃", "回滚", "不可逆", "泄露", "污染", "bug", "报错", "错"):
            risk = 0.72
        if has_any("确认", "复核", "质检", "验证", "审计", "诊断"):
            risk = max(risk, 0.45)
        joy = 0.35 if has_any("通过", "完成", "成功", "正常", "可以", "很好") else 0.10
        reflection = 0.65 if has_any("看看", "确认", "分析", "诊断", "为什么", "是否", "检查", "复核") else 0.30
        novelty = 0.60 if has_any("下一步", "新", "接入", "模拟", "发布") else 0.20
        obstruction = 0.65 if has_any("不对", "问题", "bug", "报错", "失败", "错", "修复") else 0.10
        loss = 0.55 if has_any("丢失", "失败", "崩溃", "不可用", "没跑起来") else 0.05
        threat = 0.78 if has_any("a5", "高危", "不可逆", "泄露", "污染", "删除") else max(0.15, risk * 0.55)
        fatigue = 0.35 if has_any("长链", "连续", "压测", "多轮", "超时") else 0.10
        order = 0.72 if has_any("修复", "验证", "质检", "冻结", "基线", "回归", "契约") else 0.35
        achievement = 0.72 if has_any("完成", "修复", "执行", "交付", "推进", "下一步") else 0.45
        curiosity = 0.55 if has_any("看看", "确认", "为什么", "搜搜", "论文", "是否") else 0.25
        connection = 0.35 if has_any("大哥", "公子", "妾身", "咱们") else 0.20
        survival = max(0.18, threat)
        return (
            SevenEmotionSignalSources(
                joy_reward_signal=clamp01(joy),
                obstruction_violation_signal=clamp01(obstruction),
                uncertainty_future_risk_signal=clamp01(risk),
                reflection_load_signal=clamp01(reflection),
                loss_failure_signal=clamp01(loss),
                threat_irreversible_signal=clamp01(threat),
                novelty_prediction_error_signal=clamp01(novelty),
            ),
            SixDesireSignalSources(
                survival_resource_boundary_signal=clamp01(survival),
                curiosity_knowledge_gap_signal=clamp01(curiosity),
                achievement_goal_gap_signal=clamp01(achievement),
                connection_alignment_signal=clamp01(connection),
                order_entropy_signal=clamp01(order),
                rest_fatigue_recovery_signal=clamp01(fatigue),
            ),
        )

    def _message_has_any(self, user_message: str, *tokens: str) -> bool:
        text = str(user_message or "").lower()
        return any(str(token).lower() in text for token in tokens)

    def _run_memory_recall(self, user_message: str, *, now: float | None = None) -> L640MemoryRecallRoute | None:
        self._last_memory_recall_error = ""
        if self._memory_store is None:
            self._last_memory_recall_route = None
            return None
        try:
            route = MemoryRecallRouter(self._memory_store).route(user_message, top_k=5, now=now)
        except Exception as exc:  # 不静默吞掉；接口错配必须可见。
            self._last_memory_recall_error = f"{type(exc).__name__}: {exc}"
            raise
        self._last_memory_recall_route = route
        return route

    def _context_pressure_hint(self, memory_route: L640MemoryRecallRoute | None) -> float:
        if memory_route is None:
            return 0.0
        hint_count = len(memory_route.hints)
        filtered = max(0, int(memory_route.filtered_count))
        return clamp01((hint_count / 8.0) + min(0.35, filtered / 20.0))

    def _build_runtime_budget_snapshot(self) -> dict[str, Any]:
        payload = self.planner_execution.public_dict()
        if payload.get("status") == "empty":
            return {
                "planner_budget_hint": "Runtime 暂无执行报告：预算压力正常，A0-A4 保持低摩擦；A5/凭证/不可逆边界仍由执行链硬治理。",
                "step_ledger": {"max_steps": 0, "remaining_steps": 0, "planned_steps": 0, "exhausted": False},
                "failure_budget": {"max_failures": 3, "observed_failures": 0, "exhausted": False},
                "timeout_budget": {"default_timeout_seconds": 0, "remaining_timeout_seconds": 0, "blocks_execution": False},
                "chain_lease": {"renewal_recommended": False, "requested_extension": 0},
            }
        total = int(payload.get("total_steps") or 0)
        executed = int(payload.get("executed_steps") or 0)
        failed = int(payload.get("failed_steps") or 0)
        timeout_steps = int(payload.get("timeout_steps") or 0)
        status = str(payload.get("status") or "")
        exhausted = status in {"timeout_with_resume", "failed_with_resume"} and total > 0 and executed >= total
        return {
            "planner_budget_hint": "Runtime 只读预算压力投影：只生成降级/续租建议，不直接扣费、不默认阻断 A0-A4。",
            "step_ledger": {
                "max_steps": total,
                "remaining_steps": max(0, total - executed),
                "planned_steps": 0,
                "exhausted": bool(exhausted),
            },
            "failure_budget": {"max_failures": max(3, total or 3), "observed_failures": failed, "exhausted": failed > 0 and executed >= total > 0},
            "timeout_budget": {"default_timeout_seconds": max(0, total * 30), "remaining_timeout_seconds": max(0, (total - timeout_steps) * 30), "blocks_execution": False},
            "chain_lease": {"renewal_recommended": bool(timeout_steps or failed), "requested_extension": 5 if timeout_steps or failed else 0},
        }

    def _run_forgetting_reviews(self, *, limit: int = 10, now: float | None = None) -> list[ForgetReviewDecision]:
        self._last_forget_review_error = ""
        if self._memory_store is None:
            return []
        decisions: list[ForgetReviewDecision] = []
        try:
            records = self._memory_store.active_records()[: max(0, int(limit))]
            for record in records:
                vector = self._forgetting_vector_for_record(record, now=now)
                decisions.append(self._forget_review_router.review(record, vector))
        except Exception as exc:  # 不静默吞掉；进入可见 snapshot，调用方测试可检出。
            self._last_forget_review_error = f"{type(exc).__name__}: {exc}"
            raise
        return decisions

    def _forgetting_vector_for_record(self, record: MemoryRecord, *, now: float | None = None) -> ForgettingScoreVector:
        now_ts = float(now if now is not None else time())
        elapsed = max(0.0, now_ts - float(record.last_accessed_at))
        expiry_score = 1.0 - DecayKernel(
            elapsed_seconds=elapsed,
            half_life_seconds=record.half_life_seconds,
            reuse_count=record.reuse_count,
            success_rate=record.observed_success_rate,
        ).decay
        return ForgettingScoreVector(
            expiry_score=clamp01(expiry_score),
            low_reuse_score=clamp01(1.0 - min(1.0, record.reuse_count / 5.0)),
            low_confidence_score=clamp01(1.0 - record.confidence_score),
            conflict_score=clamp01(record.conflict_score),
            compression_gain=clamp01(len(record.sanitized_summary) / 700.0),
            privacy_minimization_need=clamp01(record.privacy_risk_score),
            user_forget_signal=1.0 if record.user_forget_request_ref else 0.0,
            explicit_user_forget_request=bool(record.user_forget_request_ref),
            protected_l5_rule_score=1.0 if MemoryLevel(record.memory_level) is MemoryLevel.L5 else 0.0,
        )

    def affective_runtime_snapshot(self) -> dict[str, Any]:
        route_payload = self._affective_route.public_dict() if self._affective_route is not None else None
        state_payload = self._affective_state.public_dict() if self._affective_state is not None else None
        return {
            "schema": "tiangong.l6_49_2.runtime_affective_snapshot.v1",
            "turn_count": self._affective_turn_count,
            "has_previous_state": self._affective_state is not None,
            "state": state_payload,
            "route": route_payload,
            "not_authorization": True,
            "not_refusal": True,
            "no_tool_dispatch": True,
            "no_quality_gate_override": True,
        }

    def forgetting_review_runtime_snapshot(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_49_2.runtime_forgetting_review_snapshot.v1",
            "memory_store_attached": self._memory_store is not None,
            "review_count": len(self._last_forget_review_decisions),
            "last_error": self._last_forget_review_error,
            "decisions": [decision.public_dict() for decision in self._last_forget_review_decisions],
            "no_physical_delete": True,
            "no_memory_mutation": True,
        }

    def memory_recall_runtime_snapshot(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_49_3.runtime_memory_recall_snapshot.v1",
            "memory_store_attached": self._memory_store is not None,
            "last_error": self._last_memory_recall_error,
            "route": self._last_memory_recall_route.public_dict() if self._last_memory_recall_route is not None else None,
            "summary_only": True,
            "no_raw_memory_body": True,
            "no_long_term_write": True,
            "no_memory_delete": True,
        }

    def lifecycle_runtime_snapshot(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_49_3.runtime_lifecycle_snapshot.v1",
            "bundle": self._last_lifecycle_bundle.public_dict() if self._last_lifecycle_bundle is not None else None,
            "coordinator_only": True,
            "no_direct_execution": True,
            "no_tool_invocation": True,
            "no_patch_apply": True,
            "no_hot_switch": True,
            "no_kernel_mutation": True,
        }

    def budget_low_friction_runtime_snapshot(self) -> dict[str, Any]:
        payload = self.budget_low_friction.public_dict()
        payload.update(
            {
                "runtime_projection_only": True,
                "no_budget_mutation": True,
                "no_execution_block": True,
                "a0_a4_low_friction_preserved": True,
                "a5_hard_boundary_preserved": True,
            }
        )
        return payload

    def four_path_runtime_snapshot(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_49_3.runtime_four_path_snapshot.v1",
            "report": self._last_four_path_report.public_dict() if self._last_four_path_report is not None else None,
            "unified_projection": True,
            "no_second_runtime": True,
            "no_direct_execution": True,
            "no_tool_dispatch": True,
            "no_model_dispatch": True,
            "no_memory_write": True,
            "no_kernel_mutation": True,
        }

    def planner_unified_consumption_snapshot(self) -> dict[str, Any]:
        return {
            "schema": "tiangong.l6_49_3.runtime_planner_unified_consumption_snapshot.v1",
            "report": self._last_planner_consumption_report.public_dict() if self._last_planner_consumption_report is not None else None,
            "planner_consumable": True,
            "no_second_runtime": True,
            "no_direct_execution": True,
            "no_tool_dispatch": True,
            "no_kernel_mutation": True,
        }

    def interface_wiring_snapshot(self) -> dict[str, Any]:
        """L6.49.3：Runtime/内核接口接线总快照。"""
        return {
            "schema": "tiangong.l6_49_3.interface_wiring_snapshot.v1",
            "runtime_entry": "RuntimeEntry",
            "kernel_boundary": "read_only_contracts_no_kernel_mutation",
            "affective": self.affective_runtime_snapshot(),
            "memory_recall": self.memory_recall_runtime_snapshot(),
            "forgetting_review": self.forgetting_review_runtime_snapshot(),
            "budget_low_friction": self.budget_low_friction_runtime_snapshot(),
            "lifecycle": self.lifecycle_runtime_snapshot(),
            "four_path": self.four_path_runtime_snapshot(),
            "planner_unified_consumption": self.planner_unified_consumption_snapshot(),
            "no_second_runtime": True,
            "no_direct_tool_call": True,
            "no_provider_sdk_call": True,
            "no_memory_mutation_from_projection": True,
            "no_self_iteration_merge": True,
            "no_kernel_mutation": True,
        }

    def _build_planner_context_hint(self, *, external_context_hint: str = "") -> str:
        safe_external_context_hint = redact_text(str(external_context_hint or "").strip())
        parts = [
            safe_external_context_hint,
            self.project_index.build_planner_hint(),
            self.context_memory.build_planner_hint(),
            self.experience.build_planner_hint(),
            self.skill_queue.build_planner_hint(),
            self.tool_requests.build_planner_hint(),
            self.exoskeleton.build_planner_hint(),
            self.learning_convergence.build_planner_hint(),
            self.learning_asset_candidate_sandbox.build_planner_hint(),
            self.learning_asset_release_gate.build_planner_hint(),
            self.learning_asset_activation.build_planner_hint(),
            self.recovery_coordination.build_planner_hint(),
            self.governance_execution.build_planner_hint(),
            self.budget_low_friction.build_planner_hint(),
            self.lifecycle_coordinator.build_planner_hint(),
            self.four_path_context.build_planner_hint(),
            self.planner_unified_consumption.build_planner_hint(),
            self.planner_context.build_planner_hint(),
            self.planner_execution.build_planner_hint(),
            self.p0_system_integration.build_planner_hint(),
            self.p0_system_integration_two.build_planner_hint(),
            self.shell_mount.build_planner_hint(),
            self.project_repair.build_planner_hint(),
            self.delivery_standardization.build_planner_hint(),
            self.provider_adaptation.build_planner_hint(),
        ]
        return "\n\n".join(part for part in parts if part)[:5200]

    def p0_system_integration_snapshot(self) -> dict[str, Any]:
        """L6.38：Provider / Budget / Skill / Handoff 四系统接入总报告。"""
        return self.p0_system_integration.public_dict()

    def export_p0_system_integration_json(self, path: str | Path) -> Path:
        return self.p0_system_integration.export_json(path)

    def reset_p0_system_integration(self) -> None:
        self.p0_system_integration.reset()

    def run_l6_38_p0_system_integration(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 10,
        max_items: int = 8,
        refresh_sources: bool = True,
    ) -> RuntimeRunResult:
        # L6.38：P0 四系统接入。所有系统均以普通工具计划进入 L6.37 冻结执行链。
        # Provider/Budget/Skill/Handoff 只能输出 Hint / Ticket / Envelope / Evidence / Report；
        # 不触网、不读密钥、不改预算、不注册/激活 Skill、不自动派生子任务、不改 tiangong_kernel。
        plan: list[ToolInvocation] = []
        if refresh_sources or self.provider_adaptation.last_report is None:
            plan.append(ToolInvocation("build_provider_adaptation", {"path": ".", "notes": notes or "L6.38 Provider 前置声明刷新。"}))
        if refresh_sources or self.skill_queue.last_report is None:
            plan.append(ToolInvocation("synthesize_experience_candidates", {"notes": notes or "L6.38 Skill 前置候选刷新。", "max_candidates": max_items}))
            plan.append(ToolInvocation("queue_skill_candidates", {"notes": notes or "L6.38 Skill 前置审阅队列刷新。", "max_items": max_items}))
        plan.extend(
            [
                ToolInvocation("build_l6_38_provider_integration", {"notes": notes, "requested_call_mode": "dry_run"}),
                ToolInvocation("build_l6_38_budget_snapshot", {"notes": notes, "max_steps": max_steps, "planned_steps": 4}),
                ToolInvocation("build_l6_38_skill_integration", {"notes": notes, "max_items": max_items}),
                ToolInvocation("build_l6_38_handoff_integration", {"notes": notes, "max_subtasks": 3}),
                ToolInvocation("build_l6_38_p0_integration", {"notes": notes}),
            ]
        )
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="l6_38_p0_system_integration",
            tool_mode=tool_mode,
            max_steps=min(max_steps, max(1, len(plan))),
        )


    def p0_system_integration_two_snapshot(self) -> dict[str, Any]:
        """L6.39：Memory / Audit / Recovery / QualityGate 四系统接入二总报告。"""
        return self.p0_system_integration_two.public_dict()

    def export_p0_system_integration_two_json(self, path: str | Path) -> Path:
        return self.p0_system_integration_two.export_json(path)

    def reset_p0_system_integration_two(self) -> None:
        self.p0_system_integration_two.reset()

    def run_l6_39_p0_system_integration_two(
        self,
        *,
        workspace: str | Path | None = None,
        notes: str = "",
        tool_mode: str | ToolExecutionMode = ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps: int = 10,
        max_items: int = 8,
        refresh_sources: bool = True,
    ) -> RuntimeRunResult:
        # L6.39：P0 四系统接入二。所有系统均以普通工具计划进入 L6.37 冻结执行链。
        # Memory/Audit/Recovery/QualityGate 只能输出安全摘要、证据、续接票据和质量引用；
        # 不写长期记忆、不篡改审计、不执行补丁、不派生子智能体、不改预算、不覆盖质量门。
        plan: list[ToolInvocation] = []
        if refresh_sources or self.recovery_coordination.last_report is None:
            plan.append(ToolInvocation("build_recovery_coordination", {"notes": notes or "L6.39 Recovery 前置续接报告刷新。", "max_items": max_items, "step_budget": max_steps}))
        plan.extend(
            [
                ToolInvocation("build_l6_39_memory_integration", {"notes": notes, "max_items": max_items}),
                ToolInvocation("build_l6_39_audit_integration", {"notes": notes, "max_events": 24}),
                ToolInvocation("build_l6_39_recovery_integration", {"notes": notes, "max_items": max_items}),
                ToolInvocation("build_l6_39_quality_gate_integration", {"notes": notes}),
                ToolInvocation("build_l6_39_p0_integration", {"notes": notes}),
            ]
        )
        return self.execute_plan(
            plan,
            workspace=workspace,
            user_message="l6_39_p0_system_integration_two",
            tool_mode=tool_mode,
            max_steps=min(max_steps, max(1, len(plan))),
        )


    def run_model_plan_compat_replay(self) -> dict[str, Any]:
        """L6.34：离线回放 DeepSeek plan 输出语料，不触网不读凭证。"""
        return replay_deepseek_plan_samples().public_dict()

    def run_recovery_replay_quality_corpus(self, workspace: str | Path, *, export_dir: str | Path | None = None) -> dict[str, Any]:
        """L6.36：运行失败恢复 / 可回放 / 执行质量门离线语料。"""
        return run_l6_36_replay_corpus(workspace, export_dir=export_dir).public_dict()

    def _remember(self, result: RuntimeRunResult) -> RuntimeRunResult:
        self.last_result = result
        self.context_memory.observe_run(result)
        return result


def build_default_registry() -> RuntimeToolRegistry:
    registry = RuntimeToolRegistry()
    registry.register(ToolDescriptor("model_chat", "通过 Runtime 审计链执行模型聊天调用。", "A2"), model_chat_adapter)
    registry.register(ToolDescriptor("list_dir", "列出工作区内目录。", "A1"), list_dir_adapter)
    registry.register(ToolDescriptor("read_file", "读取工作区内普通文本文件。", "A1"), read_file_adapter)
    registry.register(ToolDescriptor("write_workspace_file", "写入工作区文件，覆盖前自动备份。", "A3/A4"), write_workspace_file_adapter)
    registry.register(ToolDescriptor("return_code", "审计型虚拟代码返回；不执行、不写文件。", "A2"), return_code_adapter)
    registry.register(ToolDescriptor("return_analysis", "审计型虚拟分析返回；不执行、不写文件。", "A2"), return_analysis_adapter)
    registry.register(ToolDescriptor("run_python_quality_check", "执行 allowlist 内 Python 质量检查。", "A3"), run_python_quality_check_adapter)
    registry.register(ToolDescriptor("create_zip_package", "在工作区内生成交付 ZIP 与 SHA256。", "A3"), create_zip_package_adapter)
    # L6.70.2-CodeX：代码执行外骨骼工具为 v2 原生实现；只在 build_default_registry 显式注册，
    # 不含启动副作用、不导入 v1、不替换 ToolRegistry。
    register_code_x_runtime_tools(registry)
    # L6.70.2-R14：v1 非 Code-X 语义按独立纯净导入层注册；不复制/不 import v1，不混入 Code-X。
    register_v1_clean_import_tools(registry)
    # create_release_bundle / synthesize_experience_candidates / queue_skill_candidates / queue_tool_production_requests / build_execution_exoskeleton / build_shell_system_mount / build_project_repair_plan / build_delivery_standardization / build_provider_adaptation / build_learning_convergence / build_recovery_coordination / build_governance_execution / build_planner_context / L6.38/L6.39 P0 integration tools 需要 RuntimeEntry 内部状态桥，故在 RuntimeEntry.__init__ 中注册。
    return registry
