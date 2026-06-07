"""风险分级。"""

from __future__ import annotations

from pathlib import Path

from .execution_policy import RiskLevel
from .tool_invocation import ToolInvocation

A1_TOOLS = {"scan_project", "diagnose_project", "list_dir", "read_file"}
A2_TOOLS = {"model_chat", "return_code", "return_analysis", "evaluate_quality_gate", "synthesize_experience_candidates", "queue_skill_candidates", "queue_tool_production_requests", "build_execution_exoskeleton", "build_shell_system_mount", "build_project_repair_plan", "build_delivery_standardization", "build_provider_adaptation", "build_learning_convergence", "build_recovery_coordination", "build_governance_execution", "build_planner_context", "build_l6_38_provider_integration", "build_l6_38_budget_snapshot", "build_l6_38_skill_integration", "build_l6_38_handoff_integration", "build_l6_38_p0_integration", "build_l6_39_memory_integration", "build_l6_39_audit_integration", "build_l6_39_recovery_integration", "build_l6_39_quality_gate_integration", "build_l6_39_p0_integration"}
WILDCARD_ALLOWED_PREFIXES = ("diagnose_", "scan_", "read_", "list_", "synthesize_")
A3_TOOLS = {"write_workspace_file", "run_python_quality_check", "create_zip_package", "create_release_bundle"}
A5_COMMAND_TERMS = {
    "rm",
    "del",
    "format",
    "sudo",
    "chmod 777",
    "curl | sh",
    "powershell -enc",
    "reg delete",
    "mkfs",
}
A5_COMMAND_EXACT_TOKENS = {"rm", "del", "format", "sudo", "mkfs"}
A5_COMMAND_PHRASES = {"chmod 777", "curl | sh", "powershell -enc", "reg delete"}
SENSITIVE_TERMS = {".env", "id_rsa", "token", "secret", "password", "credential"}


class RiskClassifier:
    def classify(self, invocation: ToolInvocation) -> tuple[RiskLevel, str]:
        if invocation.risk_level is not None:
            return invocation.risk_level, invocation.reason or "调用已显式声明风险等级。"

        tool_name = invocation.tool_name
        args_text = " ".join(str(v).lower() for v in invocation.arguments.values())

        if tool_name not in A1_TOOLS | A2_TOOLS | A3_TOOLS and not tool_name.startswith(WILDCARD_ALLOWED_PREFIXES):
            return RiskLevel.A5, "未知工具不允许执行。"

        if tool_name.startswith(("read_", "list_", "scan_", "diagnose_")) and tool_name not in A1_TOOLS | A2_TOOLS | A3_TOOLS:
            if any(term in args_text for term in SENSITIVE_TERMS):
                return RiskLevel.A5, "读取目标疑似敏感路径或凭证。"
            return RiskLevel.A1, "安全前缀只读/诊断类工具；真实执行仍需 RuntimeToolRegistry 注册。"

        if tool_name.startswith("synthesize_") and tool_name not in A1_TOOLS | A2_TOOLS | A3_TOOLS:
            return RiskLevel.A2, "安全前缀合成类工具；真实执行仍需 RuntimeToolRegistry 注册。"

        if tool_name in A2_TOOLS:
            if tool_name in {"return_code", "return_analysis"}:
                return RiskLevel.A2, "审计型虚拟返回，不执行代码、不写文件。"
            if tool_name == "model_chat":
                return RiskLevel.A2, "受治理模型调用，不开放工具执行。"
            if tool_name == "synthesize_experience_candidates":
                return RiskLevel.A2, "受治理 L6.20 经验候选生成，不注册 Skill、不生产 Tool。"
            if tool_name == "queue_skill_candidates":
                return RiskLevel.A2, "受治理 L6.21 Skill 草案版本入队，不注册、不激活、不写 Skill 注册表。"
            if tool_name == "queue_tool_production_requests":
                return RiskLevel.A2, "受治理 L6.22 Tool 生产请求入队，只做沙箱验证前置，不生产、不注册、不释放工具句柄。"
            if tool_name == "build_execution_exoskeleton":
                return RiskLevel.A2, "受治理 L6.23 LLM 外骨骼压缩，只生成 PlannerHint 和最小 ToolCandidateTicket，不注册、不生产、不激活。"
            if tool_name == "build_shell_system_mount":
                return RiskLevel.A2, "受治理 L6.24 十八系统壳装，只读映射已装系统，不注册、不激活、不改内核。"
            if tool_name == "build_project_repair_plan":
                return RiskLevel.A2, "受治理 L6.25 项目雷达与工程修复计划，只生成 PatchPlan/RegressionHint/RollbackEvidence，不应用补丁、不改内核。"
            if tool_name == "build_delivery_standardization":
                return RiskLevel.A2, "受治理 L6.26 交付链标准化，只生成 ChangeSet/TestEvidence/Manifest/Integrity/Todo 证据，不打包、不写文件、不改内核。"
            if tool_name == "build_provider_adaptation":
                return RiskLevel.A2, "受治理 L6.27 Provider 适配外壳，只生成声明式 ProviderProfile/CapabilityMatrix/API Surface/GovernanceMount，不触网、不读密钥、不注册正式适配器。"
            if tool_name == "build_learning_convergence":
                return RiskLevel.A2, "受治理 L6.28 经验/Skill/Tool 执行合流，只生成 PlannerHintRoute/SkillDraftRoute/ToolCandidateRoute/ConsumptionCard，不写记忆、不注册 Skill、不生产 Tool。"
            if tool_name == "build_recovery_coordination":
                return RiskLevel.A2, "受治理 L6.29 自修复/多智能体/预算联动，只生成 FailureSignal/RepairCandidate/HandoffDigest/BudgetUpdate/ResumePlan，不派生子智能体、不执行补丁、不改预算、不改内核。"
            if tool_name == "build_governance_execution":
                return RiskLevel.A2, "受治理 L6.30 治理执行力化，只生成 A0-A4 快车道、A5 硬边界、发布/注册/激活护栏和 PlannerGovernanceHint，不改 PermitGateway/ExecutionPolicy、不执行副作用、不改内核。"
            if tool_name == "build_planner_context":
                return RiskLevel.A2, "受治理 L6.31 统一 Planner 接入，只生成 UnifiedPlannerContext / ExecutionStepDraft / PlannerResumeEnvelope，不执行工具、不注册 Tool/Skill/Provider、不读取密钥、不改内核。"
            if tool_name == "build_l6_38_provider_integration":
                return RiskLevel.A2, "受治理 L6.38 Provider 接入，只生成 ProviderProfile/ProviderExecutionTicket/CredentialRef；无许可时 sample replay，不触网、不读密钥、不裸调 SDK。"
            if tool_name == "build_l6_38_budget_snapshot":
                return RiskLevel.A2, "受治理 L6.38 Budget 接入，只生成 StepBudgetLedger/ChainBudgetLease/TimeoutBudget/FailureBudget/BudgetSnapshot，不直接改预算，不默认阻断 A0-A4。"
            if tool_name == "build_l6_38_skill_integration":
                return RiskLevel.A2, "受治理 L6.38 Skill 接入，只生成 SkillCandidateRoute/SkillReviewTicket/SkillActivationIntent/SkillExecutionHint，不注册、不激活、不释放工具。"
            if tool_name == "build_l6_38_handoff_integration":
                return RiskLevel.A2, "受治理 L6.38 Handoff 接入，只生成 SubtaskTicket/HandoffEnvelope/ParentChainCollectReport，不自动递归派生，必须回流父链。"
            if tool_name == "build_l6_38_p0_integration":
                return RiskLevel.A2, "受治理 L6.38 P0 总报告，只汇总 Provider/Budget/Skill/Handoff 的 Hint/Ticket/Envelope/Evidence/Report，不新增 Runtime 不改内核。"
            if tool_name == "build_l6_39_memory_integration":
                return RiskLevel.A2, "受治理 L6.39 Memory 接入，只生成 MemoryRecallRoute 安全摘要路由，不写长期记忆、不注入原始正文。"
            if tool_name == "build_l6_39_audit_integration":
                return RiskLevel.A2, "受治理 L6.39 Audit 接入，只生成 AuditEvidenceEnvelope 安全摘要证据，不删除、不重写、不伪造审计。"
            if tool_name == "build_l6_39_recovery_integration":
                return RiskLevel.A2, "受治理 L6.39 Recovery 接入，只生成 RecoveryResumeTicket，不执行补丁、不派生子智能体、不改预算。"
            if tool_name == "build_l6_39_quality_gate_integration":
                return RiskLevel.A2, "受治理 L6.39 QualityGate 接入，只生成 QualityGateEvidence，不覆盖裁决、不自动放行发布。"
            if tool_name == "build_l6_39_p0_integration":
                return RiskLevel.A2, "受治理 L6.39 P0 接入二总报告，只汇总 Memory/Audit/Recovery/QualityGate 的安全摘要/证据/票据/质量引用，不新增 Runtime 不改内核。"
            return RiskLevel.A2, "受治理质量门裁决，不执行外部副作用。"

        if _contains_dangerous_command(args_text):
            return RiskLevel.A5, "命中危险命令或提权/删除模式。"

        if tool_name == "run_python_quality_check":
            command = str(invocation.arguments.get("command") or invocation.arguments.get("command_type") or "").lower()
            if command not in {"compileall", "pytest", "python -m compileall", "python -m pytest"}:
                return RiskLevel.A5, "命令不在质量检查 allowlist 中。"
            return RiskLevel.A3, "受控 Python 质量检查。"

        if tool_name in A1_TOOLS:
            if any(term in args_text for term in SENSITIVE_TERMS):
                return RiskLevel.A5, "读取目标疑似敏感路径或凭证。"
            return RiskLevel.A1, "只读工作区操作。"

        if tool_name == "write_workspace_file":
            target = Path(str(invocation.arguments.get("path") or ""))
            if target.is_absolute():
                return RiskLevel.A4, "绝对路径写入需要确认。"
            return RiskLevel.A3, "受控工作区写入。"

        if tool_name == "create_zip_package":
            return RiskLevel.A3, "受控交付打包。"

        if tool_name == "create_release_bundle":
            return RiskLevel.A3, "受控 L6.19 标准发布包构建。"

        return RiskLevel.A5, "默认安全阻断。"


def _contains_dangerous_command(args_text: str) -> bool:
    """避免把 confirmed.txt、normal.txt 这类路径误判为 rm 命令。"""
    tokens = {token.strip("\\/.:;()[]{}\"'`).,=") for token in args_text.split()}
    if tokens.intersection(A5_COMMAND_EXACT_TOKENS):
        return True
    return any(phrase in args_text for phrase in A5_COMMAND_PHRASES)
