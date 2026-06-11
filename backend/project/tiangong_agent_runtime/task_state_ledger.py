"""L6.72.53 持久化任务状态账本。

被动记录层：只写安全摘要与引用，不改变 Planner、工具执行、QualityGate、
前端渲染行为。写入失败不会打断 Runtime 主链。
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from uuid import uuid4

from tiangong_agent_shell.safe_logging import redact_text

from .task_state_schema import TaskEvent, TaskState, json_safe, new_task_id, now_iso, safe_preview




def _state_root(workspace: str | Path, root_name: str) -> Path:
    override = os.environ.get("LINYUANZHE_STATE_DIR") or os.environ.get("TIANGONG_STATE_DIR")
    if override:
        return Path(override).expanduser().resolve() / root_name.replace(".linyuanzhe/", "")
    return Path(workspace).expanduser().resolve() / root_name

def _status_of(result: Any) -> str:
    status = getattr(result, "status", "")
    value = getattr(status, "value", status)
    return str(value or "unknown")


class TaskStateLedger:
    def __init__(self, root_name: str = ".linyuanzhe/tasks") -> None:
        self.root_name = root_name
        self.last_task_id: str = ""
        self.last_task_path: str = ""
        self.last_error: str = ""
        self._cache: dict[str, TaskState] = {}
        self._roots: dict[str, Path] = {}

    def create_task(
        self,
        workspace: str | Path,
        *,
        user_goal: str,
        user_selected_mode: str = "work",
        model_profile_ref: str = "",
        model_profile: dict[str, Any] | None = None,
        model_execution_policy: dict[str, Any] | None = None,
        final_output_contract: str = "execution_report",
    ) -> TaskState:
        task = TaskState(
            task_id=new_task_id(),
            created_at=now_iso(),
            updated_at=now_iso(),
            user_goal=safe_preview(user_goal, 1800),
            normalized_goal=safe_preview(user_goal, 1800),
            user_selected_mode=user_selected_mode,
            model_profile_ref=model_profile_ref,
            model_profile=model_profile,
            model_execution_policy=model_execution_policy,
            final_output_contract=final_output_contract,
            current_phase="created",
            status="created",
            next_action="await_activation_or_plan",
        )
        self._cache[task.task_id] = task
        self._roots[task.task_id] = self._task_root(workspace, task.task_id)
        self._persist(task)
        self.append_event(task.task_id, "task_created", {"user_selected_mode": user_selected_mode, "model_profile_ref": model_profile_ref})
        return task


    def record_context_pack(self, task_id: str, context_bundle: Any, *, stage: str = "planning") -> None:
        """L6.72.56：记录 ContextWindowManager 上下文包摘要。"""
        task = self._cache.get(task_id)
        root = self._roots.get(task_id)
        if task is None:
            return
        payload = context_bundle.public_dict() if hasattr(context_bundle, "public_dict") else json_safe(context_bundle)
        if not isinstance(payload, dict):
            payload = {"summary": safe_preview(payload, 600)}
        summary = {
            "bundle_id": safe_preview(payload.get("bundle_id", ""), 120),
            "stage": safe_preview(stage or payload.get("stage", ""), 80),
            "model_tier": safe_preview(payload.get("model_tier", ""), 40),
            "model_role": safe_preview(payload.get("model_role", ""), 80),
            "pack_names": json_safe(payload.get("pack_names", [])),
            "total_chars": int(payload.get("total_chars", 0) or 0),
            "max_context_chars": int(payload.get("max_context_chars", 0) or 0),
            "context_overflow_recovered": bool(payload.get("context_overflow_recovered", False)),
            "storage_boundary": {"no_api_key": True, "no_raw_prompt": True, "no_full_file_content": True, "summary_and_refs_only": True},
        }
        existing = [item for item in list(getattr(task, "context_packs", []) or []) if item.get("bundle_id") != summary["bundle_id"]]
        task.context_packs = (existing + [summary])[-12:]
        task.token_budget = {**(task.token_budget or {}), "last_context_pack": summary, "context_pack_count": len(task.context_packs)}
        task.updated_at = now_iso()
        self._persist(task)
        if root is not None:
            try:
                context_dir = root / "context_packs"
                context_dir.mkdir(parents=True, exist_ok=True)
                bundle_id = summary.get("bundle_id") or f"context_pack_{len(task.context_packs)}"
                (context_dir / f"{bundle_id}.json").write_text(json.dumps(json_safe(payload), ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                self.last_error = redact_text(f"{type(exc).__name__}: {exc}")[:300]
        self.append_event(task_id, "context_pack_recorded", summary)

    def record_skill_playbook_route(self, task_id: str, route: Any, *, stage: str = "planning") -> None:
        """L6.72.57：记录 SkillPlaybookRouter 路由摘要。"""
        task = self._cache.get(task_id)
        root = self._roots.get(task_id)
        if task is None:
            return
        payload = route.public_dict() if hasattr(route, "public_dict") else json_safe(route)
        if not isinstance(payload, dict):
            payload = {"summary": safe_preview(payload, 600)}
        summary = {
            "stage": safe_preview(stage or payload.get("current_phase", ""), 80),
            "playbook_id": safe_preview(payload.get("playbook_id", ""), 120),
            "work_type": safe_preview(payload.get("work_type", ""), 80),
            "current_phase": safe_preview(payload.get("current_phase", ""), 120),
            "phase_sequence": json_safe(payload.get("phase_sequence", [])),
            "recommended_tools": json_safe(payload.get("recommended_tools", [])),
            "forbidden_tools": json_safe(payload.get("forbidden_tools", [])),
            "learned_asset_candidates": json_safe(payload.get("learned_asset_candidates", [])),
            "route_reason": safe_preview(payload.get("route_reason", ""), 400),
            "conversation_display": False,
        }
        task.playbook_routes = (list(getattr(task, "playbook_routes", []) or []) + [summary])[-12:]
        task.current_subgoal = summary["current_phase"] or task.current_subgoal
        task.token_budget = {**(task.token_budget or {}), "last_playbook_route": summary}
        task.updated_at = now_iso()
        self._persist(task)
        if root is not None:
            try:
                route_dir = root / "playbook_routes"
                route_dir.mkdir(parents=True, exist_ok=True)
                name = f"{len(task.playbook_routes):03d}_{summary['playbook_id'] or 'playbook'}.json"
                (route_dir / name).write_text(json.dumps(json_safe(payload), ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                self.last_error = redact_text(f"{type(exc).__name__}: {exc}")[:300]
        self.append_event(task_id, "skill_playbook_route_recorded", summary)

    def record_active_model_policy(self, task_id: str, active_policy: Any, *, stage: str = "planning", plan_filter: Any | None = None) -> None:
        """L6.72.58：记录主动 ModelExecutionPolicy 生效摘要。"""
        task = self._cache.get(task_id)
        root = self._roots.get(task_id)
        if task is None:
            return
        payload = active_policy.public_dict() if hasattr(active_policy, "public_dict") else json_safe(active_policy)
        if not isinstance(payload, dict):
            payload = {"summary": safe_preview(payload, 600)}
        filter_payload = plan_filter.public_dict() if hasattr(plan_filter, "public_dict") else (json_safe(plan_filter) if plan_filter is not None else None)
        summary = {
            "stage": safe_preview(stage, 80),
            "model_role": safe_preview(payload.get("model_role", ""), 80),
            "allowed_work_mode": bool(payload.get("allowed_work_mode", False)),
            "status": safe_preview(payload.get("status", ""), 80),
            "failure_kind": safe_preview(payload.get("failure_kind", ""), 120),
            "effective_max_steps": int(payload.get("effective_max_steps", 0) or 0),
            "prompt_contract": safe_preview(payload.get("prompt_contract", ""), 100),
            "allowed_tool_families": json_safe(payload.get("allowed_tool_families", [])),
            "plan_filter": json_safe(filter_payload) if filter_payload is not None else None,
            "conversation_display": False,
        }
        task.active_model_policy = summary
        task.token_budget = {**(task.token_budget or {}), "active_model_policy": summary}
        if not summary["allowed_work_mode"]:
            task.status = "model_required"
            task.current_phase = "model_policy_blocked"
            task.next_action = "switch_model_or_chat_only"
            task.recovery_plan = {
                "kind": "l6_72_58_active_model_policy",
                "can_resume": False,
                "next_action": "switch_to_main_brain_model",
                "failure_kind": summary["failure_kind"],
            }
        task.updated_at = now_iso()
        self._persist(task)
        if root is not None:
            try:
                policy_dir = root / "model_policy"
                policy_dir.mkdir(parents=True, exist_ok=True)
                (policy_dir / f"{safe_preview(stage, 40) or 'policy'}_active_policy.json").write_text(json.dumps(json_safe({"active_policy": payload, "plan_filter": filter_payload}), ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as exc:  # noqa: BLE001
                self.last_error = redact_text(f"{type(exc).__name__}: {exc}")[:300]
        self.append_event(task_id, "active_model_policy_recorded", summary)


    def record_activation(self, task_id: str, activation_form: Any | None) -> None:
        task = self._cache.get(task_id)
        if task is None:
            return
        payload = activation_form.public_dict() if hasattr(activation_form, "public_dict") else activation_form
        task.activation_form = json_safe(payload)
        task.current_phase = "activation_decided"
        task.status = "activation_decided"
        if isinstance(payload, dict):
            task.final_output_contract = str(payload.get("final_output_contract") or task.final_output_contract)
            depth = str(payload.get("execution_depth") or "")
            wtype = str(payload.get("work_type") or "")
            task.current_subgoal = f"{wtype}/{depth}".strip("/")
            task.next_action = "build_model_plan" if payload.get("tools_requested") else "answer_without_tools"
        task.updated_at = now_iso()
        self._persist(task)
        self.append_event(task_id, "activation_recorded", {"activation_form": payload})

    def record_plan(self, task_id: str, plan: list[Any], planner_result: Any | None = None) -> None:
        task = self._cache.get(task_id)
        if task is None:
            return
        steps = [self._step_public(step, i) for i, step in enumerate(plan or [])]
        task.current_plan = steps
        task.plan_history.append(
            {
                "created_at": now_iso(),
                "step_count": len(steps),
                "planner_result": self._planner_public(planner_result),
                "steps": steps,
            }
        )
        task.current_phase = "planning" if steps else "planning_empty"
        task.status = "planning" if steps else "failed_recoverable"
        task.next_action = "execute_plan" if steps else "plan_repair_or_user_clarification"
        task.updated_at = now_iso()
        self._persist(task)
        self.append_event(task_id, "plan_recorded", {"step_count": len(steps), "planner_ok": bool(getattr(planner_result, "ok", False))})

    def record_execution(self, task_id: str, results: list[Any], planner_report: Any | None = None, projection: Any | None = None) -> None:
        task = self._cache.get(task_id)
        if task is None:
            return
        step_summaries = [self._result_public(result, i) for i, result in enumerate(results or [])]
        task.executed_steps.extend(step_summaries)
        failed = [item for item in step_summaries if item.get("status") not in {"success", "ok", "skipped"}]
        task.unresolved_failures = failed[-10:]
        task.current_phase = "verifying" if results else task.current_phase
        if failed:
            task.status = "failed_recoverable"
            task.next_action = "classify_failure_or_resume"
        elif results:
            task.status = "completed_pass"
            task.next_action = "final_report"
        else:
            task.status = "partial_with_resume" if task.current_plan else task.status
        task.quality_gate = self._quality_public(planner_report, projection)
        if planner_report is not None:
            task.evidence_refs.append(self._report_ref(planner_report))
        for item in step_summaries:
            if item.get("audit_ref"):
                task.audit_refs.append({"audit_ref": item.get("audit_ref"), "tool_name": item.get("tool_name")})
        task.updated_at = now_iso()
        self._persist(task)
        self.append_event(task_id, "execution_recorded", {"result_count": len(step_summaries), "failed_count": len(failed), "status": task.status})

    def record_work_failure_contract(self, task_id: str, report: Any, *, planner_result: Any | None = None) -> None:
        """L6.72.54：work 模式失败也必须写成可续接任务状态。

        只写脱敏摘要和 machine-actionable status/next_action；不存 raw prompt、API Key
        或完整文件内容。
        """
        task = self._cache.get(task_id)
        if task is None:
            return
        status = str(getattr(report, "status", "failed_recoverable") or "failed_recoverable")
        failure_kind = str(getattr(report, "failure_kind", "planner_failed") or "planner_failed")
        next_action = str(getattr(report, "next_action", "plan_repair_or_resume") or "plan_repair_or_resume")
        summary = safe_preview(getattr(report, "user_visible_summary", ""), 900)
        task.current_phase = "work_failure_contract"
        task.status = status
        task.next_action = next_action
        task.final_output_contract = "execution_report"
        task.unresolved_failures = ([
            {
                "failure_kind": failure_kind,
                "status": status,
                "summary": summary,
                "planner_result": self._planner_public(planner_result),
                "next_action": next_action,
            }
        ] + list(task.unresolved_failures or []))[:10]
        task.recovery_plan = {
            "kind": "l6_72_54_work_failure_contract",
            "failure_kind": failure_kind,
            "status": status,
            "can_resume": status not in {"blocked_A5"},
            "next_action": next_action,
        }
        task.updated_at = now_iso()
        self._persist(task)
        self.append_event(task_id, "work_failure_recorded", {"status": status, "failure_kind": failure_kind, "next_action": next_action})


    def record_adaptive_repair(self, task_id: str, adaptive_report: Any) -> None:
        """L6.72.55：记录一次性 AdaptiveWorkLoop repair 结果。

        只保存 original_plan / repair_plan / quality / next_action 的公开摘要；不保存 raw prompt、
        API Key 或完整文件正文。该记录层不额外执行工具。
        """
        task = self._cache.get(task_id)
        if task is None:
            return
        payload = adaptive_report.public_dict() if hasattr(adaptive_report, "public_dict") else json_safe(adaptive_report)
        if not isinstance(payload, dict):
            payload = {"summary": safe_preview(payload, 600)}
        status = str(payload.get("status") or "partial_with_resume")
        next_action = str(payload.get("next_action") or "resume_from_repair_context")
        retry_budget = payload.get("retry_budget") if isinstance(payload.get("retry_budget"), dict) else {}
        quality_payload = {
            "kind": "l6_72_55_adaptive_repair_quality",
            "status": status,
            "quality_status": safe_preview(payload.get("quality_status", ""), 120),
            "repair_succeeded": bool(payload.get("repair_succeeded")),
            "retry_budget": json_safe(retry_budget),
            "repair_execution_report_digest": safe_preview(
                ((payload.get("repair_execution_report") or {}) if isinstance(payload.get("repair_execution_report"), dict) else {}).get("report_digest", ""),
                200,
            ),
        }
        task.plan_history.append(
            {
                "created_at": now_iso(),
                "kind": "l6_72_55_adaptive_repair",
                "original_plan": json_safe(payload.get("original_plan") or []),
                "repair_plan": json_safe(payload.get("repair_plan") or []),
                "planner_result": json_safe(payload.get("planner_result") or {}),
                "status": status,
                "next_action": safe_preview(next_action, 300),
            }
        )
        repair_plan = payload.get("repair_plan") or []
        if isinstance(repair_plan, list) and repair_plan:
            task.current_plan = json_safe(repair_plan)
        task.quality_gate = quality_payload
        task.recovery_plan = {
            "kind": "l6_72_55_adaptive_work_loop_v1",
            "status": status,
            "can_resume": status not in {"completed_pass", "blocked_A5", "awaiting_confirmation"},
            "next_action": safe_preview(next_action, 300),
            "repair_context": json_safe(payload.get("repair_context") or {}),
            "one_repair_attempt_only": True,
        }
        failures = []
        context = payload.get("repair_context") if isinstance(payload.get("repair_context"), dict) else {}
        for item in (context.get("failures") if isinstance(context, dict) else []) or []:
            failures.append(json_safe(item))
        if status in {"completed_pass", "completed_with_warnings"}:
            task.unresolved_failures = []
            task.current_phase = "adaptive_repair_completed"
        else:
            task.unresolved_failures = (failures + list(task.unresolved_failures or []))[:10]
            task.current_phase = "adaptive_repair_partial"
        task.status = status
        task.next_action = next_action
        task.final_output_contract = "execution_report"
        used = int(retry_budget.get("used", 1) or 1)
        maximum = int(retry_budget.get("max", 1) or 1)
        task.retry_budget = {"max_retries": maximum, "used": max(int((task.retry_budget or {}).get("used", 0) or 0), used)}
        repair_report = payload.get("repair_execution_report") if isinstance(payload.get("repair_execution_report"), dict) else {}
        digest = safe_preview(repair_report.get("report_digest", ""), 200) if isinstance(repair_report, dict) else ""
        if digest:
            task.evidence_refs.append({"type": "adaptive_repair_execution_report", "report_digest": digest, "status": status})
        task.updated_at = now_iso()
        self._persist(task)
        self.append_event(task_id, "adaptive_repair_recorded", {"status": status, "next_action": next_action, "retry_budget": retry_budget})

    def load_task(self, workspace: str | Path, task_id: str) -> TaskState | None:
        try:
            path = self._task_root(workspace, task_id) / "task_state.json"
            if not path.exists():
                return self._cache.get(task_id)
            raw = json.loads(path.read_text(encoding="utf-8"))
            state = TaskState(
                task_id=str(raw.get("task_id") or task_id),
                created_at=str(raw.get("created_at") or now_iso()),
                updated_at=str(raw.get("updated_at") or now_iso()),
                user_goal=str(raw.get("user_goal") or ""),
                normalized_goal=str(raw.get("normalized_goal") or ""),
                user_selected_mode=str(raw.get("user_selected_mode") or "work"),
            )
            for key, value in raw.items():
                if hasattr(state, key):
                    setattr(state, key, value)
            self._cache[state.task_id] = state
            self._roots[state.task_id] = self._task_root(workspace, task_id)
            return state
        except Exception as exc:  # noqa: BLE001
            self.last_error = redact_text(f"{type(exc).__name__}: {exc}")[:300]
            return None

    def append_event(self, task_id: str, event_type: str, payload: dict[str, Any] | None = None) -> None:
        task = self._cache.get(task_id)
        root = self._roots.get(task_id)
        if task is None or root is None:
            return
        event = TaskEvent(
            event_id="evt_" + uuid4().hex[:12],
            task_id=task_id,
            event_type=event_type,
            created_at=now_iso(),
            payload=json_safe(payload or {}),
        )
        try:
            root.mkdir(parents=True, exist_ok=True)
            with (root / "events.jsonl").open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(event.public_dict(), ensure_ascii=False) + "\n")
        except Exception as exc:  # noqa: BLE001
            self.last_error = redact_text(f"{type(exc).__name__}: {exc}")[:300]

    def latest_snapshot(self) -> dict[str, Any]:
        task = self._cache.get(self.last_task_id)
        return {
            "schema": "tiangong.l6_72_53.task_state_ledger_snapshot.v1",
            "last_task_id": self.last_task_id,
            "last_task_path": self.last_task_path,
            "last_error": self.last_error,
            "task": task.public_dict() if task is not None else None,
            "passive_only": True,
        }

    def _task_root(self, workspace: str | Path, task_id: str) -> Path:
        return _state_root(workspace, self.root_name) / task_id

    def _persist(self, task: TaskState) -> None:
        root = self._roots.get(task.task_id)
        if root is None:
            return
        try:
            root.mkdir(parents=True, exist_ok=True)
            (root / "task_state.json").write_text(json.dumps(task.public_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
            artifacts = {
                "schema": "tiangong.l6_72_53.artifacts_manifest.v1",
                "task_id": task.task_id,
                "artifact_refs": task.artifact_refs,
                "evidence_refs": task.evidence_refs,
                "passive_only": True,
            }
            (root / "artifacts_manifest.json").write_text(json.dumps(artifacts, ensure_ascii=False, indent=2), encoding="utf-8")
            quality_dir = root / "quality"
            quality_dir.mkdir(exist_ok=True)
            if task.quality_gate is not None:
                (quality_dir / "latest_quality.json").write_text(json.dumps(task.quality_gate, ensure_ascii=False, indent=2), encoding="utf-8")
            context_dir = root / "context_packs"
            context_dir.mkdir(exist_ok=True)
            playbook_dir = root / "playbook_routes"
            playbook_dir.mkdir(exist_ok=True)
            handoff = [
                f"# TaskState Handoff Digest",
                f"task_id: {task.task_id}",
                f"status: {task.status}",
                f"phase: {task.current_phase}",
                f"next_action: {task.next_action}",
                "",
                "本文件由 L6.72.53 被动任务账本生成，只含安全摘要与引用。",
            ]
            (root / "handoff_digest.md").write_text("\n".join(handoff), encoding="utf-8")
            self.last_task_id = task.task_id
            self.last_task_path = str(root)
            self.last_error = ""
        except Exception as exc:  # noqa: BLE001 - passive ledger must not break Runtime
            self.last_error = redact_text(f"{type(exc).__name__}: {exc}")[:300]

    def _step_public(self, step: Any, index: int) -> dict[str, Any]:
        return {
            "index": index,
            "step_id": safe_preview(getattr(step, "step_id", ""), 120),
            "tool_name": safe_preview(getattr(step, "tool_name", ""), 120),
            "reason": safe_preview(getattr(step, "reason", ""), 300),
            "arguments_keys": sorted([safe_preview(k, 80) for k in getattr(step, "arguments", {}).keys()]) if isinstance(getattr(step, "arguments", None), dict) else [],
        }

    def _result_public(self, result: Any, index: int) -> dict[str, Any]:
        data = getattr(result, "data", {}) or {}
        artifact = ""
        if isinstance(data, dict):
            artifact = str(data.get("path") or data.get("target") or data.get("output_path") or "")[:500]
        return {
            "index": index,
            "tool_name": safe_preview(getattr(result, "tool_name", ""), 120),
            "status": _status_of(result),
            "error_code": safe_preview(getattr(result, "error_code", ""), 120),
            "summary": safe_preview(getattr(result, "output_summary", ""), 600),
            "audit_ref": safe_preview(getattr(result, "audit_ref", ""), 120),
            "artifact_ref": safe_preview(artifact, 500),
        }

    def _planner_public(self, planner_result: Any | None) -> dict[str, Any] | None:
        if planner_result is None:
            return None
        try:
            payload = planner_result.public_dict() if hasattr(planner_result, "public_dict") else planner_result
            if isinstance(payload, dict):
                payload.pop("raw_preview", None)
            return json_safe(payload)
        except Exception:  # noqa: BLE001
            return {"summary": safe_preview(planner_result, 300)}

    def _quality_public(self, planner_report: Any | None, projection: Any | None) -> dict[str, Any]:
        return {
            "planner_report_digest": safe_preview(getattr(planner_report, "report_digest", ""), 200),
            "projection_status": safe_preview(getattr(projection, "status", ""), 120),
            "projection_summary": safe_preview(getattr(projection, "summary", ""), 600),
            "warning": "quality status is projection-level in L6.72.53 passive ledger",
        }

    def _report_ref(self, planner_report: Any) -> dict[str, Any]:
        return {
            "type": "planner_execution_report",
            "report_digest": safe_preview(getattr(planner_report, "report_digest", ""), 200),
            "status": safe_preview(getattr(planner_report, "status", ""), 120),
        }
