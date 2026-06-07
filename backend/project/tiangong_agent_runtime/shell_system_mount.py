"""L6.24 十八系统壳装总线。

该模块只在 Runtime 外壳层把已装能力映射成 18 个系统挂载槽，供 LLM / Planner
理解“现在有什么、下一刀应该接哪里”。它不注册正式 Tool、Skill 或 Capability，
不释放工具句柄，不修改 tiangong_kernel。
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

SHELL_SYSTEM_MOUNT_SCHEMA = "tiangong.l6_24.shell_system_mount.v1"
SENSITIVE_PATTERN = re.compile(
    r"(?i)(api[_-]?key|authorization|bearer|token|secret|password|credential)\s*[:=]\s*[^\s,;]+"
)
SENSITIVE_WORDS = ("api_key", "apikey", "authorization", "bearer", "token", "secret", "password", "credential")


@dataclass(frozen=True)
class ShellSystemSpec:
    system_id: str
    name: str
    execution_role: str
    primary_modules: tuple[str, ...] = ()
    runtime_tools: tuple[str, ...] = ()
    existing_stage_refs: tuple[str, ...] = ()
    next_shell_action: str = "保持壳层只读挂载，等待后续执行增强。"
    priority: str = "P1"


SYSTEM_SPECS: tuple[ShellSystemSpec, ...] = (
    ShellSystemSpec(
        "S01",
        "上下文 / 会话 / 记忆连续性系统",
        "维持长链任务状态、最近执行摘要和下一轮 PlannerHint。",
        ("context_memory_bridge.py", "session_bridge.py"),
        (),
        ("L6.15",),
        "把执行摘要继续压成下一轮 Planner 可消费提示。",
        "P0",
    ),
    ShellSystemSpec(
        "S02",
        "项目感知与文件索引系统",
        "只读扫描工程结构，让 LLM 不盲改文件。",
        ("project_index_bridge.py", "adapters/project_scan_adapter.py"),
        ("scan_project",),
        ("L6.16",),
        "继续增强项目雷达索引与测试入口索引。",
        "P0",
    ),
    ShellSystemSpec(
        "S03",
        "工程修复执行系统",
        "把诊断、受控写入、质量检查合成可回滚修复链。",
        ("diagnostic_bridge.py", "adapters/workspace_write_adapter.py", "adapters/python_test_adapter.py"),
        ("diagnose_project", "write_workspace_file", "run_python_quality_check"),
        ("L6.17",),
        "后续接入 PatchPlan / PatchApplyResult，但仍走 Runtime 写入适配器。",
        "P0",
    ),
    ShellSystemSpec(
        "S04",
        "测试验证质量门系统",
        "测试、诊断和质量门裁决，质量门只卡正式发布/冻结。",
        ("quality_gate_bridge.py", "adapters/quality_gate_adapter.py", "adapters/python_test_adapter.py"),
        ("run_python_quality_check", "evaluate_quality_gate"),
        ("L6.18",),
        "维持执行力优先：不卡 A0-A4 草案，只卡正式发布与 A5。",
        "P0",
    ),
    ShellSystemSpec(
        "S05",
        "产品交付系统",
        "形成 Manifest、Release Gate、交付包和完整性摘要。",
        ("delivery_manifest.py", "delivery_standardization.py", "adapters/zip_package_adapter.py"),
        ("create_zip_package", "create_release_bundle", "build_delivery_standardization"),
        ("L6.19", "L6.26"),
        "继续标准化修改清单、测试证据、sha256 与 integrity。",
        "P0",
    ),
    ShellSystemSpec(
        "S06",
        "真实 Provider 适配系统",
        "模型调用必须经 Runtime 审计链和模型计划器，不允许插件裸调 SDK。",
        ("adapters/model_chat_adapter.py", "model_planner.py", "provider_adaptation_shell.py"),
        ("model_chat", "build_provider_adaptation"),
        ("L6.13", "L6.14", "L6.27"),
        "已接 ProviderProfile / CapabilityMatrix / API Surface / GovernanceMount 外壳；后续才进入真实 L4/L5 permit 执行链。",
        "P0",
    ),
    ShellSystemSpec(
        "S07",
        "插件建议接入系统",
        "插件只给计划/修复/质量/Handoff 建议，经 Runtime 转为受控计划。",
        ("plugin_suggestion_bridge.py", "suggestions.py"),
        (),
        ("L6.11",),
        "扩大建议类型，但继续禁止插件直接执行工具。",
        "P1",
    ),
    ShellSystemSpec(
        "S08",
        "治理权限系统",
        "风险分级、确认票据、PermitGateway 和 A5 硬阻断。",
        ("execution_policy.py", "permit_gateway.py", "risk_classifier.py", "confirmation_ticket.py", "governance_execution.py"),
        ("build_governance_execution",),
        ("L6.10", "L6.12", "L6.23", "L6.30"),
        "已接治理执行力化外壳：A0-A4 草案/分析/smoke/续接快车道，A5/裸密钥/越权路径硬拦。",
        "P0",
    ),
    ShellSystemSpec(
        "S09",
        "审计与公共投影系统",
        "记录审计事件、运行报告与可公开摘要，支撑复盘。",
        ("audit_bridge.py", "audit_replay.py", "public_projection_bridge.py", "runtime_report.py", "delivery_standardization.py", "governance_execution.py"),
        ("build_delivery_standardization", "build_governance_execution"),
        ("L6.10", "L6.12", "L6.13", "L6.26", "L6.30"),
        "后续将 18 系统挂载报告与标准化交付证据纳入公共投影摘要。",
        "P1",
    ),
    ShellSystemSpec(
        "S10",
        "自修复系统",
        "把失败信号转成诊断、修复顺序、回归建议。",
        ("diagnostic_bridge.py", "error_mapper.py", "recovery_coordination.py"),
        ("diagnose_project", "run_python_quality_check", "build_recovery_coordination"),
        ("L6.17", "L6.20", "L6.29"),
        "已接 FailureSignal → RepairCandidate 恢复协调外壳，不自动改内核。",
        "P1",
    ),
    ShellSystemSpec(
        "S11",
        "自学习 / 自迭代候选系统",
        "把成功、失败、用户修正沉淀为经验与候选。",
        ("experience_synthesis.py", "learning_convergence.py"),
        ("synthesize_experience_candidates", "build_learning_convergence"),
        ("L6.20", "L6.28"),
        "保证经验必须合流为 Planner 可直接消费的 ExecutionConsumptionCard，而不是只生成报告。",
        "P0",
    ),
    ShellSystemSpec(
        "S12",
        "Skill / 知识系统",
        "把 Skill 候选版本化，不注册、不激活、不写 Skill 注册表。",
        ("skill_review_queue.py", "learning_convergence.py"),
        ("queue_skill_candidates", "build_learning_convergence"),
        ("L6.21", "L6.28"),
        "已接 SkillDraftRoute / PlannerHintRoute 合流外壳；正式注册和激活仍被治理链隔离。",
        "P1",
    ),
    ShellSystemSpec(
        "S13",
        "多智能体 / Handoff 系统",
        "Handoff 建议、长链摘要和父链回收，不创建平行 Runtime。",
        ("long_chain_runner.py", "plugin_suggestion_bridge.py", "suggestions.py", "recovery_coordination.py"),
        ("build_recovery_coordination",),
        ("L6.11", "L6.29"),
        "已接 HandoffDigest 投影，但不得自动派生子智能体或成为第二运行时。",
        "P1",
    ),
    ShellSystemSpec(
        "S14",
        "预算与资源系统",
        "步骤预算、长链预算和资源压力降级。",
        ("budget_guard.py", "long_chain_runner.py", "recovery_coordination.py", "governance_execution.py"),
        ("build_recovery_coordination", "build_governance_execution"),
        ("L6.11", "L6.29", "L6.30"),
        "已接 BudgetUpdate 投影与治理执行力化外壳；真实预算变更仍由 Runtime 执行链控制。",
        "P1",
    ),
    ShellSystemSpec(
        "S15",
        "回滚 / 版本 / 热切换系统",
        "保持写入备份、交付完整性和候选可撤销，不做不可回滚激活。",
        ("adapters/workspace_write_adapter.py", "delivery_manifest.py", "delivery_standardization.py", "governance_execution.py"),
        ("write_workspace_file", "create_release_bundle", "build_delivery_standardization", "build_governance_execution"),
        ("L6.17", "L6.19", "L6.26", "L6.30"),
        "通过治理执行力化外壳区分草案快车道与正式发布/注册/激活护栏，仍不动 tiangong_kernel。",
        "P1",
    ),
    ShellSystemSpec(
        "S16",
        "情感 / 自由意志行为调制系统",
        "只提供行为优先级和节律提示，不提供授权、不绕过治理。",
        (),
        (),
        ("L6.phase3", "L6.phase4"),
        "当前只壳层预留；后续接入 BehaviorPriorityHint，六欲只影响行为侧。",
        "P2",
    ),
    ShellSystemSpec(
        "S17",
        "前端驾驶舱系统",
        "展示计划、工具、测试、产物、审计、预算和回滚入口。",
        ("public_projection_bridge.py", "runtime_report.py", "delivery_standardization.py"),
        ("build_delivery_standardization",),
        ("L6.13", "L6.26"),
        "当前由 CLI/公共投影承载；后续再接桌面端驾驶舱。",
        "P2",
    ),
    ShellSystemSpec(
        "S18",
        "安装 / 手册 / 三端产品化系统",
        "安装包、首启配置、API 配置页、手册与移动控制端。",
        ("delivery_manifest.py",),
        ("create_release_bundle",),
        ("L6.19",),
        "当前由交付链承载；后续接安装器和三端控制文档。",
        "P2",
    ),
)


@dataclass(frozen=True)
class ShellMountedSystem:
    system_id: str
    name: str
    status: str
    mount_mode: str
    execution_role: str
    installed_evidence: list[str] = field(default_factory=list)
    missing_evidence: list[str] = field(default_factory=list)
    runtime_tools: list[str] = field(default_factory=list)
    existing_stage_refs: list[str] = field(default_factory=list)
    next_shell_action: str = ""
    priority: str = "P1"
    shell_only: bool = True
    kernel_mutation_allowed: bool = False
    registers_formal_tool: bool = False
    releases_tool_handle: bool = False
    activates_skill: bool = False
    bypasses_runtime: bool = False

    def __post_init__(self) -> None:
        if not self.shell_only:
            raise ValueError("L6.24 shell mounted system must remain shell-only")
        if any((self.kernel_mutation_allowed, self.registers_formal_tool, self.releases_tool_handle, self.activates_skill, self.bypasses_runtime)):
            raise ValueError("L6.24 shell mount cannot mutate kernel/register/release/activate/bypass Runtime")

    def public_dict(self) -> dict[str, Any]:
        return {
            "system_id": self.system_id,
            "name": self.name,
            "status": self.status,
            "mount_mode": self.mount_mode,
            "execution_role": self.execution_role,
            "installed_evidence": list(self.installed_evidence),
            "missing_evidence": list(self.missing_evidence),
            "runtime_tools": list(self.runtime_tools),
            "existing_stage_refs": list(self.existing_stage_refs),
            "next_shell_action": self.next_shell_action,
            "priority": self.priority,
            "shell_only": self.shell_only,
            "kernel_mutation_allowed": self.kernel_mutation_allowed,
            "registers_formal_tool": self.registers_formal_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "activates_skill": self.activates_skill,
            "bypasses_runtime": self.bypasses_runtime,
        }


@dataclass(frozen=True)
class ShellSystemMountReport:
    schema: str
    generated_at: float
    status: str
    summary: str
    systems: list[ShellMountedSystem] = field(default_factory=list)
    notes_used: bool = False
    execution_first: bool = True
    shell_only: bool = True
    system_count: int = 18
    active_shell_systems: int = 0
    partial_shell_systems: int = 0
    reserved_shell_systems: int = 0
    kernel_pollution_guard: bool = True
    modifies_kernel: bool = False
    modifies_core_runtime: bool = False
    registers_formal_tool: bool = False
    releases_tool_handle: bool = False
    activates_skill: bool = False
    bypasses_governance: bool = False

    def __post_init__(self) -> None:
        if self.system_count != 18 or len(self.systems) != 18:
            raise ValueError("L6.24 shell system mount must expose exactly 18 system slots")
        if not (self.execution_first and self.shell_only and self.kernel_pollution_guard):
            raise ValueError("L6.24 shell system mount must remain execution-first, shell-only and kernel-guarded")
        forbidden = (
            self.modifies_kernel,
            self.modifies_core_runtime,
            self.registers_formal_tool,
            self.releases_tool_handle,
            self.activates_skill,
            self.bypasses_governance,
        )
        if any(forbidden):
            raise ValueError("L6.24 shell mount report cannot mutate kernel/core/register/release/activate/bypass governance")

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "generated_at": self.generated_at,
            "status": self.status,
            "summary": self.summary,
            "system_count": self.system_count,
            "active_shell_systems": self.active_shell_systems,
            "partial_shell_systems": self.partial_shell_systems,
            "reserved_shell_systems": self.reserved_shell_systems,
            "systems": [item.public_dict() for item in self.systems],
            "notes_used": self.notes_used,
            "execution_first": self.execution_first,
            "shell_only": self.shell_only,
            "kernel_pollution_guard": self.kernel_pollution_guard,
            "modifies_kernel": self.modifies_kernel,
            "modifies_core_runtime": self.modifies_core_runtime,
            "registers_formal_tool": self.registers_formal_tool,
            "releases_tool_handle": self.releases_tool_handle,
            "activates_skill": self.activates_skill,
            "bypasses_governance": self.bypasses_governance,
        }

    def summary_text(self) -> str:
        return (
            "L6.24 十八系统壳装："
            f"status={self.status}；systems={self.system_count}；"
            f"active={self.active_shell_systems}；partial={self.partial_shell_systems}；reserved={self.reserved_shell_systems}；"
            f"shell_only={self.shell_only}；kernel_pollution_guard={self.kernel_pollution_guard}。{self.summary}"
        )

    def markdown_report(self) -> str:
        lines = [
            "# 临渊者 L6.24 十八系统壳装报告",
            "",
            f"- schema: `{self.schema}`",
            f"- status: `{self.status}`",
            f"- system_count: `{self.system_count}`",
            f"- active_shell_systems: `{self.active_shell_systems}`",
            f"- partial_shell_systems: `{self.partial_shell_systems}`",
            f"- reserved_shell_systems: `{self.reserved_shell_systems}`",
            f"- shell_only: `{self.shell_only}`",
            f"- kernel_pollution_guard: `{self.kernel_pollution_guard}`",
            "",
            "## 摘要",
            "",
            self.summary,
            "",
            "## 18 系统挂载槽",
            "",
        ]
        for item in self.systems:
            lines.append(f"- `{item.system_id}` {item.name}：{item.status} / {item.mount_mode}；下一步：{item.next_shell_action}")
        lines.extend([
            "",
            "> L6.24 只做 Runtime 外壳系统挂载，不注册正式工具、不激活 Skill、不释放工具句柄、不修改 tiangong_kernel。",
        ])
        return "\n".join(lines)


class ShellSystemMountBridge:
    """Runtime 外壳层 18 系统挂载总线。"""

    def __init__(self) -> None:
        self._last_report: ShellSystemMountReport | None = None

    @property
    def last_report(self) -> ShellSystemMountReport | None:
        return self._last_report

    def reset(self) -> None:
        self._last_report = None

    def build(
        self,
        *,
        available_tools: Iterable[str] = (),
        available_modules: Iterable[str] = (),
        notes: str = "",
    ) -> ShellSystemMountReport:
        tools = set(str(item) for item in available_tools)
        modules = set(str(item) for item in available_modules)
        systems = [_mount_spec(spec, available_tools=tools, available_modules=modules) for spec in SYSTEM_SPECS]
        active = sum(1 for item in systems if item.status == "active_shell_mounted")
        partial = sum(1 for item in systems if item.status == "partial_shell_mounted")
        reserved = sum(1 for item in systems if item.status == "reserved_shell_slot")
        manual_note = _safe_text(notes, limit=360)
        summary = (
            "已根据当前 Runtime 已装模块和工具注册表生成 18 个外壳挂载槽；"
            "挂载结果只供 Planner/LLM 选择下一步执行路径，不改变正式注册链。"
        )
        if manual_note:
            summary += f" 用户备注：{manual_note}"
        status = "shell_mount_ready" if active + partial + reserved == 18 else "shell_mount_incomplete"
        report = ShellSystemMountReport(
            schema=SHELL_SYSTEM_MOUNT_SCHEMA,
            generated_at=time(),
            status=status,
            summary=summary,
            systems=systems,
            notes_used=bool(manual_note),
            active_shell_systems=active,
            partial_shell_systems=partial,
            reserved_shell_systems=reserved,
        )
        self._last_report = report
        return report

    def public_dict(self) -> dict[str, Any]:
        if self._last_report is None:
            return {
                "schema": SHELL_SYSTEM_MOUNT_SCHEMA,
                "status": "empty",
                "message": "暂无 L6.24 十八系统壳装报告，请先执行 /shell-mount-build。",
            }
        return self._last_report.public_dict()

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(self.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return target

    def build_planner_hint(self) -> str:
        if self._last_report is None:
            return ""
        active_names = ", ".join(item.system_id for item in self._last_report.systems if item.status == "active_shell_mounted")
        return (
            "最近 L6.24 十八系统壳装："
            f"active={self._last_report.active_shell_systems}; partial={self._last_report.partial_shell_systems}; "
            f"reserved={self._last_report.reserved_shell_systems}; active_slots={active_names}; "
            "shell_only=True; kernel_pollution_guard=True; formal_activation_gated=True"
        )[:1200]



def build_shell_system_mount_adapter(shell_mount: ShellSystemMountBridge, state_provider: Any):
    def shell_system_mount_adapter(invocation: ToolInvocation, context: TurnContext) -> ToolResult:
        try:
            state = state_provider()
            report = shell_mount.build(
                available_tools=state.get("available_tools", []),
                available_modules=state.get("available_modules", []),
                notes=str(invocation.arguments.get("notes") or invocation.arguments.get("manual_notes") or ""),
            )
        except (TypeError, ValueError) as exc:
            return ToolResult(
                invocation.step_id,
                invocation.tool_name,
                ToolResultStatus.FAILED,
                f"十八系统壳装失败：{exc}",
                error_code="shell_system_mount_failed",
            )
        return ToolResult(
            step_id=invocation.step_id,
            tool_name=invocation.tool_name,
            status=ToolResultStatus.OK,
            output_summary=report.summary_text(),
            data=report.public_dict(),
        )

    return shell_system_mount_adapter



def discover_runtime_module_files(runtime_root: str | Path | None = None) -> list[str]:
    root = Path(runtime_root) if runtime_root else Path(__file__).resolve().parent
    if not root.exists():
        return []
    files: list[str] = []
    for path in root.rglob("*.py"):
        try:
            files.append(str(path.relative_to(root)).replace("\\", "/"))
        except ValueError:
            files.append(path.name)
    return sorted(files)



def _mount_spec(spec: ShellSystemSpec, *, available_tools: set[str], available_modules: set[str]) -> ShellMountedSystem:
    module_hits = [module for module in spec.primary_modules if module in available_modules]
    tool_hits = [tool for tool in spec.runtime_tools if tool in available_tools]
    missing_modules = [module for module in spec.primary_modules if module not in available_modules]
    missing_tools = [tool for tool in spec.runtime_tools if tool not in available_tools]
    evidence = [f"module:{item}" for item in module_hits] + [f"tool:{item}" for item in tool_hits]
    missing = [f"module:{item}" for item in missing_modules] + [f"tool:{item}" for item in missing_tools]

    if evidence and not missing:
        status = "active_shell_mounted"
        mount_mode = "existing_runtime_bridge"
    elif evidence:
        status = "partial_shell_mounted"
        mount_mode = "existing_bridge_plus_reserved_shell_slot"
    else:
        status = "reserved_shell_slot"
        mount_mode = "reserved_shell_only"

    return ShellMountedSystem(
        system_id=spec.system_id,
        name=spec.name,
        status=status,
        mount_mode=mount_mode,
        execution_role=spec.execution_role,
        installed_evidence=evidence,
        missing_evidence=missing,
        runtime_tools=list(spec.runtime_tools),
        existing_stage_refs=list(spec.existing_stage_refs),
        next_shell_action=spec.next_shell_action,
        priority=spec.priority,
    )



def _safe_text(value: Any, *, limit: int = 700) -> str:
    text = redact_text(str(value or ""))
    text = SENSITIVE_PATTERN.sub(lambda m: f"{m.group(1)}=<redacted>", text)
    for word in SENSITIVE_WORDS:
        text = re.sub(re.escape(word), f"{word[:2]}***", text, flags=re.IGNORECASE)
    return text.strip()[:limit]



def stable_mount_digest(report: ShellSystemMountReport) -> str:
    material = json.dumps(report.public_dict(), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
