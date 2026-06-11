"""L6.72.57 SkillPlaybookRouter。

把 Code-X / 文件 / 文档 / 交付能力从散装工具列表升级为默认工作流。
该模块只输出工作流路由、候选工具和约束；不执行工具、不写文件正文、不绕过 Runtime。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .context_pack_schema import json_safe, safe_text

SCHEMA_VERSION = "tiangong.l6_72_57.skill_playbook_router.v1"
PLAYBOOK_DIR = Path(__file__).resolve().parent / "playbooks"


@dataclass(frozen=True)
class SkillPlaybook:
    playbook_id: str
    work_type: str
    description: str
    phase_sequence: tuple[str, ...]
    recommended_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...] = tuple()
    verification_policy: str = "阶段结束必须验证；失败进入 partial_with_resume 或 AdaptiveWorkLoop。"
    fallback_policy: str = "失败按 ErrorPack / RecoveryPlan 续接，不假装完成。"

    def public_dict(self) -> dict[str, Any]:
        return {
            "playbook_id": self.playbook_id,
            "work_type": self.work_type,
            "description": safe_text(self.description, 400),
            "phase_sequence": list(self.phase_sequence),
            "recommended_tools": list(self.recommended_tools),
            "forbidden_tools": list(self.forbidden_tools),
            "verification_policy": safe_text(self.verification_policy, 400),
            "fallback_policy": safe_text(self.fallback_policy, 400),
        }


@dataclass(frozen=True)
class SkillPlaybookRoute:
    ok: bool
    playbook_id: str
    work_type: str
    current_phase: str
    phase_sequence: tuple[str, ...]
    recommended_tools: tuple[str, ...]
    forbidden_tools: tuple[str, ...]
    verification_policy: str
    fallback_policy: str
    learned_asset_candidates: tuple[str, ...] = tuple()
    route_reason: str = ""
    model_role: str = ""
    route_source: str = "skill_playbook_router"
    notes: tuple[str, ...] = tuple()

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "ok": bool(self.ok),
            "playbook_id": self.playbook_id,
            "work_type": self.work_type,
            "current_phase": self.current_phase,
            "phase_sequence": list(self.phase_sequence),
            "recommended_tools": list(self.recommended_tools),
            "forbidden_tools": list(self.forbidden_tools),
            "verification_policy": safe_text(self.verification_policy, 600),
            "fallback_policy": safe_text(self.fallback_policy, 600),
            "learned_asset_candidates": list(self.learned_asset_candidates),
            "route_reason": safe_text(self.route_reason, 500),
            "model_role": safe_text(self.model_role, 120),
            "route_source": self.route_source,
            "notes": [safe_text(note, 240) for note in self.notes],
            "execution_boundary": {
                "router_only": True,
                "no_tool_execution": True,
                "conversation_display": False,
                "workbench_display": True,
                "learned_assets_candidate_only": True,
            },
        }

    def prompt_card(self, *, max_chars: int = 1600) -> str:
        payload = json.dumps(self.public_dict(), ensure_ascii=False, sort_keys=True)
        text = "\n".join([
            "[SkillPlaybookRouter / L6.72.57 / 默认工作流路由]",
            "Planner 应优先按 recommended_tools 和 phase_sequence 生成短步计划；forbidden_tools 不得用于本轮。",
            payload,
        ])
        return safe_text(text, max_chars)


_DEFAULT_PLAYBOOKS: dict[str, SkillPlaybook] = {
    "code_x_bug_fix": SkillPlaybook(
        playbook_id="code_x_bug_fix",
        work_type="code",
        description="代码修复默认工作流：发现项目结构、定位问题、规划补丁、应用修改、验证、修复、交付。",
        phase_sequence=("repo_discovery", "localization", "patch_planning", "patch_apply", "validation", "repair", "delivery"),
        recommended_tools=(
            "scan_project",
            "diagnose_project",
            "read_file",
            "write_workspace_file",
            "run_python_quality_check",
            "code_x_runtime_status",
            "code_x_smoke_workflow",
            "create_zip_package",
        ),
        forbidden_tools=("document_parse", "document_query", "document_rewrite_plan"),
        verification_policy="代码修改后必须运行 compileall / pytest / 对应质量检查；质量检查失败不得 completed_pass。",
        fallback_policy="定位失败进入 diagnose_project；验证失败进入 AdaptiveWorkLoop repair；仍失败则 partial_with_resume。",
    ),
    "workspace_file_simple": SkillPlaybook(
        playbook_id="workspace_file_simple",
        work_type="file",
        description="普通工作区文件读写工作流：写入或读取、验证、报告。创建 txt/md/json 不进入文档解析系统。",
        phase_sequence=("write_or_read", "verify", "final_report"),
        recommended_tools=("list_dir", "read_file", "write_workspace_file", "return_analysis"),
        forbidden_tools=("document_parse", "document_query", "document_rewrite_plan", "document_apply_rewrite"),
        verification_policy="写文件后必须 read_file 或物理落盘验证；读取失败进入 failed_recoverable。",
        fallback_policy="Provider 不可用时可用 deterministic fallback；不可确定任务输出 model_required。",
    ),
    "document_parse_rewrite": SkillPlaybook(
        playbook_id="document_parse_rewrite",
        work_type="document",
        description="明确 docx/pdf/pptx/xlsx/txt 文档解析、追问、改写、导出与回滚工作流。",
        phase_sequence=("document_parse", "query_or_rewrite_plan", "apply_or_export", "rollback_ready", "final_report"),
        recommended_tools=("document_parse", "document_query", "document_rewrite_plan", "document_apply_rewrite", "document_export", "document_rollback"),
        forbidden_tools=(),
        verification_policy="文档写回必须保留回滚证据；导出必须返回 artifact refs。",
        fallback_policy="解析失败只返回文档错误摘要，不改写原文件；可回滚优先。",
    ),
    "delivery_package": SkillPlaybook(
        playbook_id="delivery_package",
        work_type="delivery",
        description="交付打包工作流：扫描项目、质量检查、打包、manifest、报告。",
        phase_sequence=("scan_project", "quality_check", "package", "manifest", "report"),
        recommended_tools=("scan_project", "run_python_quality_check", "diagnose_project", "create_zip_package", "create_release_bundle", "build_delivery_standardization"),
        forbidden_tools=("document_parse", "document_apply_rewrite"),
        verification_policy="打包前至少有项目扫描和质量检查摘要；失败不得 completed_pass。",
        fallback_policy="质量检查失败则 completed_with_warnings 或 partial_with_resume，不阻塞非 A5 打包报告。",
    ),
    "mixed_work_default": SkillPlaybook(
        playbook_id="mixed_work_default",
        work_type="mixed",
        description="混合工作默认流程：先扫描/澄清，再按文件、代码、文档或交付路由。",
        phase_sequence=("intake", "plan", "act", "observe", "verify", "final_report"),
        recommended_tools=("scan_project", "list_dir", "read_file", "return_analysis"),
        forbidden_tools=(),
        verification_policy="每阶段必须有可验证工具结果或明确 partial_with_resume。",
        fallback_policy="无法确认任务类型时输出短计划或要求补充，不假装完成。",
    ),
}


class SkillPlaybookRouter:
    def __init__(self, playbook_dir: str | Path | None = None) -> None:
        self.playbook_dir = Path(playbook_dir) if playbook_dir is not None else PLAYBOOK_DIR
        self.playbooks = self._load_playbooks()
        self.last_route: SkillPlaybookRoute | None = None

    def route(
        self,
        *,
        activation_form: Any | None = None,
        user_goal: str = "",
        model_profile: Any | None = None,
        task_state: Any | None = None,
        available_tools: Iterable[Any] | None = None,
        learned_assets: Iterable[Any] | None = None,
    ) -> SkillPlaybookRoute:
        work_type = self._work_type(activation_form, user_goal)
        playbook_id, reason = self._select_playbook_id(work_type, user_goal)
        playbook = self.playbooks.get(playbook_id) or self.playbooks["mixed_work_default"]
        available = self._available_names(available_tools)
        recommended = self._filter_recommended(playbook.recommended_tools, available)
        learned_candidates = self._learned_candidates(learned_assets)
        current_phase = safe_text(getattr(task_state, "current_phase", "") or (playbook.phase_sequence[0] if playbook.phase_sequence else "intake"), 80)
        route = SkillPlaybookRoute(
            ok=True,
            playbook_id=playbook.playbook_id,
            work_type=playbook.work_type,
            current_phase=current_phase,
            phase_sequence=playbook.phase_sequence,
            recommended_tools=tuple(recommended),
            forbidden_tools=tuple(playbook.forbidden_tools),
            verification_policy=playbook.verification_policy,
            fallback_policy=playbook.fallback_policy,
            learned_asset_candidates=learned_candidates,
            route_reason=reason,
            model_role=safe_text(getattr(model_profile, "recommended_role", ""), 120),
            notes=("learned_assets_candidate_only", "router_does_not_execute_tools"),
        )
        self.last_route = route
        return route

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "loaded_playbooks": sorted(self.playbooks),
            "last_route": self.last_route.public_dict() if self.last_route else None,
            "router_only": True,
            "no_tool_execution": True,
        }

    def build_planner_hint(self) -> str:
        return self.last_route.prompt_card(max_chars=1400) if self.last_route is not None else ""

    def _load_playbooks(self) -> dict[str, SkillPlaybook]:
        out = dict(_DEFAULT_PLAYBOOKS)
        if self.playbook_dir.exists():
            for path in sorted(self.playbook_dir.glob("*.json")):
                try:
                    data = json.loads(path.read_text(encoding="utf-8"))
                    playbook = SkillPlaybook(
                        playbook_id=safe_text(data.get("playbook_id") or path.stem, 120),
                        work_type=safe_text(data.get("work_type") or "mixed", 80),
                        description=safe_text(data.get("description") or "", 500),
                        phase_sequence=tuple(safe_text(x, 80) for x in data.get("phase_sequence", []) if x),
                        recommended_tools=tuple(safe_text(x, 120) for x in data.get("recommended_tools", []) if x),
                        forbidden_tools=tuple(safe_text(x, 120) for x in data.get("forbidden_tools", []) if x),
                        verification_policy=safe_text(data.get("verification_policy") or "", 600),
                        fallback_policy=safe_text(data.get("fallback_policy") or "", 600),
                    )
                    if playbook.playbook_id:
                        out[playbook.playbook_id] = playbook
                except Exception:  # noqa: BLE001 - corrupted playbook should not break runtime import
                    continue
        return out

    def _work_type(self, activation_form: Any | None, user_goal: str) -> str:
        raw: dict[str, Any] = {}
        if hasattr(activation_form, "public_dict"):
            raw = activation_form.public_dict()
        elif isinstance(activation_form, dict):
            raw = activation_form
        work_type = safe_text(raw.get("work_type", ""), 40).lower()
        if work_type and work_type != "none":
            return work_type
        return self._infer_work_type(user_goal)

    def _select_playbook_id(self, work_type: str, user_goal: str) -> tuple[str, str]:
        text = str(user_goal or "").lower()
        if self._is_simple_file(text):
            return "workspace_file_simple", "普通工作区文件读写：txt/md/json/列目录/读取，不走 document_parse。"
        if self._is_document_task(text) or work_type == "document":
            return "document_parse_rewrite", "明确文档解析/追问/改写/导出任务。"
        if self._is_delivery_task(text) or work_type == "delivery":
            return "delivery_package", "交付/打包/manifest 任务。"
        if self._is_code_task(text) or work_type in {"code", "terminal"}:
            return "code_x_bug_fix", "代码/项目修复任务默认进入 Code-X 工作流。"
        if work_type == "file":
            return "workspace_file_simple", "ActivationForm work_type=file。"
        return "mixed_work_default", "未命中专用 playbook，使用混合默认流程。"

    def _infer_work_type(self, user_goal: str) -> str:
        text = str(user_goal or "").lower()
        if self._is_simple_file(text):
            return "file"
        if self._is_document_task(text):
            return "document"
        if self._is_delivery_task(text):
            return "delivery"
        if self._is_code_task(text):
            return "code"
        return "mixed"

    def _is_simple_file(self, text: str) -> bool:
        simple_markers = (".txt", ".md", ".json", "列目录", "读取目录", "list dir", "创建", "写入", "普通文件")
        document_markers = ("docx", "pdf", "pptx", "xlsx", "文档解析", "解析文档", "改写文档")
        return any(x in text for x in simple_markers) and not any(x in text for x in document_markers)

    def _is_document_task(self, text: str) -> bool:
        return any(x in text for x in ("docx", "pdf", "pptx", "xlsx", "文档解析", "解析文档", "总结文档", "改写文档", "document_parse"))

    def _is_delivery_task(self, text: str) -> bool:
        return any(x in text for x in ("打包", "交付", "zip", "release", "manifest", "发布包"))

    def _is_code_task(self, text: str) -> bool:
        return any(x in text for x in ("修复", "bug", "pytest", "compileall", ".py", "代码", "项目", "backend", "frontend", "runtime", "跨文件"))

    def _available_names(self, available_tools: Iterable[Any] | None) -> tuple[str, ...]:
        names: list[str] = []
        for tool in available_tools or ():
            name = safe_text(getattr(tool, "name", tool), 120)
            if name:
                names.append(name)
        return tuple(dict.fromkeys(names))

    def _filter_recommended(self, recommended: Iterable[str], available: tuple[str, ...]) -> list[str]:
        if not available:
            return [safe_text(name, 120) for name in recommended]
        available_set = set(available)
        selected = [name for name in recommended if name in available_set]
        # Code-X full tools may not exist in slim packages; keep robust Runtime fallbacks.
        fallbacks = ["scan_project", "diagnose_project", "list_dir", "read_file", "write_workspace_file", "run_python_quality_check", "create_zip_package", "return_analysis"]
        for name in fallbacks:
            if name in available_set and name not in selected:
                selected.append(name)
        return selected[:20]

    def _learned_candidates(self, learned_assets: Iterable[Any] | None) -> tuple[str, ...]:
        out: list[str] = []
        for item in learned_assets or ():
            if isinstance(item, str):
                name = item
            elif isinstance(item, dict):
                name = str(item.get("name") or item.get("tool_name") or item.get("asset_id") or "")
            else:
                name = str(getattr(item, "name", "") or getattr(item, "asset_id", ""))
            name = safe_text(name, 120)
            if name and name.startswith(("learned_", "skill_")):
                out.append(name)
        return tuple(dict.fromkeys(out))[:20]
