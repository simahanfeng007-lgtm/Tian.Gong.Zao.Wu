"""最小计划桥：把显式文本任务转成受控工具计划。"""

from __future__ import annotations

import shlex

from .tool_invocation import ToolInvocation


class PlanBridge:
    """第一版只做可审计的显式/半显式计划，不做自由工具执行。"""

    def build_plan(self, user_message: str) -> list[ToolInvocation]:
        text = user_message.strip()
        if not text:
            return []

        segments = _split_chain(text)
        if len(segments) > 1:
            plan: list[ToolInvocation] = []
            for segment in segments:
                plan.extend(self.build_plan(segment))
            return plan

        lowered = text.lower()

        # 显式工具 JSON/DSL 以后再扩展；当前支持 CLI 风格短命令与 && / 换行多步骤链。
        if (
            lowered.startswith("p0-system2-build")
            or lowered.startswith("p0-system-two-build")
            or lowered.startswith("l6.39")
            or lowered.startswith("l6_39")
            or lowered.startswith("p0 接入二")
            or lowered.startswith("p0系统接入二")
            or lowered.startswith("p0 系统接入二")
            or "memory / audit / recovery / qualitygate" in lowered
            or "memory/audit/recovery/qualitygate" in lowered
            or ("memory" in lowered and "audit" in lowered and "recovery" in lowered and ("qualitygate" in lowered or "quality gate" in lowered or "质量门" in lowered))
            or ("记忆" in lowered and "审计" in lowered and "恢复" in lowered and "质量门" in lowered)
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": 8, "step_budget": 10}),
                ToolInvocation("build_l6_39_memory_integration", {"notes": notes, "max_items": 8}),
                ToolInvocation("build_l6_39_audit_integration", {"notes": notes, "max_events": 24}),
                ToolInvocation("build_l6_39_recovery_integration", {"notes": notes, "max_items": 8}),
                ToolInvocation("build_l6_39_quality_gate_integration", {"notes": notes}),
                ToolInvocation("build_l6_39_p0_integration", {"notes": notes}),
            ]
        if (
            lowered.startswith("p0-system-build")
            or lowered.startswith("l6.38")
            or lowered.startswith("l6_38")
            or lowered.startswith("p0 接入")
            or lowered.startswith("p0系统接入")
            or lowered.startswith("p0 系统接入")
            or "provider / budget / skill / handoff" in lowered
            or "provider/budget/skill/handoff" in lowered
            or ("provider" in lowered and "budget" in lowered and "skill" in lowered and "handoff" in lowered)
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("build_provider_adaptation", {"path": ".", "notes": notes}),
                ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 8}),
                ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 8}),
                ToolInvocation("build_l6_38_provider_integration", {"notes": notes, "requested_call_mode": "dry_run"}),
                ToolInvocation("build_l6_38_budget_snapshot", {"notes": notes, "max_steps": 10, "planned_steps": 4}),
                ToolInvocation("build_l6_38_skill_integration", {"notes": notes, "max_items": 8}),
                ToolInvocation("build_l6_38_handoff_integration", {"notes": notes, "max_subtasks": 3}),
                ToolInvocation("build_l6_38_p0_integration", {"notes": notes}),
            ]
        if (
            lowered.startswith("planner-context")
            or lowered.startswith("planner context")
            or lowered.startswith("planner-context-build")
            or lowered.startswith("统一 planner")
            or lowered.startswith("统一planner")
            or lowered.startswith("planner 接入")
            or lowered.startswith("l6.31")
            or "unifiedplannercontext" in lowered
            or "统一 planner" in lowered
            or "统一planner" in lowered
            or ("planner" in lowered and ("接入" in lowered or "收口" in lowered or "上下文" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("build_shell_system_mount", {"notes": notes}),
                ToolInvocation("build_learning_convergence", {"notes": notes, "max_items": 16}),
                ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": 16, "step_budget": 20}),
                ToolInvocation("build_delivery_standardization", {"path": ".", "notes": notes}),
                ToolInvocation("build_provider_adaptation", {"path": ".", "notes": notes}),
                ToolInvocation("build_governance_execution", {"notes": notes, "max_items": 16}),
                ToolInvocation("build_planner_context", {"notes": notes, "max_items": 16, "task_id": "l6_31_unified_planner"}),
            ]

        if lowered.startswith("scan ") or lowered in {"scan", "扫描项目", "项目扫描", "inspect project", "project scan"}:
            path = _tail(text, default=".")
            return [ToolInvocation("scan_project", {"path": path})]
        if lowered.startswith("diagnose ") or lowered in {"diagnose", "诊断", "工程诊断", "诊断项目", "project diagnose"}:
            path = _tail(text, default=".")
            return [ToolInvocation("scan_project", {"path": path}), ToolInvocation("diagnose_project", {"path": path})]
        if (
            lowered.startswith("governance-build")
            or lowered.startswith("governance")
            or lowered.startswith("governance-execution")
            or lowered.startswith("治理执行力化")
            or lowered.startswith("治理护栏")
            or lowered.startswith("l6.30")
            or "治理执行力化" in lowered
            or "a0-a4" in lowered and "a5" in lowered
            or ("治理" in lowered and ("执行力" in lowered or "护栏" in lowered or "快车道" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": 12, "step_budget": 20}),
                ToolInvocation("build_governance_execution", {"notes": notes, "max_items": 12}),
            ]

        if (
            lowered.startswith("recovery-build")
            or lowered.startswith("recovery")
            or lowered.startswith("long-chain-recovery")
            or lowered.startswith("自修复联动")
            or lowered.startswith("恢复协调")
            or lowered.startswith("l6.29")
            or "自修复 + 多智能体 + 预算" in lowered
            or "恢复协调" in lowered
            or ("自修复" in lowered and ("多智能体" in lowered or "预算" in lowered or "续接" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("build_learning_convergence", {"notes": notes, "max_items": 12}),
                ToolInvocation("build_recovery_coordination", {"notes": notes, "max_items": 12, "step_budget": 20}),
            ]

        if (
            lowered.startswith("learning-converge")
            or lowered.startswith("learning convergence")
            or lowered.startswith("经验合流")
            or lowered.startswith("学习合流")
            or lowered.startswith("skill-tool-converge")
            or lowered.startswith("l6.28")
            or "经验 / skill / tool" in lowered
            or "经验 skill tool" in lowered
            or "skill/tool 合流" in lowered
            or "执行合流" in lowered
            or ("合流" in lowered and ("经验" in lowered or "skill" in lowered or "tool" in lowered or "工具" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 18}),
                ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 18}),
                ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 18}),
                ToolInvocation("build_execution_exoskeleton", {"notes": notes, "max_items": 18}),
                ToolInvocation("build_learning_convergence", {"notes": notes, "max_items": 18}),
            ]

        if (
            lowered.startswith("provider-build")
            or lowered.startswith("provider")
            or lowered.startswith("model-provider")
            or lowered.startswith("模型provider")
            or lowered.startswith("模型 provider")
            or lowered.startswith("provider适配")
            or lowered.startswith("l6.27")
            or "provider 适配" in lowered
            or "provider适配" in lowered
            or "真实 provider" in lowered
        ):
            path = _tail(text, default=".")
            return [ToolInvocation("build_provider_adaptation", {"path": path, "notes": text})]

        if (
            lowered.startswith("delivery-standard")
            or lowered.startswith("delivery standard")
            or lowered.startswith("交付链标准化")
            or lowered.startswith("标准化交付")
            or lowered.startswith("标准交付链")
            or lowered.startswith("l6.26")
            or "交付链标准化" in lowered
        ):
            path = _tail(text, default=".")
            return [ToolInvocation("build_delivery_standardization", {"path": path, "notes": text})]

        if (
            lowered.startswith("repair-plan")
            or lowered.startswith("project-repair")
            or lowered.startswith("工程修复计划")
            or lowered.startswith("项目修复计划")
            or lowered.startswith("l6.25")
            or "patchplan" in lowered
            or "工程修复外壳" in lowered
        ):
            path = _tail(text, default=".")
            return [
                ToolInvocation("scan_project", {"path": path}),
                ToolInvocation("run_python_quality_check", {"command": "compileall", "target": path}),
                ToolInvocation("diagnose_project", {"path": path}),
                ToolInvocation("build_project_repair_plan", {"path": path, "notes": text, "max_targets": 12}),
            ]

        if lowered.startswith("repair-loop") or lowered.startswith("repair loop") or "修复循环" in lowered:
            path = _tail(text, default=".") if lowered.startswith("repair") else "."
            return [
                ToolInvocation("scan_project", {"path": path}),
                ToolInvocation("run_python_quality_check", {"command": "compileall", "target": path}),
                ToolInvocation("run_python_quality_check", {"command": "pytest", "target": path}),
                ToolInvocation("diagnose_project", {"path": path}),
                ToolInvocation("write_workspace_file", {"path": "reports/l6_17_repair_loop_note.md", "content": "# L6.17 修复循环记录\n\n请查看 Runtime 运行报告和诊断摘要。\n"}),
            ]
        if lowered.startswith("list ") or lowered in {"list", "ls", "列目录", "列出目录"}:
            path = _tail(text, default=".")
            return [ToolInvocation("list_dir", {"path": path})]
        if lowered.startswith("ls "):
            path = _tail(text, default=".")
            return [ToolInvocation("list_dir", {"path": path})]
        if lowered.startswith("read ") or lowered.startswith("cat ") or lowered.startswith("读取 "):
            path = _tail(text, default="")
            return [ToolInvocation("read_file", {"path": path})]
        if lowered.startswith("write ") or lowered.startswith("写入 "):
            return _parse_write(text)
        if lowered.startswith("compileall") or lowered.startswith("python -m compileall") or "跑 compileall" in lowered:
            target = _tail(text, default=".") if lowered.startswith("compileall") else "."
            return [ToolInvocation("run_python_quality_check", {"command": "compileall", "target": target})]
        if lowered.startswith("pytest") or lowered.startswith("python -m pytest") or "跑 pytest" in lowered:
            target = _tail(text, default=".") if lowered.startswith("pytest") else "."
            return [ToolInvocation("run_python_quality_check", {"command": "pytest", "target": target})]
        if lowered.startswith("zip ") or lowered.startswith("打包 "):
            parts = shlex.split(text)
            source = parts[1] if len(parts) >= 2 else "."
            target = parts[2] if len(parts) >= 3 else "dist/tiangong_delivery.zip"
            return [ToolInvocation("create_zip_package", {"source": source, "target": target})]
        if lowered.startswith("release ") or lowered.startswith("发布 "):
            parts = shlex.split(text)
            target = parts[1] if len(parts) >= 2 else "dist/l6_19_release_bundle.zip"
            source = parts[2] if len(parts) >= 3 else "."
            return [ToolInvocation("create_release_bundle", {"source": source, "target": target})]
        if (
            lowered.startswith("shell-mount")
            or lowered.startswith("shell mount")
            or lowered.startswith("系统壳装")
            or lowered.startswith("壳装系统")
            or lowered.startswith("十八系统")
            or lowered.startswith("18系统")
            or "壳装" in lowered
            or "十八系统" in lowered
            or "18 个系统" in lowered
            or "18个系统" in lowered
        ):
            notes = _tail(text, default="")
            return [ToolInvocation("build_shell_system_mount", {"notes": notes})]

        if (
            lowered.startswith("exoskeleton")
            or lowered.startswith("外骨骼")
            or lowered.startswith("执行外骨骼")
            or lowered.startswith("llm外骨骼")
            or lowered.startswith("llm 外骨骼")
            or "外骨骼" in lowered
            or "执行力压缩" in lowered
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 12}),
                ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 12}),
                ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 12}),
                ToolInvocation("build_execution_exoskeleton", {"notes": notes, "max_items": 12}),
            ]
        if (
            lowered.startswith("tool-request")
            or lowered.startswith("tool request")
            or lowered.startswith("工具生产请求")
            or lowered.startswith("工具请求")
            or lowered.startswith("工具缺口入队")
            or ("工具" in lowered and ("生产请求" in lowered or "沙箱" in lowered or "验证前置" in lowered or "缺口入队" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 20}),
                ToolInvocation("queue_tool_production_requests", {"notes": notes, "max_items": 20}),
            ]
        if (
            lowered.startswith("skill-queue")
            or lowered.startswith("技能候选入队")
            or lowered.startswith("技能版本化")
            or lowered.startswith("skill review")
            or ("技能" in lowered and ("审阅队列" in lowered or "入队" in lowered or "版本化" in lowered))
        ):
            notes = _tail(text, default="")
            return [
                ToolInvocation("synthesize_experience_candidates", {"notes": notes, "max_candidates": 20}),
                ToolInvocation("queue_skill_candidates", {"notes": notes, "max_items": 20}),
            ]
        if (
            lowered.startswith("reflect ")
            or lowered.startswith("experience ")
            or lowered.startswith("沉淀经验")
            or lowered.startswith("经验沉淀")
            or "总结经验" in lowered
            or "转化成技能" in lowered
            or "转化成工具" in lowered
        ):
            notes = _tail(text, default="")
            if lowered.startswith("沉淀经验") or lowered.startswith("经验沉淀"):
                notes = text.split(maxsplit=1)[1] if len(text.split(maxsplit=1)) > 1 else ""
            return [ToolInvocation("synthesize_experience_candidates", {"notes": notes})]
        return []


def _tail(text: str, default: str = "") -> str:
    try:
        parts = shlex.split(text)
    except ValueError:
        parts = text.split(maxsplit=1)
    return parts[1] if len(parts) >= 2 else default


def _parse_write(text: str) -> list[ToolInvocation]:
    # 格式：write path :: content
    if "::" not in text:
        return []
    left, content = text.split("::", 1)
    parts = shlex.split(left)
    if len(parts) < 2:
        return []
    return [ToolInvocation("write_workspace_file", {"path": parts[1], "content": content.lstrip()})]



def _split_chain(text: str) -> list[str]:
    """按安全的轻量分隔符拆分多步骤任务。

    支持换行和 `&&`。`;` 暂不作为默认分隔符，避免中文正文或 Windows 路径误切。
    """
    normalized = text.replace("\r\n", "\n")
    pieces: list[str] = []
    for line in normalized.split("\n"):
        for part in line.split(" && "):
            item = part.strip()
            if item:
                pieces.append(item)
    return pieces
