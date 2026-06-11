"""L6.72.56 ContextWindowManager + L6.72.57 playbook pack 接线。"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Iterable

from .context_pack_schema import ContextPack, ContextWindowBundle, json_safe, safe_text

_TOOL_USAGE_CARDS: dict[str, str] = {
    "list_dir": "列出工作区内目录。args: {path}。只读。",
    "read_file": "读取工作区内普通文件摘要。args: {path}。只读，不读凭证文件。",
    "file_sha256": "Calculate SHA256 for a workspace file. args: {path}. read-only.",
    "write_workspace_file": "在工作区内创建/写入文件。args: {path, content}。写后需验证。",
    "run_python_quality_check": "运行受控 Python 质量检查。args: {command, target}，仅允许 compileall/pytest。",
    "scan_project": "只读扫描项目结构，生成索引摘要。args: {path,max_depth,max_files}。",
    "diagnose_project": "基于项目索引和质量结果生成诊断摘要。args: {path}。",
    "document_parse": "解析明确文档任务中的 docx/pdf/txt/md 等。args: {path,max_chars}。",
    "document_query": "对已解析文档追问。args: {query,path/document_id}。",
    "document_rewrite_plan": "生成文档改写计划，不直接写。args: {instruction,path}。",
    "document_apply_rewrite": "按计划写回文档/文本，需备份/回滚。args: {path,old_text,new_text/content}。",
    "document_export": "导出文档摘要/引用/查询结果。args: {path,target,format}。",
    "document_rollback": "按 operation_id/manifest 回滚文档写回。",
    "create_zip_package": "打包工作区内交付物。args: {source,target}。",
    "create_release_bundle": "生成标准 release bundle 和 manifest。",
    "build_delivery_standardization": "生成交付标准化证据，不改内核。",
    "return_analysis": "返回分析摘要，不执行外部动作。args: {content}。",
    "return_code": "返回代码文本，不直接写盘。args: {content,language}。",
}

_FAMILY_TOOL_PREFIXES: dict[str, tuple[str, ...]] = {
    "file": ("list_dir", "read_file", "file_sha256", "write_workspace_file"),
    "document": ("document_",),
    "code": ("scan_project", "diagnose_project", "run_python_quality_check", "code_x_"),
    "terminal": ("run_python_quality_check",),
    "delivery": ("create_zip_package", "create_release_bundle", "build_delivery_"),
    "quality": ("run_python_quality_check", "evaluate_quality_gate"),
    "analysis": ("return_analysis", "return_code", "diagnose_project"),
    "web": ("web_", "search_"),
}


@dataclass(frozen=True)
class ContextWindowDecision:
    model_tier: str
    include_packs: tuple[str, ...]
    tool_limit: int
    pack_char_limit: int
    notes: tuple[str, ...]

    def public_dict(self) -> dict[str, Any]:
        return {
            "model_tier": self.model_tier,
            "include_packs": list(self.include_packs),
            "tool_limit": self.tool_limit,
            "pack_char_limit": self.pack_char_limit,
            "notes": list(self.notes),
        }


class ContextWindowManager:
    def classify_tier(self, model_profile: Any | None, model_policy: Any | None = None) -> str:
        role = str(getattr(model_policy, "model_role", "") or getattr(model_profile, "recommended_role", "") or "main_brain_guarded")
        if role == "main_brain_full":
            return "S"
        if role == "main_brain_guarded":
            return "A"
        if role == "micro_planner":
            return "B"
        if role == "subagent_only":
            return "C"
        if role == "disabled":
            return "D"
        planner = float(getattr(model_profile, "planner_strength", 0.5) or 0.5)
        json_rel = float(getattr(model_profile, "json_reliability", 0.5) or 0.5)
        return "B" if planner < 0.58 or json_rel < 0.58 else "A"

    def decision_for(self, model_profile: Any | None, model_policy: Any | None = None, *, stage: str = "planning") -> ContextWindowDecision:
        tier = self.classify_tier(model_profile, model_policy)
        role = str(getattr(model_policy, "model_role", "") or getattr(model_profile, "recommended_role", "") or "main_brain_guarded")
        max_chars = int(getattr(model_policy, "max_context_chars", 8000) or 8000)
        notes = [f"role={role}", f"stage={safe_text(stage, 40)}"]
        if tier == "S":
            return ContextWindowDecision("S", ("MissionPack", "StatePack", "EvidencePack", "ErrorPack", "ToolPack", "PlaybookPack", "ConstraintPack"), 24, max(7000, min(max_chars, 18000)), tuple(notes + ["full_main_brain_context"]))
        if tier == "A":
            return ContextWindowDecision("A", ("MissionPack", "StatePack", "EvidencePack", "ErrorPack", "ToolPack", "PlaybookPack", "ConstraintPack"), 12, max(4200, min(max_chars, 9000)), tuple(notes + ["guarded_main_brain_trimmed_context"]))
        if tier == "B":
            return ContextWindowDecision("B", ("MissionPack", "StatePack", "ErrorPack", "ToolPack", "ConstraintPack"), 5, max(1600, min(max_chars, 3200)), tuple(notes + ["micro_planner_short_context"]))
        if tier == "C":
            return ContextWindowDecision("C", ("MissionPack", "ConstraintPack"), 1, 1200, tuple(notes + ["subagent_only_single_task_context"]))
        return ContextWindowDecision("D", ("MissionPack", "ConstraintPack"), 0, 800, tuple(notes + ["disabled_model_no_work_context"]))

    def build_context_pack(
        self,
        *,
        user_goal: str,
        model_profile: Any | None = None,
        model_policy: Any | None = None,
        task_state: Any | None = None,
        stage: str = "planning",
        activation_form: Any | None = None,
        current_plan: Iterable[Any] | None = None,
        recent_results: Iterable[Any] | None = None,
        planner_failure: Any | None = None,
        available_tools: Iterable[Any] | None = None,
        playbook_route: Any | None = None,
        playbook_hint: str = "",
        external_context_hint: str = "",
        context_overflow_recovered: bool = False,
    ) -> ContextWindowBundle:
        decision = self.decision_for(model_profile, model_policy, stage=stage)
        all_packs = {
            "MissionPack": self._mission_pack(user_goal, task_state, stage, activation_form, decision),
            "StatePack": self._state_pack(task_state, current_plan, stage, decision),
            "EvidencePack": self._evidence_pack(task_state, recent_results, decision),
            "ErrorPack": self._error_pack(task_state, recent_results, planner_failure, decision),
            "ToolPack": self._tool_pack(model_policy, available_tools, decision, playbook_route),
            "PlaybookPack": self._playbook_pack(user_goal, activation_form, task_state, playbook_hint, decision, playbook_route),
            "ConstraintPack": self._constraint_pack(model_profile, model_policy, external_context_hint, decision, playbook_route),
        }
        selected = tuple(all_packs[name] for name in decision.include_packs if name in all_packs)
        budget = {
            "decision": decision.public_dict(),
            "model_context_window_estimate": int(getattr(model_profile, "context_window_estimate", 0) or 0),
            "policy_max_context_chars": int(getattr(model_policy, "max_context_chars", decision.pack_char_limit) or decision.pack_char_limit),
            "tool_limit": decision.tool_limit,
            "pack_char_limit": decision.pack_char_limit,
            "playbook_id": safe_text(getattr(playbook_route, "playbook_id", ""), 120),
            "summary_only": True,
        }
        return ContextWindowBundle(
            model_tier=decision.model_tier,
            model_role=str(getattr(model_policy, "model_role", "") or getattr(model_profile, "recommended_role", "") or "main_brain_guarded"),
            stage=safe_text(stage, 60),
            max_context_chars=decision.pack_char_limit,
            packs=selected,
            budget=budget,
            context_overflow_recovered=context_overflow_recovered,
            notes=decision.notes,
        )

    def build_activation_context_pack(self, **kwargs: Any) -> ContextWindowBundle:
        bundle = self.build_context_pack(stage="activation", **kwargs)
        keep = [pack for pack in bundle.packs if pack.name in {"MissionPack", "StatePack", "ConstraintPack"}]
        return ContextWindowBundle(
            model_tier=bundle.model_tier,
            model_role=bundle.model_role,
            stage="activation",
            max_context_chars=min(1400, bundle.max_context_chars),
            packs=tuple(ContextPack(pack.name, pack.title + " / activation_short", pack.priority, pack.payload, max_chars=min(pack.max_chars, 500)) for pack in keep),
            budget={**bundle.budget, "activation_short": True},
            notes=tuple(list(bundle.notes) + ["activation_form_short_context"]),
        )

    def _mission_pack(self, user_goal: str, task_state: Any | None, stage: str, activation_form: Any | None, decision: ContextWindowDecision) -> ContextPack:
        payload = {
            "user_goal": safe_text(user_goal, 700 if decision.model_tier in {"S", "A"} else 360),
            "current_stage": safe_text(stage, 80),
            "completion_standard": "真实执行、可验证、失败可续接；不得假装完成。",
            "task_id": safe_text(getattr(task_state, "task_id", ""), 120),
        }
        if activation_form is not None:
            payload["activation_form_summary"] = self._activation_summary(activation_form)
        return ContextPack("MissionPack", "用户目标 / 当前阶段 / 完成标准", 10, payload, max_chars=900 if decision.model_tier in {"S", "A"} else 420)

    def _state_pack(self, task_state: Any | None, current_plan: Iterable[Any] | None, stage: str, decision: ContextWindowDecision) -> ContextPack:
        executed = list(getattr(task_state, "executed_steps", []) or []) if task_state is not None else []
        unresolved = list(getattr(task_state, "unresolved_failures", []) or []) if task_state is not None else []
        plan = list(current_plan or getattr(task_state, "current_plan", []) or []) if task_state is not None or current_plan is not None else []
        payload = {
            "status": safe_text(getattr(task_state, "status", "created") if task_state is not None else "created", 80),
            "phase": safe_text(getattr(task_state, "current_phase", stage) if task_state is not None else stage, 100),
            "next_action": safe_text(getattr(task_state, "next_action", "build_or_execute_plan") if task_state is not None else "build_or_execute_plan", 200),
            "completed_step_count": len(executed),
            "pending_plan_step_count": len(plan),
            "unresolved_failure_count": len(unresolved),
        }
        if executed:
            payload["recent_completed"] = json_safe(executed[-5:], string_limit=260)
        if unresolved:
            payload["recent_unresolved_failures"] = json_safe(unresolved[-3:], string_limit=260)
        return ContextPack("StatePack", "任务状态 / 进度 / 下一步", 20, payload, max_chars=1200 if decision.model_tier in {"S", "A"} else 520)

    def _evidence_pack(self, task_state: Any | None, recent_results: Iterable[Any] | None, decision: ContextWindowDecision) -> ContextPack:
        evidence_refs = list(getattr(task_state, "evidence_refs", []) or []) if task_state is not None else []
        audit_refs = list(getattr(task_state, "audit_refs", []) or []) if task_state is not None else []
        artifacts = list(getattr(task_state, "artifact_refs", []) or []) if task_state is not None else []
        results = [self._result_summary(item) for item in list(recent_results or [])[-6:]]
        payload = {
            "recent_tool_result_summaries": results,
            "evidence_refs": json_safe(evidence_refs[-8:], string_limit=240),
            "audit_refs": json_safe(audit_refs[-8:], string_limit=160),
            "artifact_refs": json_safe(artifacts[-8:], string_limit=220),
            "body_policy": "只给路径/hash/摘要/引用，不给完整敏感文件正文。",
        }
        return ContextPack("EvidencePack", "最近证据 / 工具结果摘要 / 引用", 30, payload, max_chars=1700 if decision.model_tier == "S" else 900)

    def _error_pack(self, task_state: Any | None, recent_results: Iterable[Any] | None, planner_failure: Any | None, decision: ContextWindowDecision) -> ContextPack:
        failures = []
        for result in list(recent_results or [])[-8:]:
            if not bool(getattr(result, "ok", False)):
                failures.append(self._result_summary(result))
        unresolved = list(getattr(task_state, "unresolved_failures", []) or []) if task_state is not None else []
        payload = {
            "failure_type": safe_text(getattr(planner_failure, "failure_kind", "") or ("tool_or_validation_failed" if failures or unresolved else ""), 100),
            "planner_failure": json_safe(planner_failure, string_limit=300) if planner_failure is not None else None,
            "recent_failures": failures[-4:],
            "task_unresolved_failures": json_safe(unresolved[-4:], string_limit=260),
            "retry_budget": json_safe(getattr(task_state, "retry_budget", {}) if task_state is not None else {}, string_limit=180),
        }
        return ContextPack("ErrorPack", "失败摘要 / retry 状态 / 修复入口", 40, payload, max_chars=1300 if decision.model_tier in {"S", "A"} else 520)

    def _tool_pack(self, model_policy: Any | None, available_tools: Iterable[Any] | None, decision: ContextWindowDecision, playbook_route: Any | None = None) -> ContextPack:
        allowed_families = tuple(getattr(model_policy, "allowed_tool_families", ()) or ())
        preferred = tuple(getattr(playbook_route, "recommended_tools", ()) or ())
        forbidden = set(getattr(playbook_route, "forbidden_tools", ()) or ())
        candidates = self._candidate_tools(available_tools, allowed_families, decision.tool_limit, preferred=preferred, forbidden=forbidden)
        payload = {
            "tool_limit": decision.tool_limit,
            "allowed_families": list(allowed_families),
            "playbook_recommended_tools": list(preferred),
            "playbook_forbidden_tools": list(forbidden),
            "candidate_tools": candidates,
            "tool_policy": "LLM 只生成计划；真实工具调用由 Runtime / ExecutionSpine / QualityGate 执行。",
        }
        return ContextPack("ToolPack", "本轮候选工具 usage cards", 50, payload, max_chars=1500 if decision.model_tier in {"S", "A"} else 650)

    def _playbook_pack(self, user_goal: str, activation_form: Any | None, task_state: Any | None, playbook_hint: str, decision: ContextWindowDecision, playbook_route: Any | None = None) -> ContextPack:
        if playbook_route is not None and hasattr(playbook_route, "public_dict"):
            payload = playbook_route.public_dict()
        else:
            work_type = self._activation_summary(activation_form).get("work_type") if activation_form is not None else "mixed"
            payload = {
                "playbook_id": self._default_playbook_id(str(work_type), user_goal),
                "phase_sequence": self._default_phase_sequence(str(work_type), user_goal),
                "current_phase": safe_text(getattr(task_state, "current_phase", "intake") if task_state is not None else "intake", 120),
                "verification_policy": "阶段结束必须有可验证工具结果或 partial_with_resume，不得 completed_pass 假完成。",
                "fallback_policy": "失败进入 ErrorPack/AdaptiveWorkLoop；context overflow 先压缩再重试。",
            }
        if playbook_hint:
            payload = {**payload, "playbook_hint": safe_text(playbook_hint, 500)}
        return ContextPack("PlaybookPack", "SkillPlaybookRouter 当前默认工作流", 60, payload, max_chars=1800 if decision.model_tier == "S" else 1000)

    def _constraint_pack(self, model_profile: Any | None, model_policy: Any | None, external_context_hint: str, decision: ContextWindowDecision, playbook_route: Any | None = None) -> ContextPack:
        payload = {
            "a5_boundary": "A5 极高危必须硬拦或人工确认；A0-A4 默认可执行并审计。",
            "workspace_boundary": "文件/打包/质量检查只能在受控 workspace 内执行。",
            "prompt_integrator_boundary": "所有模型请求必须由 PromptIntegrator 编译为 CompiledPromptEnvelope；不得裸发 messages。",
            "privacy_boundary": "不读/不存/不输出 API Key、token、raw prompt、完整敏感文件正文。",
            "model_role": safe_text(getattr(model_policy, "model_role", "") or getattr(model_profile, "recommended_role", ""), 100),
            "prompt_contract": safe_text(getattr(model_policy, "prompt_contract", ""), 100),
            "playbook_id": safe_text(getattr(playbook_route, "playbook_id", ""), 100),
        }
        if external_context_hint:
            raw_hint = str(external_context_hint or "")
            payload["external_context_digest"] = {
                "chars": len(raw_hint),
                "sha256": hashlib.sha256(raw_hint.encode("utf-8", errors="ignore")).hexdigest()[:16],
                "safe_preview": safe_text(raw_hint, 160 if decision.model_tier in {"S", "A"} else 80),
                "policy": "摘要+hash+极短预览；不保存完整外部上下文。",
            }
        return ContextPack("ConstraintPack", "风险 / 隐私 / PromptIntegrator 边界", 70, payload, max_chars=1200 if decision.model_tier in {"S", "A"} else 520)

    def _activation_summary(self, activation_form: Any) -> dict[str, Any]:
        raw = activation_form.public_dict() if hasattr(activation_form, "public_dict") else (activation_form if isinstance(activation_form, dict) else {})
        return {
            "mode": safe_text(raw.get("mode", ""), 40),
            "work_type": safe_text(raw.get("work_type", ""), 40),
            "execution_depth": safe_text(raw.get("execution_depth", ""), 60),
            "risk_level": safe_text(raw.get("risk_level", ""), 20),
            "need_quality_gate": bool(raw.get("need_quality_gate", False)),
            "final_output_contract": safe_text(raw.get("final_output_contract", "execution_report"), 80),
        }

    def _result_summary(self, result: Any) -> dict[str, Any]:
        status = getattr(result, "status", "")
        status_text = getattr(status, "value", status)
        data = getattr(result, "data", {}) or {}
        artifact = str(data.get("path") or data.get("target") or data.get("output_path") or "") if isinstance(data, dict) else ""
        return {
            "tool_name": safe_text(getattr(result, "tool_name", ""), 120),
            "status": safe_text(status_text, 80),
            "error_code": safe_text(getattr(result, "error_code", ""), 120),
            "summary": safe_text(getattr(result, "output_summary", ""), 520),
            "artifact_ref": safe_text(artifact, 240),
            "audit_ref": safe_text(getattr(result, "audit_ref", ""), 120),
        }

    def _candidate_tools(self, available_tools: Iterable[Any] | None, allowed_families: tuple[str, ...], limit: int, *, preferred: tuple[str, ...] = tuple(), forbidden: set[str] | None = None) -> list[dict[str, Any]]:
        if limit <= 0:
            return []
        forbidden = forbidden or set()
        names = []
        for tool in available_tools or ():
            name = safe_text(getattr(tool, "name", tool), 120)
            if name and name not in forbidden:
                names.append(name)
        if not names:
            names = [name for name in _TOOL_USAGE_CARDS if name not in forbidden]
        ranked: list[str] = []
        for name in preferred:
            if name in names and name not in ranked and name not in forbidden:
                ranked.append(name)
        for family in allowed_families or ("file", "code", "document", "delivery", "analysis"):
            prefixes = _FAMILY_TOOL_PREFIXES.get(str(family), (str(family),))
            for name in names:
                if name in ranked or name in forbidden:
                    continue
                if any(name == prefix or name.startswith(prefix) for prefix in prefixes):
                    ranked.append(name)
        for name in ("list_dir", "read_file", "file_sha256", "write_workspace_file", "run_python_quality_check", "scan_project", "diagnose_project", "document_parse", "create_zip_package", "return_analysis"):
            if name in names and name not in ranked and name not in forbidden:
                ranked.append(name)
        for name in names:
            if name not in ranked and name not in forbidden:
                ranked.append(name)
        return [{"tool_name": name, "usage_card": safe_text(_TOOL_USAGE_CARDS.get(name, f"{name}: Runtime 注册工具；仅按 schema 给参数，真实执行由 Runtime 校验。"), 260)} for name in ranked[:limit]]

    def _default_playbook_id(self, work_type: str, user_goal: str) -> str:
        text = str(user_goal or "").lower()
        if work_type == "code" or any(x in text for x in ("pytest", "compile", ".py", "代码", "修复", "bug", "backend", "frontend")):
            return "code_x_bug_fix"
        if work_type == "file" or any(x in text for x in ("txt", "目录", "读取", "创建", "文件")):
            return "workspace_file_simple"
        if work_type == "document" or any(x in text for x in ("docx", "pdf", "文档解析", "总结文档")):
            return "document_parse_rewrite"
        if work_type == "delivery" or any(x in text for x in ("打包", "zip", "交付")):
            return "delivery_package"
        return "mixed_work_default"

    def _default_phase_sequence(self, work_type: str, user_goal: str) -> list[str]:
        playbook = self._default_playbook_id(work_type, user_goal)
        if playbook == "code_x_bug_fix":
            return ["repo_discovery", "localization", "patch_planning", "patch_apply", "validation", "repair", "delivery"]
        if playbook == "workspace_file_simple":
            return ["write_or_read", "verify", "final_report"]
        if playbook == "document_parse_rewrite":
            return ["document_parse", "query_or_rewrite_plan", "apply_or_export", "rollback_ready", "final_report"]
        if playbook == "delivery_package":
            return ["scan_project", "quality_check", "package", "manifest", "report"]
        return ["intake", "plan", "act", "observe", "verify", "final_report"]
