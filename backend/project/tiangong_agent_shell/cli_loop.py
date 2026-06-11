"""CLI 对话循环。"""

from __future__ import annotations

import json
import os
import shlex
import sys
from pathlib import Path
from typing import TextIO

from tiangong_agent_runtime.planner_mode import PlannerMode
from tiangong_agent_runtime.runtime_report import export_runtime_report
from tiangong_agent_runtime.tool_invocation import ToolInvocation

from .composition_root import AgentShellContext
from .errors import AgentShellError
from .tool_bridge import ToolExecutionMode
from .prompt_compiler import compile_existing_messages_envelope, provider_is_ready
from tiangong_agent_runtime.activation_protocol import ActivationForm
from .organ_signal_emitters import refresh_session_system_prompt
from .prompt_trace import record_prompt_trace_outcome, recent_prompt_trace_summary
from .homeostasis_prompt_tuner import prompt_tuning_public_summary, reset_prompt_tuning_state

HELP_TEXT = """可用命令：
  /help              显示帮助
  /status            显示当前启动状态与模型配置摘要（密钥脱敏）
  /config            显示配置摘要（密钥脱敏）
  /tools             显示 L6.32 受治理工具/模型注册表
  /policy            显示执行分级策略
  /workspace         显示当前工作区
  /audit             显示最近审计摘要
  /prompt-trace      显示最近 PromptTrace 内部摘要
  /prompt-tuner      显示 L6.72.15 稳态提示词调权状态
  /prompt-tuner-reset 重置 L6.72.15 稳态提示词调权状态
  /audit-save <path> 导出审计 JSONL
  /audit-replay <path> 回放审计 JSONL 摘要，不执行真实工具
  /tickets           显示待确认票据
  /confirm <id>      确认 A4 票据并回到治理链执行
  /deny <id>         拒绝 A4 票据
  /report <path>     导出最近一次运行报告（json/md）
  /plan <任务>       预览 L6.17 结构化计划，不执行工具
  /scan [path]       只读扫描项目结构，生成 L6.17 项目雷达索引
  /diagnose [path]   运行 L6.17 工程诊断（扫描+质量检查+诊断）
  /quality-gate [p]  运行 L6.18 测试验证质量门（扫描+检查+诊断+裁决）
  /quality-report    显示最近质量门裁决
  /quality-save <p>  导出质量门 JSON
  /quality-reset     清空质量门裁决
  /delivery          显示最近 L6.19 标准交付 Manifest
  /delivery-save <p> 导出交付 Manifest JSON
  /delivery-reset    清空交付 Manifest
  /reflect [备注]     运行 L6.20 经验沉淀，生成 Skill/Tool 候选但不注册不生产
  /experience         显示最近 L6.20 经验沉淀候选报告
  /experience-save <p>导出经验沉淀 JSON
  /experience-reset   清空经验沉淀候选报告
  /skill-queue-build [备注] 运行 L6.21 Skill 候选版本化并进入审阅队列
  /skill-queue        显示最近 L6.21 Skill 草案版本与审阅队列
  /skill-queue-save <p>导出 Skill 审阅队列 JSON
  /skill-queue-reset  清空 Skill 审阅队列
  /tool-request-build [备注] 运行 L6.22 Tool 生产请求与沙箱验证前置队列
  /tool-request       显示最近 L6.22 Tool 生产请求队列
  /tool-request-save <p>导出 Tool 生产请求 JSON
  /tool-request-reset 清空 Tool 生产请求队列
  /exoskeleton-build [备注] 运行 L6.23 LLM 外骨骼执行力压缩
  /exoskeleton       显示最近 L6.23 PlannerHint 与最小 Tool 票据
  /exoskeleton-save <p>导出 LLM 外骨骼 JSON
  /exoskeleton-reset 清空 LLM 外骨骼压缩报告
  /shell-mount-build [备注] 运行 L6.24 十八系统 Runtime 外壳挂载
  /shell-mount       显示最近 L6.24 十八系统壳装报告
  /shell-mount-save <p>导出十八系统壳装 JSON
  /shell-mount-reset 清空十八系统壳装报告
  /repair-plan-build [p] 运行 L6.25 项目雷达 + 工程修复外壳计划
  /repair-plan       显示最近 L6.25 PatchPlan/RegressionHint/RollbackEvidence
  /repair-plan-save <p>导出 L6.25 工程修复计划 JSON
  /repair-plan-reset 清空 L6.25 工程修复计划
  /delivery-standard-build [p] 运行 L6.26 交付链标准化（ChangeSet/TestEvidence/Manifest/Integrity/Todo）
  /delivery-standard       显示最近 L6.26 标准化交付证据
  /delivery-standard-save <p>导出 L6.26 标准化交付证据 JSON
  /delivery-standard-reset 清空 L6.26 标准化交付证据
  /provider-build [p] 运行 L6.27 Provider 适配外壳（Profile/Capability/API Surface/Governance）
  /provider       显示最近 L6.27 Provider 适配外壳报告
  /provider-save <p>导出 L6.27 Provider 适配外壳 JSON
  /provider-reset 清空 L6.27 Provider 适配外壳报告
  /learning-converge-build [备注] 运行 L6.28 经验/Skill/Tool 执行合流
  /learning-converge       显示最近 L6.28 执行合流报告
  /learning-converge-save <p>导出 L6.28 执行合流 JSON
  /learning-converge-reset 清空 L6.28 执行合流报告
  /recovery-build [备注] 运行 L6.29 自修复/多智能体/预算联动恢复协调
  /recovery       显示最近 L6.29 恢复协调报告
  /recovery-save <p>导出 L6.29 恢复协调 JSON
  /recovery-reset 清空 L6.29 恢复协调报告
  /governance-build [备注] 运行 L6.30 治理执行力化外壳
  /governance       显示最近 L6.30 治理执行力化报告
  /governance-save <p>导出 L6.30 治理执行力化 JSON
  /governance-reset 清空 L6.30 治理执行力化报告
  /planner-context-build [备注] 运行 L6.31 统一 Planner 接入 / 执行主链收口
  /planner-context       显示最近 L6.31 UnifiedPlannerContext
  /planner-context-save <p>导出 L6.31 Planner 上下文 JSON
  /planner-context-reset 清空 L6.31 Planner 上下文
  /planner-execute <任务> 运行 L6.32 Planner 驱动真实执行主链
  /planner-execution       显示最近 L6.32 执行主链报告
  /planner-execution-save <p>导出 L6.32 执行主链 JSON
  /planner-execution-reset 清空 L6.32 执行主链报告
  /execution-chain-contract       显示 L6.37 执行链冻结契约
  /execution-chain-contract-save <p>导出 L6.37 执行链冻结契约 JSON
  /execution-chain-freeze         显示 L6.37 执行链冻结验收报告
  /execution-chain-freeze-save <p>导出 L6.37 执行链冻结验收 JSON
  /p0-system-build [备注] 运行 L6.38 Provider/Budget/Skill/Handoff P0 系统接入
  /p0-system       显示最近 L6.38 P0 系统接入报告
  /p0-system-save <p>导出 L6.38 P0 系统接入 JSON
  /p0-system-reset 清空 L6.38 P0 系统接入报告
  /p0-system2-build [备注] 运行 L6.39 Memory/Audit/Recovery/QualityGate P0 系统接入二
  /p0-system2       显示最近 L6.39 P0 系统接入二报告
  /p0-system2-save <p>导出 L6.39 P0 系统接入二 JSON
  /p0-system2-reset 清空 L6.39 P0 系统接入二报告
  /release [zip] [p] 运行 L6.19 标准发布流程（质量门+Release Gate+Manifest+ZIP）
  /repair-loop [p]   运行 L6.17 工程诊断/复测/报告/打包闭环
  /diagnosis         显示最近工程诊断摘要
  /diagnosis-save <p>导出工程诊断 JSON
  /diagnosis-reset   清空工程诊断摘要
  /project           显示最近项目索引摘要
  /project-save <p>  导出项目索引 JSON
  /project-reset     清空项目索引，不删除文件
  /context           显示当前进程内上下文/记忆摘要
  /context-save <p>  导出上下文摘要 JSON（不含密钥/完整文件内容）
  /context-reset     清空上下文摘要，不删除会话消息
  /run <任务>        通过 L6.17 受治理运行链执行显式/模型计划任务
  /reset             清空当前会话上下文
  /exit              退出
  /quit              退出
""".strip()


def write_line(text: str, *, stream: TextIO | None = None) -> None:
    target = stream or sys.stdout
    value = str(text)
    try:
        print(value, file=target)
    except UnicodeEncodeError:
        # Windows 控制台/桥接子进程可能继承非 UTF-8 代码页。不要让输出编码错误打断会话或 ActivationForm。
        safe = value.encode("utf-8", errors="replace").decode("utf-8", errors="replace")
        try:
            target.buffer.write((safe + "\n").encode("utf-8", errors="replace"))  # type: ignore[attr-defined]
            target.flush()
        except Exception:
            print(safe.encode(getattr(target, "encoding", None) or "utf-8", errors="backslashreplace").decode(getattr(target, "encoding", None) or "utf-8", errors="replace"), file=target)


def _display_workspace_path(path: Path) -> str:
    """Return a reproducible, non-absolute workspace label for status output."""
    try:
        resolved = Path(path).expanduser().resolve()
        cwd = Path.cwd().resolve()
        if resolved == cwd:
            return "."
        try:
            rel = resolved.relative_to(cwd)
            return "./" + rel.as_posix()
        except ValueError:
            return f"<external-workspace:{resolved.name or 'workspace'}>"
    except Exception:
        return "<workspace-unavailable>"


def format_status(context: AgentShellContext) -> str:
    cfg = context.config
    return "\n".join(
        [
            "临渊者 Runtime 启动器状态：",
            f"- kernel_importable: {context.kernel_importable}",
            f"- provider: {cfg.provider}",
            f"- model: {cfg.model or '<未配置>'}",
            f"- endpoint_state: {cfg.sanitized_dict().get('base_url')}",
            f"- credential_state: {cfg.sanitized_dict().get('api_key')}",
            f"- tool_execution_mode: {cfg.tool_execution_mode.value}",
            f"- planner_mode: {cfg.planner_mode.value}",
            f"- workspace: {_display_workspace_path(context.workspace)}",
            f"- workspace_writable: {context.tool_bridge.capability_enabled('write_file')}",
            f"- max_steps: {context.max_steps}",
            f"- pending_confirmations: {len(context.runtime.pending_confirmations())}",
            f"- session_id: {context.session.session_id}",
            f"- messages_count: {context.session.message_count}",
            f"- context_memory_records: {context.runtime.context_snapshot().get('session_records', 0)}",
            f"- project_index_status: {context.runtime.project_snapshot().get('status', 'ready')}",
            f"- quality_gate_decision: {context.runtime.quality_gate_snapshot().get('decision', context.runtime.quality_gate_snapshot().get('status', 'empty'))}",
            f"- delivery_status: {context.runtime.delivery_snapshot().get('release_gate', {}).get('decision', context.runtime.delivery_snapshot().get('status', 'empty'))}",
            f"- experience_status: {context.runtime.experience_snapshot().get('status', 'empty')}",
            f"- skill_queue_status: {context.runtime.skill_queue_snapshot().get('status', 'empty')}",
            f"- tool_request_status: {context.runtime.tool_request_snapshot().get('status', 'empty')}",
            f"- exoskeleton_status: {context.runtime.exoskeleton_snapshot().get('status', 'empty')}",
            f"- shell_mount_status: {context.runtime.shell_mount_snapshot().get('status', 'empty')}",
            f"- project_repair_status: {context.runtime.project_repair_snapshot().get('status', 'empty')}",
            f"- delivery_standard_status: {context.runtime.delivery_standardization_snapshot().get('status', 'empty')}",
            f"- provider_adaptation_status: {context.runtime.provider_adaptation_snapshot().get('status', 'empty')}",
            f"- learning_convergence_status: {context.runtime.learning_convergence_snapshot().get('status', 'empty')}",
            f"- recovery_coordination_status: {context.runtime.recovery_coordination_snapshot().get('status', 'empty')}",
            f"- governance_execution_status: {context.runtime.governance_execution_snapshot().get('status', 'empty')}",
            f"- planner_context_status: {context.runtime.planner_context_snapshot().get('status', 'empty')}",
            f"- planner_execution_status: {context.runtime.planner_execution_snapshot().get('status', 'empty')}",
            f"- execution_chain_freeze_status: {context.runtime.execution_chain_freeze_snapshot().get('status', 'not_ready')}",
            f"- l6_38_p0_status: {context.runtime.p0_system_integration_snapshot().get('status', 'empty')}",
        ]
    )


def format_config(context: AgentShellContext) -> str:
    return json.dumps(context.config.sanitized_dict(), ensure_ascii=False, indent=2)


def format_tools(context: AgentShellContext) -> str:
    rows = ["L6.37 受治理工具注册表："]
    for tool in context.runtime.available_tools():
        rows.append(f"- {tool.name} [{tool.default_risk}] {tool.description}")
    return "\n".join(rows)


def format_policy(context: AgentShellContext) -> str:
    return "\n".join(
        [
            "L6.37 执行链全线贯通冻结默认执行策略：",
            "- A0/A1/A2/A3：在工作区、allowlist、预算和审计链内自动执行",
            "- 执行力优先：Skill 候选、Tool 请求、PlannerHint、最小 Tool 票据默认放开",
            "- L6.20 synthesize_experience_candidates：只生成候选，不写 Skill、不生产 Tool",
            "- L6.21 queue_skill_candidates：只生成草案版本和审阅队列，不注册、不激活",
            "- L6.22 queue_tool_production_requests：只生成 Tool 生产请求和沙箱验证前置队列，不生产、不注册、不释放",
            "- L6.23 build_execution_exoskeleton：把候选链压缩成 PlannerHint + ToolCandidateTicket，不继续堆重型队列",
            "- L6.24 build_shell_system_mount：只读映射 18 系统已装内容，外壳挂载，不改内核、不注册正式工具",
            "- L6.25 build_project_repair_plan：只生成 PatchPlan / RegressionHint / RollbackEvidence，不应用补丁、不写文件、不改内核",
            "- L6.26 build_delivery_standardization：只生成 ChangeSet/TestEvidence/Manifest/Integrity/Todo 证据，不生成正式发布 ZIP、不写文件、不改内核",
            "- L6.27 build_provider_adaptation：只生成 Provider 声明式适配外壳，不触网、不读密钥、不注册正式适配器",
            "- L6.28 build_learning_convergence：把经验/Skill/Tool/外骨骼结果合流为 Planner 可消费执行卡片，不写记忆、不注册、不生产",
            "- L6.29 build_recovery_coordination：把 FailureSignal/RepairCandidate/HandoffDigest/BudgetUpdate/ResumePlan 压成恢复续接路径，不派生子智能体、不执行补丁、不改预算、不改内核",
            "- L6.30 build_governance_execution：把治理压成 A0-A4 快车道、A5 硬边界、发布/注册/激活护栏，不改策略不执行不改内核",
            "- L6.31 build_planner_context：把 L6.24-L6.30 外壳输出统一为 UnifiedPlannerContext / ExecutionStepDraft / PlannerResumeEnvelope，不执行、不注册、不读密钥、不改内核",
            "- L6.32 planner_execute：Planner 只生成计划，真实执行由 LongChainRunner + ExecutionSpine 接管，并输出状态机、replay、resume 信封",
            "- L6.34 model_suggest：DeepSeek plan 样本回放、CLI 最近会话上下文注入、plan_failed 回退保真，不触网不读密钥",
            "- L6.35 Step 状态机：planned/queued/running/succeeded/failed/blocked/confirmation_required/skipped/recovered/timeout 可回放",
            "- L6.36 恢复与质量门：FailureClassification/RecoveryPlan/ReplayReport/QualityGateResult 纳入执行报告",
            "- L6.37 执行链冻结：后续系统只能提交 Hint/Step/Ticket/Evidence/Report，不得产生第二执行入口",
            "- L6.38 P0 接入：Provider/Budget/Skill/Handoff 统一输出 Hint/Ticket/Envelope/Evidence/Report，并通过 PlannerExecutionController 执行",
            "- A4：生成确认票据，暂停执行；用户 /confirm 后仍走 registry/adapter/audit",
            "- A5：硬阻断",
            f"- 当前工具模式：{context.config.tool_execution_mode.value}",
            f"- 当前计划器模式：{context.config.planner_mode.value}",
        ]
    )


def format_audit(context: AgentShellContext) -> str:
    events = context.runtime.audit.recent_summary()
    if not events:
        return "暂无审计事件。"
    return json.dumps(events, ensure_ascii=False, indent=2)


def format_prompt_trace(context: AgentShellContext) -> str:
    rows = recent_prompt_trace_summary(context, limit=8)
    if not rows:
        return "暂无 PromptTrace 记录。"
    return json.dumps(rows, ensure_ascii=False, indent=2)


def format_prompt_tuner(context: AgentShellContext) -> str:
    return json.dumps(prompt_tuning_public_summary(context), ensure_ascii=False, indent=2)


def format_tickets(context: AgentShellContext) -> str:
    tickets = context.runtime.pending_confirmations()
    if not tickets:
        return "暂无待确认票据。"
    return json.dumps(tickets, ensure_ascii=False, indent=2)






def format_quality_gate(context: AgentShellContext) -> str:
    snapshot = context.runtime.quality_gate_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无质量门裁决。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_quality_gate(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "quality_gate.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_quality_gate_json(target)
    write_line(f"质量门裁决已导出：{path}")


def _run_quality_gate(context: AgentShellContext, path_text: str) -> None:
    target = path_text.strip() or "."
    result = context.runtime.run_quality_gate(
        workspace=context.workspace,
        path=target,
        tool_mode=context.config.tool_execution_mode,
        max_steps=context.max_steps,
        require_pytest=True,
        package_on_pass=True,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    verdict = context.runtime.quality_gate_snapshot()
    if verdict.get("decision"):
        write_line(f"质量门：{verdict.get('decision')}；allow_package={verdict.get('allow_package')}")
    if result.projection.artifacts:
        write_line("产物：")
        for artifact in result.projection.artifacts:
            write_line(f"- {artifact}")


def format_delivery(context: AgentShellContext) -> str:
    snapshot = context.runtime.delivery_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无交付 Manifest。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_delivery(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "delivery_manifest.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_delivery_json(target)
    write_line(f"交付 Manifest 已导出：{path}")


def _run_release(context: AgentShellContext, path_text: str) -> None:
    try:
        parts = shlex.split(path_text) if path_text else []
    except ValueError:
        parts = path_text.split()
    target = parts[0] if parts else "dist/l6_19_release_bundle.zip"
    source = parts[1] if len(parts) >= 2 else "."
    result = context.runtime.run_release(
        workspace=context.workspace,
        path=source,
        target=target,
        tool_mode=context.config.tool_execution_mode,
        max_steps=context.max_steps,
        require_pytest=True,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    manifest = context.runtime.delivery_snapshot()
    release_gate = manifest.get("release_gate", {}) if isinstance(manifest, dict) else {}
    if release_gate:
        write_line(f"Release Gate：{release_gate.get('decision')}；allow_release={release_gate.get('allow_release')}")
    if result.projection.artifacts:
        write_line("产物：")
        for artifact in result.projection.artifacts:
            write_line(f"- {artifact}")

def format_experience(context: AgentShellContext) -> str:
    snapshot = context.runtime.experience_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无经验沉淀候选报告。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_experience(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "experience_synthesis.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_experience_json(target)
    write_line(f"经验沉淀候选报告已导出：{path}")


def _run_reflect(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_experience_synthesis(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 2),
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.experience_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"经验沉淀：{report.get('status')}；Skill 候选={len(report.get('skill_candidates', []))}；Tool 缺口={len(report.get('tool_gap_candidates', []))}"
        )


def format_skill_queue(context: AgentShellContext) -> str:
    snapshot = context.runtime.skill_queue_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 Skill 草案版本审阅队列。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_skill_queue(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "skill_review_queue.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_skill_queue_json(target)
    write_line(f"Skill 审阅队列已导出：{path}")


def _run_skill_queue_build(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_skill_queue_build(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 3),
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    queue = context.runtime.skill_queue_snapshot()
    if queue.get("status") and queue.get("status") != "empty":
        write_line(
            f"Skill 审阅队列：{queue.get('status')}；草案版本={len(queue.get('draft_versions', []))}；队列项={len(queue.get('review_queue', []))}"
        )


def format_tool_request(context: AgentShellContext) -> str:
    snapshot = context.runtime.tool_request_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 Tool 生产请求队列。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_tool_request(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "tool_production_requests.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_tool_request_json(target)
    write_line(f"Tool 生产请求队列已导出：{path}")


def _run_tool_request_build(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_tool_request_build(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 3),
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.tool_request_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"Tool 生产请求：{report.get('status')}；请求={len(report.get('production_requests', []))}；沙箱验证计划={len(report.get('sandbox_validation_plans', []))}；队列项={len(report.get('review_queue', []))}"
        )



def format_exoskeleton(context: AgentShellContext) -> str:
    snapshot = context.runtime.exoskeleton_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 LLM 外骨骼压缩报告。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_exoskeleton(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "execution_exoskeleton.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_exoskeleton_json(target)
    write_line(f"LLM 外骨骼压缩报告已导出：{path}")


def _run_exoskeleton_build(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_exoskeleton_build(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 4),
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.exoskeleton_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"LLM 外骨骼：{report.get('status')}；PlannerHint={len(report.get('planner_hints', []))}；Tool 票据={len(report.get('tool_candidate_tickets', []))}"
        )




def format_shell_mount(context: AgentShellContext) -> str:
    snapshot = context.runtime.shell_mount_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.24 十八系统壳装报告。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_shell_mount(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "shell_system_mount.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_shell_mount_json(target)
    write_line(f"十八系统壳装报告已导出：{path}")


def _run_shell_mount_build(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_shell_mount_build(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=1,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.shell_mount_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"十八系统壳装：{report.get('status')}；系统={report.get('system_count')}；active={report.get('active_shell_systems')}；partial={report.get('partial_shell_systems')}；reserved={report.get('reserved_shell_systems')}"
        )


def format_project_repair(context: AgentShellContext) -> str:
    snapshot = context.runtime.project_repair_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.25 工程修复计划。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_project_repair(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "project_repair_plan.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_project_repair_json(target)
    write_line(f"L6.25 工程修复计划已导出：{path}")


def _run_project_repair_plan(context: AgentShellContext, path_text: str) -> None:
    try:
        parts = shlex.split(path_text) if path_text else []
    except ValueError:
        parts = path_text.split()
    target = parts[0] if parts else "."
    notes = " ".join(parts[1:]) if len(parts) > 1 else path_text
    result = context.runtime.run_project_repair_plan(
        workspace=context.workspace,
        path=target,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 8),
        run_compileall=True,
        run_pytest=False,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.project_repair_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"L6.25 工程修复计划：{report.get('status')}；PatchPlan={len(report.get('patch_plan', []))}；RegressionHint={len(report.get('regression_hints', []))}；shell_only={report.get('shell_only')}"
        )




def format_delivery_standardization(context: AgentShellContext) -> str:
    snapshot = context.runtime.delivery_standardization_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.26 标准化交付证据。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_delivery_standardization(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "delivery_standardization.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_delivery_standardization_json(target)
    write_line(f"L6.26 标准化交付证据已导出：{path}")


def _run_delivery_standardization(context: AgentShellContext, path_text: str) -> None:
    try:
        parts = shlex.split(path_text) if path_text else []
    except ValueError:
        parts = path_text.split()
    target = parts[0] if parts else "."
    notes = " ".join(parts[1:]) if len(parts) > 1 else path_text
    result = context.runtime.run_delivery_standardization(
        workspace=context.workspace,
        path=target,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 10),
        run_compileall=True,
        run_pytest=False,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.delivery_standardization_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"L6.26 标准化交付证据：{report.get('status')}；ChangeSet={len(report.get('change_set', []))}；TestEvidence={len(report.get('test_evidence', []))}；Todo={len(report.get('todo_report', []))}；release_ready={report.get('release_ready')}"
        )



def format_provider_adaptation(context: AgentShellContext) -> str:
    snapshot = context.runtime.provider_adaptation_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.27 Provider 适配外壳报告。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_provider_adaptation(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "provider_adaptation.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_provider_adaptation_json(target)
    write_line(f"L6.27 Provider 适配外壳报告已导出：{path}")


def _run_provider_adaptation(context: AgentShellContext, path_text: str) -> None:
    try:
        parts = shlex.split(path_text) if path_text else []
    except ValueError:
        parts = path_text.split()
    target = parts[0] if parts else "."
    notes = " ".join(parts[1:]) if len(parts) > 1 else path_text
    result = context.runtime.run_provider_adaptation(
        workspace=context.workspace,
        path=target,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 8),
        refresh_shell_mount=True,
        refresh_delivery_standard=False,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.provider_adaptation_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"L6.27 Provider 适配外壳：{report.get('status')}；Provider={report.get('provider_count')}；Route={report.get('route_count')}；declaration_only={report.get('provider_declaration_only')}；shell_only={report.get('shell_only')}"
        )


def format_learning_convergence(context: AgentShellContext) -> str:
    snapshot = context.runtime.learning_convergence_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.28 执行合流报告。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_learning_convergence(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "learning_convergence.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_learning_convergence_json(target)
    write_line(f"L6.28 执行合流报告已导出：{path}")


def _run_learning_convergence(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_learning_convergence_build(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 6),
        max_items=18,
        refresh_sources=True,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.learning_convergence_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"L6.28 执行合流：{report.get('status')}；PlannerHintRoute={report.get('planner_hint_count')}；SkillDraftRoute={report.get('skill_draft_count')}；ToolCandidateRoute={report.get('tool_candidate_count')}；Cards={report.get('consumption_card_count')}"
        )


def format_recovery_coordination(context: AgentShellContext) -> str:
    snapshot = context.runtime.recovery_coordination_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.29 恢复协调报告。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_recovery_coordination(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "recovery_coordination.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_recovery_coordination_json(target)
    write_line(f"L6.29 恢复协调报告已导出：{path}")


def _run_recovery_coordination(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_recovery_coordination_build(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 8),
        max_items=12,
        refresh_sources=True,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.recovery_coordination_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"L6.29 恢复协调：{report.get('status')}；FailureSignal={report.get('failure_signal_count')}；RepairCandidate={report.get('repair_candidate_count')}；HandoffDigest={report.get('handoff_digest_count')}；BudgetUpdate={report.get('budget_update_count')}；ResumePlan={report.get('resume_plan_count')}"
        )


def format_governance_execution(context: AgentShellContext) -> str:
    snapshot = context.runtime.governance_execution_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.30 治理执行力化报告。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_governance_execution(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "governance_execution.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_governance_execution_json(target)
    write_line(f"L6.30 治理执行力化报告已导出：{path}")


def _run_governance_execution(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_governance_execution_build(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 8),
        max_items=12,
        refresh_sources=True,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.governance_execution_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"L6.30 治理执行力化：{report.get('status')}；FastLane={report.get('fast_lane_count')}；Boundary={report.get('boundary_count')}；Hard={report.get('hard_boundary_count')}；ReleaseGate={report.get('release_gate_count')}；Hint={report.get('planner_hint_count')}"
        )


def format_planner_context(context: AgentShellContext) -> str:
    snapshot = context.runtime.planner_context_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.31 统一 Planner 上下文。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_planner_context(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "planner_context.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_planner_context_json(target)
    write_line(f"L6.31 统一 Planner 上下文已导出：{path}")


def _run_planner_context(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_planner_context_build(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 10),
        max_items=16,
        refresh_sources=True,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.planner_context_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"L6.31 统一 Planner：{report.get('status')}；Source={report.get('source_evidence_count')}；Hint={report.get('planner_hint_count')}；Step={report.get('next_execution_step_count')}；FastLane={report.get('fast_lane_action_count')}；Blocked={report.get('blocked_action_count')}；Confirm={report.get('required_confirmation_count')}"
        )


def format_planner_execution(context: AgentShellContext) -> str:
    snapshot = context.runtime.planner_execution_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.32 Planner 执行主链报告。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_planner_execution(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "planner_execution.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_planner_execution_json(target)
    write_line(f"L6.32 Planner 执行主链报告已导出：{path}")




def format_execution_chain_contract(context: AgentShellContext) -> str:
    return json.dumps(context.runtime.execution_chain_contract_snapshot(), ensure_ascii=False, indent=2)


def _export_execution_chain_contract(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "execution_chain_contract.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_execution_chain_contract_json(target)
    write_line(f"L6.37 执行链冻结契约已导出：{path}")


def format_execution_chain_freeze(context: AgentShellContext) -> str:
    return json.dumps(context.runtime.execution_chain_freeze_snapshot(), ensure_ascii=False, indent=2)


def _export_execution_chain_freeze(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "execution_chain_freeze.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_execution_chain_freeze_json(target)
    write_line(f"L6.37 执行链冻结验收报告已导出：{path}")

def _run_model_plan_replay(context: AgentShellContext) -> None:
    report = context.runtime.run_model_plan_compat_replay()
    write_line(json.dumps(report, ensure_ascii=False, indent=2))


def _run_planner_execution(context: AgentShellContext, user_text: str) -> None:
    result = context.runtime.run_planner_execution_task(
        user_text,
        workspace=context.workspace,
        tool_mode=context.config.tool_execution_mode,
        max_steps=context.max_steps,
        planner_mode=context.config.planner_mode,
        model_config=context.config,
        model_client=context.model_client,
        refresh_planner_context=False,
        external_context_hint=context.session.build_context_hint(turns=3),
    )
    context.last_runtime_result = result
    _record_runtime_exchange(context, user_text, result)
    if result.planner_result is not None:
        write_line(f"[计划器] {result.planner_result.message}")
    write_line(result.projection.summary)
    report = context.runtime.planner_execution_snapshot()
    if report.get("status") and report.get("status") != "empty":
        resume = report.get("resume_envelope", {})
        write_line(
            f"L6.32 执行主链：{report.get('status')}；executed={report.get('executed_steps')}/{report.get('total_steps')}；"
            f"failed={report.get('failed_steps')}；blocked={report.get('blocked_steps')}；confirm={report.get('confirmation_required_steps')}；"
            f"resume={resume.get('resume_mode')}"
        )


def format_p0_system_integration(context: AgentShellContext) -> str:
    snapshot = context.runtime.p0_system_integration_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.38 P0 系统接入报告。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_p0_system_integration(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "l6_38_p0_system_integration.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_p0_system_integration_json(target)
    write_line(f"L6.38 P0 系统接入报告已导出：{path}")


def _run_p0_system_integration(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_l6_38_p0_system_integration(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 10),
        max_items=8,
        refresh_sources=True,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.p0_system_integration_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"L6.38 P0 接入：{report.get('status')}；provider={bool(report.get('provider'))}；"
            f"budget={bool(report.get('budget'))}；skill={bool(report.get('skill'))}；handoff={bool(report.get('handoff'))}；"
            f"digest={report.get('report_digest', '')}"
        )




def format_p0_system_integration_two(context: AgentShellContext) -> str:
    snapshot = context.runtime.p0_system_integration_two_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无 L6.39 P0 系统接入二报告。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_p0_system_integration_two(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "l6_39_p0_system_integration_two.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_p0_system_integration_two_json(target)
    write_line(f"L6.39 P0 系统接入二报告已导出：{path}")


def _run_p0_system_integration_two(context: AgentShellContext, notes: str) -> None:
    result = context.runtime.run_l6_39_p0_system_integration_two(
        workspace=context.workspace,
        notes=notes,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 10),
        max_items=8,
        refresh_sources=True,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    report = context.runtime.p0_system_integration_two_snapshot()
    if report.get("status") and report.get("status") != "empty":
        write_line(
            f"L6.39 P0 接入二：{report.get('status')}；memory={bool(report.get('memory'))}；"
            f"audit={bool(report.get('audit'))}；recovery={bool(report.get('recovery'))}；"
            f"quality_gate={bool(report.get('quality_gate'))}；digest={report.get('report_digest', '')}"
        )


def format_diagnosis(context: AgentShellContext) -> str:
    snapshot = context.runtime.diagnosis_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无工程诊断。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_diagnosis(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "diagnosis.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_diagnosis_json(target)
    write_line(f"工程诊断已导出：{path}")


def _diagnose_project(context: AgentShellContext, path_text: str) -> None:
    target = path_text.strip() or "."
    result = context.runtime.run_engineering_diagnosis(
        workspace=context.workspace,
        path=target,
        tool_mode=context.config.tool_execution_mode,
        max_steps=min(context.max_steps, 8),
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)


def _repair_loop(context: AgentShellContext, path_text: str) -> None:
    target = path_text.strip() or "."
    result = context.runtime.run_engineering_repair_loop(
        workspace=context.workspace,
        path=target,
        tool_mode=context.config.tool_execution_mode,
        max_steps=context.max_steps,
        external_context_hint=context.session.build_context_hint(turns=3),
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)
    if result.projection.artifacts:
        write_line("产物：")
        for artifact in result.projection.artifacts:
            write_line(f"- {artifact}")

def format_project_index(context: AgentShellContext) -> str:
    snapshot = context.runtime.project_snapshot()
    if snapshot.get("status") == "empty":
        return snapshot.get("message", "暂无项目索引。")
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_project_index(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "project_index.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_project_json(target)
    write_line(f"项目索引已导出：{path}")


def _scan_project(context: AgentShellContext, path_text: str) -> None:
    target = path_text.strip() or "."
    result = context.runtime.execute_plan(
        [ToolInvocation("scan_project", {"path": target})],
        workspace=context.workspace,
        user_message=f"scan_project {target}",
        tool_mode=context.config.tool_execution_mode,
        max_steps=1,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)

def format_context_memory(context: AgentShellContext) -> str:
    snapshot = context.runtime.context_snapshot()
    if not snapshot.get("recent"):
        return "暂无上下文/记忆摘要。"
    return json.dumps(snapshot, ensure_ascii=False, indent=2)


def _export_context_memory(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "context_memory.json")
    target = Path(path_text)
    if not target.is_absolute():
        target = Path(context.workspace) / target
    path = context.runtime.export_context_json(target)
    write_line(f"上下文摘要已导出：{path}")


_CLI_SUCCESS_STATUSES = {"ok", "completed", "completed_pass", "completed_with_warnings", "deterministic_fallback", "partial_with_resume"}


def _runtime_status_is_cli_success(status: object) -> bool:
    return str(status or "").strip().lower() in _CLI_SUCCESS_STATUSES


def _runtime_result_session_summary(result: object) -> str:
    """把受治理执行结果压缩写回会话，供后续普通对话续接上文。"""
    plan = getattr(result, "plan", []) or []
    projection = getattr(result, "projection", None)
    chain_summary = getattr(result, "chain_summary", None)
    tool_names = [getattr(step, "tool_name", "") for step in plan][:8]
    lines = ["[运行链上下文摘要]"]
    if projection is not None:
        lines.append(f"状态：{getattr(projection, 'status', '')}。")
        summary = str(getattr(projection, "summary", "") or "")[:600]
        if summary:
            lines.append(f"摘要：{summary}")
    if tool_names:
        lines.append(f"已规划/执行工具：{', '.join(tool_names)}。")
    if chain_summary is not None:
        lines.append(
            "长链："
            f"total={getattr(chain_summary, 'total_steps', '')}, "
            f"executed={getattr(chain_summary, 'executed_steps', '')}, "
            f"status={getattr(chain_summary, 'status', '')}。"
        )
    artifacts = list(getattr(projection, "artifacts", []) or []) if projection is not None else []
    if artifacts:
        lines.append("产物：" + ", ".join(str(item) for item in artifacts[:5]))
    return "\n".join(lines)[:1800]


def _record_runtime_exchange(context: AgentShellContext, user_text: str, result: object) -> None:
    """记录执行型任务对话摘要，避免 model_suggest 失败回退普通对话时丢上文。"""
    context.session.add_user(user_text)
    context.session.add_assistant(_runtime_result_session_summary(result))


def _conversation_file() -> Path | None:
    raw = os.environ.get("TIANGONG_CONVERSATION_FILE", "").strip()
    if not raw:
        return None
    try:
        return Path(raw).expanduser().resolve()
    except Exception:
        return None


def _normalize_history_message(item: object) -> dict[str, str] | None:
    if not isinstance(item, dict):
        return None
    role = str(item.get("role") or "").strip().lower()
    if role not in {"system", "user", "assistant"}:
        return None
    content = str(item.get("content") or "").replace("\x00", "").strip()
    if not content:
        return None
    return {"role": role, "content": content[:12000]}


def _load_conversation(context: AgentShellContext) -> None:
    path = _conversation_file()
    if path is None or not path.exists():
        return
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return
    records = raw.get("messages") if isinstance(raw, dict) else raw
    if not isinstance(records, list):
        return
    messages = [_normalize_history_message(item) for item in records]
    clean = [item for item in messages if item is not None]
    if not clean:
        return
    current_system = [msg for msg in context.session.messages if msg.get("role") == "system"][:1]
    if not current_system:
        current_system = [clean[0]] if clean and clean[0].get("role") == "system" else []
    dialog = [msg for msg in clean if msg.get("role") != "system"][-40:]
    context.session.messages = current_system + dialog


def _save_conversation(context: AgentShellContext) -> None:
    path = _conversation_file()
    if path is None:
        return
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        system = [msg for msg in context.session.messages if msg.get("role") == "system"][:1]
        dialog = [msg for msg in context.session.messages if msg.get("role") != "system"][-40:]
        payload = {
            "schema": "tiangong.l6_72_10.desktop_conversation.v1",
            "message_count": len(system) + len(dialog),
            "messages": system + dialog,
        }
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
    except Exception:
        return


def run_runtime_task(
    context: AgentShellContext,
    user_text: str,
    *,
    activation_form: ActivationForm | None = None,
    planner_mode_override: PlannerMode | None = None,
) -> int:
    planner_mode = planner_mode_override or context.config.planner_mode
    result = context.runtime.run_text(
        user_text,
        workspace=context.workspace,
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=context.max_steps,
        planner_mode=planner_mode,
        model_config=context.config,
        model_client=context.model_client,
        external_context_hint=context.session.build_context_hint(turns=3),
        activation_form=activation_form,
    )
    context.last_runtime_result = result
    if not result.has_plan:
        if result.planner_result is not None:
            write_line(f"[计划器] {result.planner_result.message}")
            if result.planner_result.issues:
                write_line(json.dumps([issue.__dict__ for issue in result.planner_result.issues], ensure_ascii=False, indent=2))
        # L6.72.54：work 模式禁止静默退回 run_chat_once。无计划也必须输出 execution_report。
        _record_runtime_exchange(context, user_text, result)
        if getattr(result, "projection", None) is not None and getattr(result.projection, "summary", ""):
            write_line(result.projection.summary)
        return 0 if _runtime_status_is_cli_success(getattr(result.projection, "status", "")) else 2
    _record_runtime_exchange(context, user_text, result)
    if result.planner_result is not None:
        write_line(f"[计划器] {result.planner_result.message}")
    write_line(result.projection.summary)
    if result.projection.artifacts:
        write_line("产物：")
        for artifact in result.projection.artifacts:
            write_line(f"- {artifact}")
    return 0 if _runtime_status_is_cli_success(result.projection.status) else 2


def preview_runtime_plan(context: AgentShellContext, user_text: str) -> int:
    preview = context.runtime.preview_plan(
        user_text,
        planner_mode=context.config.planner_mode,
        model_config=context.config,
        model_client=context.model_client,
        max_steps=context.max_steps,
        external_context_hint=context.session.build_context_hint(turns=3),
    )
    write_line(json.dumps(preview, ensure_ascii=False, indent=2))
    return 0 if preview.get("ok") else 2


def _messages_for_plan_failed_fallback(context: AgentShellContext, user_text: str) -> list[dict[str, str]]:
    """计划校验失败回退普通对话时，显式携带最近两轮上下文。

    不能只发当前 user_message；否则用户说“上面代码”时，模型可能看不到上一轮 assistant
    的完整正文。这里保留 system + 最近两轮 + 当前用户消息。
    """
    system_messages = [message for message in context.session.messages if message.get("role") == "system"][:1]
    recent_dialog = [message for message in context.session.messages if message.get("role") != "system"][-4:]
    return system_messages + recent_dialog + [{"role": "user", "content": user_text}]


def _provider_not_configured_message() -> str:
    return "尚未配置模型接口。请进入【设置】页填写服务地址、模型名与 API Key，保存后即可进入真实模型链路。"


_INTERNAL_REPLY_NOISE_MARKERS = ("[计划器]", "【计划器】", "[运行链]", "【运行链】", "未生成可执行计划")


def _strip_internal_reply_noise(content: str) -> str:
    """从最终用户回复中移除内部运行链/Planner 噪声行。"""
    lines: list[str] = []
    for raw in str(content or "").replace("\x00", "").splitlines():
        line = raw.strip()
        if not line:
            lines.append(raw)
            continue
        if any(marker in line for marker in _INTERNAL_REPLY_NOISE_MARKERS):
            continue
        lines.append(raw)
    visible = "\n".join(lines).strip()
    if visible:
        return visible
    return "模型回复只包含内部运行信息，已隐藏。请重新提问，或切换诊断任务模式查看内部状态。"


def _task_mode_from_env() -> str:
    value = os.environ.get("TIANGONG_TASK_MODE", "ordinary_chat").strip().lower().replace("-", "_")
    return value or "ordinary_chat"


def run_chat_once(context: AgentShellContext, user_text: str, *, plan_failed: bool = False) -> int:
    # L6.72.14: 每轮模型调用前刷新器官信号卡，并记录 PromptTrace 起点；只更新 system prompt，不动对话历史。
    task_mode = _task_mode_from_env()
    refresh_session_system_prompt(context, user_text=user_text, task_mode=task_mode)
    if not provider_is_ready(context.config):
        message = _provider_not_configured_message()
        record_prompt_trace_outcome(
            context,
            assistant_text=message,
            model_ok=False,
            provider_not_configured=True,
            error_summary="provider_not_configured",
            plan_failed=plan_failed,
        )
        write_line(message)
        return 0
    if plan_failed:
        chat_messages = _messages_for_plan_failed_fallback(context, user_text)
    else:
        context.session.add_user(user_text)
        chat_messages = context.session.messages
    compiled_prompt = compile_existing_messages_envelope(
        chat_messages,
        phase="chat_execution",
        output_contract="normal_chat",
        metadata={"route": "run_chat_once", "plan_failed": bool(plan_failed)},
    )
    runtime_result = context.runtime.run_model_chat(
        chat_messages,
        model_config=context.config,
        model_client=context.model_client,
        workspace=context.workspace,
        user_message=user_text,
        # L6.13: 工具执行模式可以 disabled，但模型调用仍应走 Runtime 审计链。
        tool_mode=ToolExecutionMode.RUNTIME_GOVERNED,
        max_steps=1,
        compiled_prompt=compiled_prompt,
    )
    context.last_runtime_result = runtime_result
    if not runtime_result.results:
        error = "模型调用未产生结果。"
        record_prompt_trace_outcome(context, model_ok=False, error_summary=error, plan_failed=plan_failed)
        write_line(f"[错误] {error}", stream=sys.stderr)
        return 2
    model_result = runtime_result.results[0]
    if not model_result.ok:
        error = str(model_result.output_summary)
        record_prompt_trace_outcome(context, model_ok=False, error_summary=error, plan_failed=plan_failed)
        write_line(f"[错误] {error}", stream=sys.stderr)
        return 2
    raw_content = str(model_result.data.get("content", ""))
    record_prompt_trace_outcome(context, assistant_text=raw_content, model_ok=True, plan_failed=plan_failed)
    content = _strip_internal_reply_noise(raw_content)
    if plan_failed:
        context.session.add_user(user_text)
    context.session.add_assistant(content)
    write_line(content)
    return 0


def _frontend_mode_preference() -> str:
    raw = (os.environ.get("LINYUANZHE_FRONTEND_WORK_MODE") or os.environ.get("TIANGONG_USER_SELECTED_MODE") or "chat").strip().lower().replace("-", "_")
    if raw in {"work", "工作", "干活", "code", "file", "document", "long_chain"}:
        return "work"
    return "chat"


def run_once(context: AgentShellContext, user_text: str) -> int:
    _load_conversation(context)
    try:
        # L6.72.51：每轮先进入 PromptIntegrator 中转的 ActivationForm 裁决。
        # Runtime 不用关键词/后缀判模式；LLM 填 chat/work 后 Runtime 才激活对应链路。
        refresh_session_system_prompt(context, user_text=user_text, task_mode="activation_decision")
        selected_mode = _frontend_mode_preference()
        if not provider_is_ready(context.config):
            if selected_mode == "work":
                return run_runtime_task(
                    context,
                    user_text,
                    activation_form=None,
                    planner_mode_override=PlannerMode.MODEL_SUGGEST,
                )
            return run_chat_once(context, user_text)
        decision = context.runtime.activation_decider.decide(
            user_text,
            model_config=context.config,
            model_client=context.model_client,
            user_selected_mode=selected_mode,
            max_steps=context.max_steps,
            context_hint=context.session.build_context_hint(turns=3),
        )
        if not decision.ok or decision.form is None:
            write_line(f"[激活失败] {decision.message}", stream=sys.stderr)
            if selected_mode == "work":
                return run_runtime_task(
                    context,
                    user_text,
                    activation_form=None,
                    planner_mode_override=PlannerMode.MODEL_SUGGEST,
                )
            return 2
        form = decision.form
        if form.mode == "work" and form.tools_requested:
            return run_runtime_task(
                context,
                user_text,
                activation_form=form,
                planner_mode_override=PlannerMode.MODEL_SUGGEST,
            )
        if selected_mode == "work":
            return run_runtime_task(
                context,
                user_text,
                activation_form=form,
                planner_mode_override=PlannerMode.MODEL_SUGGEST,
            )
        return run_chat_once(context, user_text)
    finally:
        _save_conversation(context)


def _confirm_ticket(context: AgentShellContext, ticket_id: str) -> None:
    result = context.runtime.confirm_ticket(
        ticket_id,
        workspace=context.workspace,
        tool_mode=context.config.tool_execution_mode,
        max_steps=1,
    )
    context.last_runtime_result = result
    write_line(result.projection.summary)


def _deny_ticket(context: AgentShellContext, ticket_id: str) -> None:
    write_line(json.dumps(context.runtime.deny_ticket(ticket_id), ensure_ascii=False, indent=2))


def _export_audit(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        path_text = str(Path(context.workspace) / "runtime_audit.jsonl")
    path = context.runtime.export_audit_jsonl(path_text)
    write_line(f"审计 JSONL 已导出：{path}")


def _replay_audit(context: AgentShellContext, path_text: str) -> None:
    if not path_text:
        write_line("请提供审计 JSONL 路径。", stream=sys.stderr)
        return
    summary = context.runtime.replay_audit_jsonl(path_text)
    write_line(json.dumps(summary.to_dict(), ensure_ascii=False, indent=2))


def _export_report(context: AgentShellContext, path_text: str) -> None:
    if context.last_runtime_result is None:
        write_line("暂无可导出的运行结果。请先执行 /run 或一次 governed 任务。", stream=sys.stderr)
        return
    if not path_text:
        path_text = str(Path(context.workspace) / "runtime_report.json")
    path = export_runtime_report(context.last_runtime_result, path_text)
    write_line(f"运行报告已导出：{path}")


def run_interactive(context: AgentShellContext) -> int:
    write_line("临渊者 L6.38 P0 系统接入启动器")
    write_line("输入 /help 查看命令；输入 /exit 退出。")
    write_line(format_status(context))
    while True:
        try:
            user_text = input("\n你> ").strip()
        except (EOFError, KeyboardInterrupt):
            write_line("\n已退出。")
            return 0
        if not user_text:
            continue
        command = user_text.lower()
        if command in {"/exit", "/quit"}:
            write_line("已退出。")
            return 0
        if command == "/help":
            write_line(HELP_TEXT)
            continue
        if command == "/status":
            write_line(format_status(context))
            continue
        if command == "/config":
            write_line(format_config(context))
            continue
        if command == "/tools":
            write_line(format_tools(context))
            continue
        if command == "/policy":
            write_line(format_policy(context))
            continue
        if command == "/workspace":
            write_line(str(context.workspace))
            continue
        if command == "/audit":
            write_line(format_audit(context))
            continue
        if command == "/prompt-trace":
            write_line(format_prompt_trace(context))
            continue
        if command == "/prompt-tuner":
            write_line(format_prompt_tuner(context))
            continue
        if command == "/prompt-tuner-reset":
            reset_prompt_tuning_state(context)
            write_line("PromptTuner 已重置为基线状态。")
            continue
        if command == "/tickets":
            write_line(format_tickets(context))
            continue
        if command.startswith("/scan"):
            _scan_project(context, user_text[len("/scan"):].strip())
            continue
        if command.startswith("/diagnose"):
            _diagnose_project(context, user_text[len("/diagnose"):].strip())
            continue
        if command.startswith("/quality-gate"):
            _run_quality_gate(context, user_text[len("/quality-gate"):].strip())
            continue
        if command == "/quality-report":
            write_line(format_quality_gate(context))
            continue
        if command.startswith("/quality-save"):
            _export_quality_gate(context, user_text[len("/quality-save"):].strip())
            continue
        if command == "/quality-reset":
            context.runtime.reset_quality_gate()
            write_line("质量门裁决已清空。")
            continue
        if command == "/delivery":
            write_line(format_delivery(context))
            continue
        if command.startswith("/delivery-save"):
            _export_delivery(context, user_text[len("/delivery-save"):].strip())
            continue
        if command == "/delivery-reset":
            context.runtime.reset_delivery()
            write_line("交付 Manifest 已清空。")
            continue
        if command.startswith("/release"):
            _run_release(context, user_text[len("/release"):].strip())
            continue
        if command.startswith("/reflect"):
            _run_reflect(context, user_text[len("/reflect"):].strip())
            continue
        if command == "/experience":
            write_line(format_experience(context))
            continue
        if command.startswith("/experience-save"):
            _export_experience(context, user_text[len("/experience-save"):].strip())
            continue
        if command == "/experience-reset":
            context.runtime.reset_experience()
            write_line("经验沉淀候选报告已清空。")
            continue
        if command.startswith("/skill-queue-build"):
            _run_skill_queue_build(context, user_text[len("/skill-queue-build"):].strip())
            continue
        if command == "/skill-queue":
            write_line(format_skill_queue(context))
            continue
        if command.startswith("/skill-queue-save"):
            _export_skill_queue(context, user_text[len("/skill-queue-save"):].strip())
            continue
        if command == "/skill-queue-reset":
            context.runtime.reset_skill_queue()
            write_line("Skill 审阅队列已清空。")
            continue
        if command.startswith("/tool-request-build"):
            _run_tool_request_build(context, user_text[len("/tool-request-build"):].strip())
            continue
        if command == "/tool-request":
            write_line(format_tool_request(context))
            continue
        if command.startswith("/tool-request-save"):
            _export_tool_request(context, user_text[len("/tool-request-save"):].strip())
            continue
        if command == "/tool-request-reset":
            context.runtime.reset_tool_requests()
            write_line("Tool 生产请求队列已清空。")
            continue
        if command.startswith("/exoskeleton-build"):
            _run_exoskeleton_build(context, user_text[len("/exoskeleton-build"):].strip())
            continue
        if command == "/exoskeleton":
            write_line(format_exoskeleton(context))
            continue
        if command.startswith("/exoskeleton-save"):
            _export_exoskeleton(context, user_text[len("/exoskeleton-save"):].strip())
            continue
        if command == "/exoskeleton-reset":
            context.runtime.reset_exoskeleton()
            write_line("LLM 外骨骼压缩报告已清空。")
            continue
        if command.startswith("/shell-mount-build"):
            _run_shell_mount_build(context, user_text[len("/shell-mount-build"):].strip())
            continue
        if command == "/shell-mount":
            write_line(format_shell_mount(context))
            continue
        if command.startswith("/shell-mount-save"):
            _export_shell_mount(context, user_text[len("/shell-mount-save"):].strip())
            continue
        if command == "/shell-mount-reset":
            context.runtime.reset_shell_mount()
            write_line("十八系统壳装报告已清空。")
            continue
        if command.startswith("/repair-plan-build"):
            _run_project_repair_plan(context, user_text[len("/repair-plan-build"):].strip())
            continue
        if command == "/repair-plan":
            write_line(format_project_repair(context))
            continue
        if command.startswith("/repair-plan-save"):
            _export_project_repair(context, user_text[len("/repair-plan-save"):].strip())
            continue
        if command == "/repair-plan-reset":
            context.runtime.reset_project_repair()
            write_line("L6.25 工程修复计划已清空。")
            continue
        if command.startswith("/delivery-standard-build"):
            _run_delivery_standardization(context, user_text[len("/delivery-standard-build"):].strip())
            continue
        if command == "/delivery-standard":
            write_line(format_delivery_standardization(context))
            continue
        if command.startswith("/delivery-standard-save"):
            _export_delivery_standardization(context, user_text[len("/delivery-standard-save"):].strip())
            continue
        if command == "/delivery-standard-reset":
            context.runtime.reset_delivery_standardization()
            write_line("L6.26 标准化交付证据已清空。")
            continue
        if command.startswith("/provider-build"):
            _run_provider_adaptation(context, user_text[len("/provider-build"):].strip())
            continue
        if command == "/provider":
            write_line(format_provider_adaptation(context))
            continue
        if command.startswith("/provider-save"):
            _export_provider_adaptation(context, user_text[len("/provider-save"):].strip())
            continue
        if command == "/provider-reset":
            context.runtime.reset_provider_adaptation()
            write_line("L6.27 Provider 适配外壳报告已清空。")
            continue
        if command.startswith("/learning-converge-build"):
            _run_learning_convergence(context, user_text[len("/learning-converge-build"):].strip())
            continue
        if command == "/learning-converge":
            write_line(format_learning_convergence(context))
            continue
        if command.startswith("/learning-converge-save"):
            _export_learning_convergence(context, user_text[len("/learning-converge-save"):].strip())
            continue
        if command == "/learning-converge-reset":
            context.runtime.reset_learning_convergence()
            write_line("L6.28 执行合流报告已清空。")
            continue
        if command.startswith("/recovery-build"):
            _run_recovery_coordination(context, user_text[len("/recovery-build"):].strip())
            continue
        if command == "/recovery":
            write_line(format_recovery_coordination(context))
            continue
        if command.startswith("/recovery-save"):
            _export_recovery_coordination(context, user_text[len("/recovery-save"):].strip())
            continue
        if command == "/recovery-reset":
            context.runtime.reset_recovery_coordination()
            write_line("L6.29 恢复协调报告已清空。")
            continue
        if command.startswith("/governance-build"):
            _run_governance_execution(context, user_text[len("/governance-build"):].strip())
            continue
        if command == "/governance":
            write_line(format_governance_execution(context))
            continue
        if command.startswith("/governance-save"):
            _export_governance_execution(context, user_text[len("/governance-save"):].strip())
            continue
        if command == "/governance-reset":
            context.runtime.reset_governance_execution()
            write_line("L6.30 治理执行力化报告已清空。")
            continue
        if command.startswith("/planner-context-build"):
            _run_planner_context(context, user_text[len("/planner-context-build"):].strip())
            continue
        if command == "/planner-context":
            write_line(format_planner_context(context))
            continue
        if command.startswith("/planner-context-save"):
            _export_planner_context(context, user_text[len("/planner-context-save"):].strip())
            continue
        if command == "/planner-context-reset":
            context.runtime.reset_planner_context()
            write_line("L6.31 统一 Planner 上下文已清空。")
            continue
        if command.startswith("/planner-execute"):
            _run_planner_execution(context, user_text[len("/planner-execute"):].strip())
            continue
        if command == "/planner-execution":
            write_line(format_planner_execution(context))
            continue
        if command.startswith("/planner-execution-save"):
            _export_planner_execution(context, user_text[len("/planner-execution-save"):].strip())
            continue
        if command == "/planner-execution-reset":
            context.runtime.reset_planner_execution()
            write_line("L6.32 Planner 执行主链报告已清空。")
            continue
        if command == "/execution-chain-contract":
            write_line(format_execution_chain_contract(context))
            continue
        if command.startswith("/execution-chain-contract-save"):
            _export_execution_chain_contract(context, user_text[len("/execution-chain-contract-save"):].strip())
            continue
        if command == "/execution-chain-freeze":
            write_line(format_execution_chain_freeze(context))
            continue
        if command.startswith("/execution-chain-freeze-save"):
            _export_execution_chain_freeze(context, user_text[len("/execution-chain-freeze-save"):].strip())
            continue
        if command.startswith("/p0-system-build"):
            _run_p0_system_integration(context, user_text[len("/p0-system-build"):].strip())
            continue
        if command == "/p0-system":
            write_line(format_p0_system_integration(context))
            continue
        if command.startswith("/p0-system-save"):
            _export_p0_system_integration(context, user_text[len("/p0-system-save"):].strip())
            continue
        if command == "/p0-system-reset":
            context.runtime.reset_p0_system_integration()
            write_line("L6.38 P0 系统接入报告已清空。")
            continue
        if command.startswith("/p0-system2-build"):
            _run_p0_system_integration_two(context, user_text[len("/p0-system2-build"):].strip())
            continue
        if command == "/p0-system2":
            write_line(format_p0_system_integration_two(context))
            continue
        if command.startswith("/p0-system2-save"):
            _export_p0_system_integration_two(context, user_text[len("/p0-system2-save"):].strip())
            continue
        if command == "/p0-system2-reset":
            context.runtime.reset_p0_system_integration_two()
            write_line("L6.39 P0 系统接入二报告已清空。")
            continue
        if command == "/model-plan-replay":
            _run_model_plan_replay(context)
            continue
        if command.startswith("/repair-loop"):
            _repair_loop(context, user_text[len("/repair-loop"):].strip())
            continue
        if command == "/diagnosis":
            write_line(format_diagnosis(context))
            continue
        if command.startswith("/diagnosis-save"):
            _export_diagnosis(context, user_text[len("/diagnosis-save"):].strip())
            continue
        if command == "/diagnosis-reset":
            context.runtime.reset_diagnosis()
            write_line("工程诊断摘要已清空。")
            continue
        if command == "/project":
            write_line(format_project_index(context))
            continue
        if command.startswith("/project-save"):
            _export_project_index(context, user_text[len("/project-save"):].strip())
            continue
        if command == "/project-reset":
            context.runtime.reset_project_index()
            write_line("项目索引已清空。")
            continue
        if command == "/context":
            write_line(format_context_memory(context))
            continue
        if command.startswith("/context-save"):
            _export_context_memory(context, user_text[len("/context-save"):].strip())
            continue
        if command == "/context-reset":
            context.runtime.reset_context_memory()
            write_line("上下文摘要已清空。")
            continue
        if command.startswith("/confirm "):
            _confirm_ticket(context, user_text.split(maxsplit=1)[1].strip())
            continue
        if command.startswith("/deny "):
            _deny_ticket(context, user_text.split(maxsplit=1)[1].strip())
            continue
        if command.startswith("/audit-save"):
            _export_audit(context, user_text[len("/audit-save"):].strip())
            continue
        if command.startswith("/audit-replay"):
            _replay_audit(context, user_text[len("/audit-replay"):].strip())
            continue
        if command.startswith("/report"):
            _export_report(context, user_text[len("/report"):].strip())
            continue
        if command.startswith("/plan "):
            preview_runtime_plan(context, user_text[6:].strip())
            continue
        if command == "/reset":
            context.session.reset()
            write_line("当前会话已重置。")
            continue
        if command.startswith("/run "):
            run_runtime_task(context, user_text[5:].strip())
            continue
        run_once(context, user_text)
