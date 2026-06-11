"""风险分级。"""

from __future__ import annotations

from pathlib import Path

from .execution_policy import RiskLevel
from .tool_invocation import ToolInvocation
from .code_x_runtime_adapters import CODE_X_TOOL_RISK
from .v1_clean_import_adapters import V1_CLEAN_TOOL_RISK

A1_TOOLS = {"scan_project", "diagnose_project", "list_dir", "read_file", "file_sha256", "document_parse", "document_query"}
A2_TOOLS = {"model_chat", "return_code", "return_analysis", "document_rewrite_plan", "evaluate_quality_gate", "synthesize_experience_candidates", "queue_skill_candidates", "queue_tool_production_requests", "build_execution_exoskeleton", "build_shell_system_mount", "build_project_repair_plan", "build_delivery_standardization", "build_provider_adaptation", "build_learning_convergence", "build_recovery_coordination", "build_governance_execution", "build_planner_context", "build_l6_38_provider_integration", "build_l6_38_budget_snapshot", "build_l6_38_skill_integration", "build_l6_38_handoff_integration", "build_l6_38_p0_integration", "build_l6_39_memory_integration", "build_l6_39_audit_integration", "build_l6_39_recovery_integration", "build_l6_39_quality_gate_integration", "build_l6_39_p0_integration", "runtime_tool_alignment_check", "runtime_llm_operational_drill", "learning_asset_contract_guide", "learning_asset_contract_normalize", "learning_asset_contract_validate", "learning_asset_sandbox_guide", "learning_asset_sandbox_align", "learning_asset_sandbox_validate", "learning_asset_candidate_sandbox_guide", "learning_asset_candidate_sandbox_validate", "learning_asset_candidate_sandbox_review", "learning_asset_release_gate_guide", "learning_asset_release_gate_check", "learning_asset_activation_guide", "learning_asset_activation_status", "learning_asset_adapter_guide", "learning_asset_adapter_template_list", "learning_asset_adapter_template_normalize", "learning_asset_adapter_template_validate", "learning_asset_adapter_template_smoke"}
WILDCARD_ALLOWED_PREFIXES = ("diagnose_", "scan_", "read_", "list_", "synthesize_")
A3_TOOLS = {"write_workspace_file", "run_python_quality_check", "create_zip_package", "document_export", "document_apply_rewrite", "document_rollback", "create_release_bundle", "learning_asset_candidate_sandbox_build", "learning_asset_activation_apply", "learning_asset_activation_smoke", "learning_asset_adapter_drill"}
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

        if tool_name in CODE_X_TOOL_RISK:
            if _contains_dangerous_command(args_text):
                return RiskLevel.A5, "Code-X 调用参数命中危险命令或破坏性模式。"
            declared = CODE_X_TOOL_RISK[tool_name]
            return RiskLevel(declared), f"Code-X 原生工具，风险等级 {declared}，受 Runtime 审计链约束。"

        if tool_name in V1_CLEAN_TOOL_RISK:
            if _contains_dangerous_command(args_text):
                return RiskLevel.A5, "v1 纯净导入工具参数命中危险命令或破坏性模式。"
            declared = V1_CLEAN_TOOL_RISK[tool_name]
            if declared in {"A1", "A2"} and any(term in args_text for term in SENSITIVE_TERMS):
                return RiskLevel.A5, "v1 纯净导入工具读取目标疑似敏感路径或凭证。"
            return RiskLevel(declared), f"v1 非 Code-X 语义纯净重建工具，风险等级 {declared}，受 Runtime 审计链约束。"

        if tool_name.startswith(("learned_tool_", "learned_skill_")):
            if _contains_dangerous_command(args_text):
                return RiskLevel.A5, "R20 active learned asset 参数命中危险命令或破坏性模式。"
            if any(term in args_text for term in SENSITIVE_TERMS):
                return RiskLevel.A5, "R20 active learned asset 参数疑似包含敏感路径或凭证。"
            return RiskLevel.A3, "R20 已激活学习资产 learned_*，只允许经 Runtime 注册表和审计链调用。"

        if tool_name not in A1_TOOLS | A2_TOOLS | A3_TOOLS and not tool_name.startswith(WILDCARD_ALLOWED_PREFIXES):
            return RiskLevel.A4, "未知工具不再按 A5 阻断；交由 RuntimeToolRegistry 决定是否已注册。"

        if tool_name.startswith(("read_", "list_", "scan_", "diagnose_")) and tool_name not in A1_TOOLS | A2_TOOLS | A3_TOOLS:
            if any(term in args_text for term in SENSITIVE_TERMS):
                return RiskLevel.A5, "读取目标疑似敏感路径或凭证。"
            return RiskLevel.A1, "安全前缀只读/诊断类工具；真实执行仍需 RuntimeToolRegistry 注册。"

        if tool_name.startswith("synthesize_") and tool_name not in A1_TOOLS | A2_TOOLS | A3_TOOLS:
            return RiskLevel.A2, "安全前缀合成类工具；真实执行仍需 RuntimeToolRegistry 注册。"

        if tool_name in A2_TOOLS:
            if tool_name == "document_rewrite_plan":
                return RiskLevel.A2, "文档修改计划只生成证据和步骤，不直接写入、不覆盖原文。"
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
            if tool_name == "runtime_tool_alignment_check":
                return RiskLevel.A2, "受治理全局工具注册表/Skill 对齐检查，只读元数据，不执行目标工具，不改注册表。"
            if tool_name == "runtime_llm_operational_drill":
                return RiskLevel.A2, "受治理 LLM 路由实操演练，只模拟意图到工具名链，不执行目标工具副作用。"
            if tool_name == "learning_asset_contract_guide":
                return RiskLevel.A2, "受治理 R16 未来资产契约指南，只返回 Tool/Skill 统一格式元数据。"
            if tool_name == "learning_asset_contract_normalize":
                return RiskLevel.A2, "受治理 R16 未来资产契约归一化，只把候选 Skill/Tool 元数据转为统一格式，不注册不生产。"
            if tool_name == "learning_asset_contract_validate":
                return RiskLevel.A2, "受治理 R16 未来资产契约校验，只检查字段/usage card/chain recipe/no-pollution，不激活不写入。"
            if tool_name == "learning_asset_sandbox_guide":
                return RiskLevel.A2, "受治理 R17 沙箱对齐指南，只说明已存在 L6.22 Tool 生产请求沙箱前置链，不执行副作用。"
            if tool_name == "learning_asset_sandbox_align":
                return RiskLevel.A2, "受治理 R17 沙箱对齐，只把 R16 Tool 契约映射到 L6.22 SandboxValidationPlan，不生产不注册。"
            if tool_name == "learning_asset_sandbox_validate":
                return RiskLevel.A2, "受治理 R17 沙箱对齐校验，只复核映射证据，不释放工具句柄。"
            if tool_name == "learning_asset_candidate_sandbox_guide":
                return RiskLevel.A2, "受治理 R18 候选包沙箱指南，只返回链路和边界元数据。"
            if tool_name == "learning_asset_candidate_sandbox_validate":
                return RiskLevel.A2, "受治理 R18 候选包校验，只复核隔离候选包静态/smoke/回滚证据，不注册不激活。"
            if tool_name == "learning_asset_candidate_sandbox_review":
                return RiskLevel.A2, "受治理 R18 候选包注册审阅，只给 LLM 决策证据，不写注册表不释放句柄。"
            if tool_name == "learning_asset_release_gate_guide":
                return RiskLevel.A2, "受治理 R19 轻量发布门指南，只返回四项直检链路和边界说明。"
            if tool_name == "learning_asset_release_gate_check":
                return RiskLevel.A2, "受治理 R19 轻量发布门，只生成质量门/发布门/回滚证据/注册申请，不注册不激活。"
            if tool_name == "learning_asset_activation_guide":
                return RiskLevel.A2, "受治理 R20 学习资产激活指南，只返回注册/激活/回滚规则。"
            if tool_name == "learning_asset_activation_status":
                return RiskLevel.A2, "受治理 R20 active asset 状态读取，只加载 workspace 级 learned_* 注册信息。"
            if tool_name == "learning_asset_adapter_guide":
                return RiskLevel.A2, "受治理 R21 Adapter 模板指南，只返回模板链路和边界元数据。"
            if tool_name == "learning_asset_adapter_template_list":
                return RiskLevel.A2, "受治理 R21 Adapter 模板列表，只返回 LLM 可读 usage card。"
            if tool_name == "learning_asset_adapter_template_normalize":
                return RiskLevel.A2, "受治理 R21 Adapter 模板归一化，只生成模板 spec，不注册不激活。"
            if tool_name == "learning_asset_adapter_template_validate":
                return RiskLevel.A2, "受治理 R21 Adapter 模板校验，只做 AST/usage/边界检查。"
            if tool_name == "learning_asset_adapter_template_smoke":
                return RiskLevel.A2, "受治理 R21 Adapter 模板 smoke，只处理参数内样本，不触网不写 workspace。"
            return RiskLevel.A2, "受治理质量门裁决，不执行外部副作用。"

        if _contains_dangerous_command(args_text):
            return RiskLevel.A5, "命中危险命令或提权/删除模式。"

        if tool_name == "run_python_quality_check":
            command = str(invocation.arguments.get("command") or invocation.arguments.get("command_type") or "").lower()
            if command not in {"compileall", "pytest", "python -m compileall", "python -m pytest"}:
                return RiskLevel.A4, "非 allowlist 质量命令不再按 A5 阻断；建议改用 safe_command_runner 执行。"
            return RiskLevel.A3, "受控 Python 质量检查。"

        if tool_name in A1_TOOLS:
            if any(term in args_text for term in SENSITIVE_TERMS):
                return RiskLevel.A5, "读取目标疑似敏感路径或凭证。"
            if tool_name == "document_query":
                return RiskLevel.A1, "文档追问只读取已解析安全上下文与引用片段。"
            return RiskLevel.A1, "只读工作区操作。"

        if tool_name == "write_workspace_file":
            target = Path(str(invocation.arguments.get("path") or ""))
            if target.is_absolute():
                return RiskLevel.A3, "绝对路径写入按执行力优先放行；路径归一化、审计和回滚仍由 Runtime 处理。"
            return RiskLevel.A3, "受控工作区写入。"

        if tool_name == "document_export":
            return RiskLevel.A3, "文档导出只写入受控 artifact，内容为安全解析摘要和引用片段。"

        if tool_name == "create_zip_package":
            return RiskLevel.A3, "受控交付打包。"

        if tool_name == "create_release_bundle":
            return RiskLevel.A3, "受控 L6.19 标准发布包构建。"

        if tool_name == "learning_asset_candidate_sandbox_build":
            return RiskLevel.A3, "受治理 R18 候选包生产沙箱，只能写入隔离 candidate_sandbox 目录，不注册不激活。"

        if tool_name == "learning_asset_activation_apply":
            return RiskLevel.A3, "受治理 R20 学习资产激活：只写 workspace active_assets/r20，并注册 learned_*，不得覆盖内置工具或导入 v1。"

        if tool_name == "learning_asset_activation_smoke":
            return RiskLevel.A3, "受治理 R20 active learned asset smoke 调用，只验证 learned_* 是否可用。"

        if tool_name == "learning_asset_adapter_drill":
            return RiskLevel.A3, "受治理 R21 Adapter drill：生成隔离候选包并经 R20 激活 learned_tool_*，不覆盖内置工具。"

        if tool_name == "document_apply_rewrite":
            return RiskLevel.A3, "文档真实写回工具：默认修订副本，覆盖前备份，生成回滚清单并受 Runtime/QualityGate/Audit 约束。"

        if tool_name == "document_rollback":
            return RiskLevel.A3, "文档回滚工具：只基于写回 manifest/backup 执行恢复或删除新副本，受 Runtime/QualityGate/Audit 约束。"

        return RiskLevel.A4, "默认非 A5 行为按执行力优先交由 Runtime 注册表和 adapter 处理。"


def _contains_dangerous_command(args_text: str) -> bool:
    """避免把 confirmed.txt、normal.txt 这类路径误判为 rm 命令。"""
    tokens = {token.strip("\\/.:;()[]{}\"'`).,=") for token in args_text.split()}
    if tokens.intersection(A5_COMMAND_EXACT_TOKENS):
        return True
    return any(phrase in args_text for phrase in A5_COMMAND_PHRASES)
