"""v1 clean semantic import tools for v2 Runtime.

This module is a pure v2-native reconstruction of the useful non-Code-X
semantics found in the user-supplied v1 tools bundle. It intentionally does not
copy v1 source, import v1 modules, use v1 registries, start background loops, or
auto-execute side effects. All functions are deterministic, local, auditable,
and designed to return evidence plus next_action_hint for the LLM main brain.
"""
from __future__ import annotations

import csv
import hashlib
import html
import json
import os
import re
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping
from xml.etree import ElementTree

TEXT_EXTENSIONS = {
    ".txt", ".md", ".rst", ".adoc", ".json", ".jsonl", ".csv", ".tsv",
    ".toml", ".yaml", ".yml", ".ini", ".cfg", ".py", ".js", ".jsx",
    ".ts", ".tsx", ".css", ".html", ".htm", ".xml", ".sh", ".ps1",
}
DOCUMENT_EXTENSIONS = TEXT_EXTENSIONS | {".docx", ".pdf"}
IGNORE_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache",
    ".ruff_cache", ".venv", "venv", "env", "node_modules", "dist", "build",
    ".codex_snapshots", ".codex_delivery", ".cache", ".next", ".nuxt",
}
SECRET_RE = re.compile(
    r"(?i)(api[_-]?key|secret|token|password|authorization)\s*[:=]\s*['\"]?[^\s,'\"]+"
)
TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*|[0-9]+|[\u4e00-\u9fff]+")

V1_BUNDLE_FINGERPRINT = {
    "uploaded_name": "v1_tools_code_search.zip",
    "audited_files": 35,
    "python_modules": 26,
    "artifacts": [
        "artifacts/nengli/ability_packages.jsonl",
        "artifacts/nengli/capability_map.jsonl",
        "artifacts/zhishi/skill_versions.jsonl",
        "artifacts/zhishi/skill_templates.jsonl",
    ],
    "policy": "lessons_only_no_source_copy",
}

DEDUP_DECISIONS: list[dict[str, Any]] = [
    {
        "v1_area": "代码生产链",
        "source_examples": ["daima_luoji_gongju.py", "daima_zhixing_gongju.py", "zhongduan_adapter.py"],
        "decision": "dedup_to_codex",
        "v2_mapping": ["Code-X repo_map/symbol_index/localizer/patch/runner/failure_repair/rollback"],
        "imported_now": False,
        "reason": "R13C1 已覆盖核心代码外骨骼语义；重复导入会污染 Code-X 边界。",
    },
    {
        "v1_area": "文件读写/传输治理",
        "source_examples": ["wenjian_gongju.py", "sousuo_wenjian_adapter.py"],
        "decision": "partial_rebuild_readonly",
        "v2_mapping": ["read_file", "write_workspace_file", "zip_delivery_packager", "workspace_text_search"],
        "imported_now": True,
        "reason": "写入/传输已由 v2 与 Code-X 管；仅补只读全文搜索。",
    },
    {
        "v1_area": "会话/作业/经验搜索",
        "source_examples": ["huihua_sousuo_gongju.py", "zuoye_sousuo_gongju.py", "chuanbangdai_gongju.py"],
        "decision": "pure_rebuild",
        "v2_mapping": ["conversation_history_search", "task_pattern_search", "experience_mentor_search"],
        "imported_now": True,
        "reason": "只读检索历史留痕和 Skill 材料，适合作为 v2 独立搜索系统。",
    },
    {
        "v1_area": "文档提取",
        "source_examples": ["wendang_tiqu_gongju.py", "wendang_tiqu_adapter.py"],
        "decision": "pure_rebuild",
        "v2_mapping": ["document_text_extract"],
        "imported_now": True,
        "reason": "补文本/JSON/CSV/DOCX/PDF 降级提取；不引入外部解析器。",
    },
    {
        "v1_area": "网页/深抓/可读性",
        "source_examples": ["tiangong_wangye_gongju.py", "shenzhuakuai_gongju.py", "wangye_keduxing_adapter.py"],
        "decision": "limited_readability_rebuild",
        "v2_mapping": ["web_readability_extract"],
        "imported_now": True,
        "reason": "真实联网搜索需独立 Provider/网络系统；本轮只补已给 HTML/文本的可读性提取。",
    },
    {
        "v1_area": "学习精通",
        "source_examples": ["xuexi_jingtong_gongju.py", "tiangong_xuexi_jingtong_zhijue.py"],
        "decision": "pure_planning_rebuild",
        "v2_mapping": ["learning_master_plan"],
        "imported_now": True,
        "reason": "先导入学习分级、可信度、冲突仲裁、实践转化链路；不自动资产化。",
    },
    {
        "v1_area": "Tool/Skill 生产标准",
        "source_examples": ["tool_skill_shengchan_gongju.py", "artifacts/zhishi/skill_versions.jsonl"],
        "decision": "pure_planning_rebuild",
        "v2_mapping": ["tool_skill_blueprint"],
        "imported_now": True,
        "reason": "只产出草案和测试矩阵；不注册、不热加载、不绕过 Runtime。",
    },
    {
        "v1_area": "截图视觉",
        "source_examples": ["jietu_adapter.py"],
        "decision": "defer_frontend_or_desktop_system",
        "v2_mapping": ["frontend/desktop screenshot connector pending"],
        "imported_now": False,
        "reason": "需要桌面/前端真实截图源；本轮不伪造视觉能力。",
    },
    {
        "v1_area": "自我迭代/心流/主动驱动",
        "source_examples": ["tiangong_ziwo_diedai.py", "tiangong_shenshu_zhudong_qudong.py", "tiangong_xinliu_*.py"],
        "decision": "dedup_to_existing_lifecycle_systems",
        "v2_mapping": ["lifecycle_coordinator", "self_iteration_route", "recovery_coordination", "governance_execution"],
        "imported_now": False,
        "reason": "v2 已有生命周期/自迭代/恢复系统；不得把 v1 loop 混入 Runtime。",
    },
]

RUNTIME_TOOLS = [
    "v1_clean_import_status",
    "v1_clean_import_audit",
    "v1_clean_import_guide",
    "workspace_text_search",
    "conversation_history_search",
    "task_pattern_search",
    "experience_mentor_search",
    "document_text_extract",
    "web_readability_extract",
    "learning_master_plan",
    "tool_skill_blueprint",
]


def _hint(next_tool: str, reason: str, confidence: float = 0.85, options: list[str] | None = None) -> dict[str, Any]:
    return {
        "next_tool": next_tool,
        "reason": reason,
        "confidence": confidence,
        "options": options or [],
        "llm_final_decision_required": True,
    }


def _envelope(tool: str, summary: str, result: dict[str, Any], *, status: str = "ok", risk_level: str = "A1", next_tool: str = "v1_clean_import_guide", reason: str = "继续按 v2 纯净导入链路选择下一步。", evidence: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    return {
        "tool_name": tool,
        "status": status,
        "summary": summary,
        "risk_level": risk_level,
        "source_boundary": {
            "copied_v1_source": False,
            "imported_v1_module": False,
            "reused_v1_registry": False,
            "reused_v1_executor": False,
            "background_loop_started": False,
            "planner_or_subagent_can_override_llm": False,
        },
        "next_action_hint": _hint(next_tool, reason),
        "evidence": evidence or [],
        "result": result,
    }


def _workspace(root: str | Path) -> Path:
    p = Path(root or ".").expanduser().resolve()
    if not p.exists() or not p.is_dir():
        raise FileNotFoundError(f"workspace root not found: {p}")
    blocked = {Path("/"), Path.home().anchor and Path(Path.home().anchor)}
    if p in blocked:
        raise ValueError(f"blocked workspace root: {p}")
    return p


def _safe_rel_path(path: str) -> Path:
    normalized = str(path or "").replace("\\", "/").strip()
    if not normalized:
        raise ValueError("path must be non-empty")
    p = Path(normalized)
    if p.is_absolute() or any(part in {"..", ""} for part in p.parts):
        raise ValueError(f"unsafe relative path: {path}")
    return p


def _inside(root: Path, rel_or_abs: str | Path) -> Path:
    raw = Path(rel_or_abs)
    target = raw.resolve() if raw.is_absolute() else (root / _safe_rel_path(str(rel_or_abs))).resolve()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(f"path escapes workspace: {rel_or_abs}") from exc
    return target


def _rel(root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except Exception:
        return path.as_posix()


def _redact(text: str, limit: int = 1200) -> str:
    text = SECRET_RE.sub(lambda m: f"{m.group(1)}=***", str(text or ""))
    text = " ".join(text.replace("\x00", " ").split())
    return text[:limit]


def _tokens(query: str) -> list[str]:
    parts = re.split(r"\s+OR\s+|\s+or\s+|[，,；;\s]+", str(query or ""))
    out: list[str] = []
    for part in parts:
        item = part.strip().lower()
        if item and item not in out:
            out.append(item)
    return out


def _score_text(text: str, toks: list[str]) -> int:
    low = text.lower()
    return sum(low.count(tok) for tok in toks if tok)


def _safe_read_text(path: Path, max_bytes: int = 1_500_000) -> str:
    data = path.read_bytes()[:max_bytes]
    for enc in ("utf-8", "utf-8-sig", "gb18030", "latin-1"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _iter_text_files(root: Path, *, max_files: int = 800, include_docs: bool = True) -> Iterable[Path]:
    count = 0
    for current, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        for name in sorted(files):
            path = Path(current) / name
            ext = path.suffix.lower()
            if ext in (DOCUMENT_EXTENSIONS if include_docs else TEXT_EXTENSIONS):
                yield path
                count += 1
                if count >= max_files:
                    return


def _iter_json_records(path: Path) -> Iterable[tuple[int, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        for i, line in enumerate(_safe_read_text(path).splitlines(), 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield i, json.loads(line)
            except Exception:
                yield i, line
        return
    if suffix == ".json":
        text = _safe_read_text(path)
        try:
            data = json.loads(text)
        except Exception:
            yield 1, text
            return
        if isinstance(data, list):
            for i, item in enumerate(data, 1):
                yield i, item
        elif isinstance(data, dict):
            for i, (key, value) in enumerate(data.items(), 1):
                yield i, {key: value}
        else:
            yield 1, data
        return
    for i, line in enumerate(_safe_read_text(path).splitlines(), 1):
        if line.strip():
            yield i, line.strip()


def _object_text(obj: Any, limit: int = 4000) -> str:
    if isinstance(obj, str):
        return obj[:limit]
    try:
        return json.dumps(obj, ensure_ascii=False, default=str)[:limit]
    except Exception:
        return str(obj)[:limit]


def _hash_payload(payload: Any) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()[:16]


def _extract_docx(path: Path, max_chars: int) -> dict[str, Any]:
    paragraphs: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = [n for n in zf.namelist() if n.startswith("word/") and n.endswith(".xml")]
        for name in sorted(names):
            if name not in {"word/document.xml"} and not name.startswith("word/header") and not name.startswith("word/footer"):
                continue
            data = zf.read(name)
            try:
                root = ElementTree.fromstring(data)
            except ElementTree.ParseError:
                continue
            texts: list[str] = []
            for node in root.iter():
                if node.tag.endswith("}t") and node.text:
                    texts.append(node.text)
            if texts:
                paragraphs.append("".join(texts))
            if sum(len(x) for x in paragraphs) >= max_chars:
                break
    text = "\n".join(p for p in paragraphs if p).strip()[:max_chars]
    return {"format": "docx", "text": text, "chars": len(text), "degraded": False}


def _extract_pdf_degraded(path: Path, max_chars: int) -> dict[str, Any]:
    raw = path.read_bytes()[: max(512_000, max_chars * 8)]
    # Lightweight fallback only: extract printable byte runs. This is not a full PDF parser.
    runs = re.findall(rb"[A-Za-z0-9 ,.;:!?()\[\]{}_/\\\-]{8,}", raw)
    text = "\n".join(chunk.decode("latin-1", errors="ignore") for chunk in runs)
    text = _redact(text, max_chars)
    return {
        "format": "pdf",
        "text": text[:max_chars],
        "chars": len(text[:max_chars]),
        "degraded": True,
        "note": "PDF 使用标准库降级文本抽取；正式高质量 PDF/OCR 需独立文档系统接入解析器。",
    }


def _depth_for_goal(goal: str) -> str:
    low = goal.lower()
    if any(w in low for w in ("长期", "体系", "资产", "工具", "skill", "能力包", "专家级", "精通", "l5")):
        return "L5"
    if any(w in low for w in ("精品", "高端", "范式", "最佳实践", "系统学习", "l4")):
        return "L4"
    if any(w in low for w in ("实践", "项目", "验证", "会用", "l3")):
        return "L3"
    if any(w in low for w in ("了解", "入门", "快速", "l1")):
        return "L1"
    return "L2"


def _risk_level(text: str, default: str = "A1") -> str:
    rules = [
        ("A5", ["rm -rf", "删除全部", "格式化", "支付", "转账", "群发", "审批通过"]),
        ("A4", ["密钥", "密码", "secret", "token", "覆盖", "外发", "删除", "数据库"]),
        ("A3", ["写文件", "修改文件", "终端", "shell", "命令", "部署", "发布"]),
        ("A2", ["联网", "api", "飞书", "微信", "搜索", "工具生产", "skill"]),
    ]
    low = text.lower()
    for level, words in rules:
        if any(w.lower() in low or w in text for w in words):
            return level
    return default


def v1_clean_import_status() -> dict[str, Any]:
    imported = [d for d in DEDUP_DECISIONS if d["imported_now"]]
    deferred = [d for d in DEDUP_DECISIONS if not d["imported_now"]]
    return _envelope(
        "v1_clean_import_status",
        "v1 clean import layer is registered as an independent v2-native subsystem.",
        {
            "bundle": V1_BUNDLE_FINGERPRINT,
            "runtime_tools": RUNTIME_TOOLS,
            "imported_area_count": len(imported),
            "dedup_or_deferred_area_count": len(deferred),
            "tool_count": len(RUNTIME_TOOLS),
            "skill": "skill.v1_clean_import_workflow",
            "authority_model": "LLM 主脑；本层只提供只读检索、草案、证据和 next_action_hint。",
            "commands": {
                "status": "v1-import status",
                "audit": "v1-import audit",
                "guide": "v1-import guide",
                "workspace_search": "v1-import search <query>",
                "conversation_search": "v1-import conversation <query>",
                "experience_search": "v1-import experience <query>",
                "document_extract": "v1-import document <path>",
                "learning_plan": "v1-import learning <goal>",
                "tool_skill_blueprint": "v1-import tool-skill <goal>",
            },
        },
        risk_level="A2",
        next_tool="v1_clean_import_guide",
        reason="查看可用工具和路由卡。",
    )


def v1_clean_import_audit() -> dict[str, Any]:
    return _envelope(
        "v1_clean_import_audit",
        "v1 bundle has been deduplicated against v2 and imported only as clean v2-native semantics.",
        {
            "bundle": V1_BUNDLE_FINGERPRINT,
            "decisions": DEDUP_DECISIONS,
            "imported_runtime_tools": RUNTIME_TOOLS,
            "no_pollution_assertions": {
                "copied_v1_source": False,
                "import_v1": False,
                "reuse_v1_registry": False,
                "reuse_v1_executor": False,
                "reuse_v1_provider": False,
                "monkey_patch": False,
                "background_loop": False,
            },
            "code_x_boundary": "Code-X remains focused on coding exoskeleton. Non-Code-X v1 semantics live in this independent clean import layer.",
            "llm_skill": "tiangong_agent_runtime/skills/v1_clean_import_workflow/SKILL.md",
        },
        risk_level="A2",
        next_tool="v1_clean_import_guide",
        reason="审计通过后，让 LLM 读取独立系统使用卡。",
    )


def v1_clean_import_guide(domain: str = "all") -> dict[str, Any]:
    cards = [
        {
            "tool": "workspace_text_search",
            "domain": "file_search",
            "when_to_use": "在非代码材料、文档、配置、日志中做只读关键词搜索；代码语义搜索仍优先 Code-X semantic_code_search。",
            "required_inputs": {"query": "关键词，支持空格/OR", "root": "workspace 根目录，默认 ."},
            "next_action": "document_text_extract 或 experience_mentor_search",
        },
        {
            "tool": "conversation_history_search",
            "domain": "conversation_search",
            "when_to_use": "用户说‘上次/之前/记得吗/我们聊过’时，从本地会话/Runtime 留痕文件只读搜索摘要。",
            "required_inputs": {"query": "搜索词", "root": "workspace 根目录，默认 ."},
            "next_action": "task_pattern_search 或 handoff_digest",
        },
        {
            "tool": "task_pattern_search",
            "domain": "task_reuse",
            "when_to_use": "新任务类似历史任务，需要‘先抄再改’复用工具链/决策依据。",
            "required_inputs": {"query": "任务目标/摘要/工具名", "root": "workspace 根目录，默认 ."},
            "next_action": "v1_clean_import_guide 或 Code-X/Runtime 对应执行链",
        },
        {
            "tool": "experience_mentor_search",
            "domain": "experience_search",
            "when_to_use": "需要加载可传承经验、SKILL.md、方法材料或历史留痕。",
            "required_inputs": {"query": "经验关键词，可为空列出", "root": "workspace 根目录，默认 ."},
            "next_action": "learning_master_plan 或 tool_skill_blueprint",
        },
        {
            "tool": "document_text_extract",
            "domain": "document_extract",
            "when_to_use": "读取 txt/md/json/jsonl/csv/docx/pdf 等材料，输出可审计摘要和降级标记。",
            "required_inputs": {"path": "workspace 内相对路径"},
            "next_action": "workspace_text_search 或 learning_master_plan",
        },
        {
            "tool": "web_readability_extract",
            "domain": "web_readability",
            "when_to_use": "用户已经提供网页 HTML/正文时做可读性清洗；不联网抓取。",
            "required_inputs": {"html_or_text": "网页 HTML 或正文"},
            "next_action": "learning_master_plan 或 handoff_digest",
        },
        {
            "tool": "learning_master_plan",
            "domain": "learning_mastery",
            "when_to_use": "学习软件/API/资料/方法，并决定 L1-L5 深度、可信度、实践转化和资产化候选。",
            "required_inputs": {"goal": "学习目标", "sources": "可选来源/材料列表"},
            "next_action": "tool_skill_blueprint if L5 else experience_mentor_search",
        },
        {
            "tool": "tool_skill_blueprint",
            "domain": "tool_skill_production",
            "when_to_use": "把能力沉淀为 ToolManifest/SkillVersion/测试矩阵草案；不注册、不执行。",
            "required_inputs": {"goal": "工具或 Skill 生产目标", "asset_type": "tool/skill/ability"},
            "next_action": "queue_skill_candidates 或 queue_tool_production_requests",
        },
    ]
    domain = (domain or "all").strip().lower()
    selected = [c for c in cards if domain in {"all", "auto", c["domain"], c["tool"]}]
    if not selected:
        selected = cards
    phase = {
        "start": _hint("v1_clean_import_audit", "先确认去重/无污染导入状态。"),
        "need_context": _hint("conversation_history_search", "需要历史上下文时搜索本地会话摘要。"),
        "need_reuse": _hint("task_pattern_search", "需要复用历史任务链时先抄作业。"),
        "need_material": _hint("document_text_extract", "材料是文件时先提取文本。"),
        "need_learning": _hint("learning_master_plan", "学习类目标先分级。"),
        "need_asset": _hint("tool_skill_blueprint", "要沉淀工具/Skill 时只生成草案和测试矩阵。"),
    }
    return _envelope(
        "v1_clean_import_guide",
        "v1 clean import guide returned LLM-facing usage cards.",
        {"domain": domain, "tool_usage_cards": selected, "phase_to_next_action": phase, "commands": v1_clean_import_status()["result"]["commands"]},
        risk_level="A2",
        next_tool=selected[0]["tool"] if selected else "v1_clean_import_audit",
        reason="按任务类型调用对应只读/草案工具。",
    )


def workspace_text_search(query: str, root: str | Path = ".", limit: int = 8, max_files: int = 800) -> dict[str, Any]:
    root_path = _workspace(root)
    toks = _tokens(query)
    if not toks:
        return _envelope("workspace_text_search", "查询为空。", {"hits": [], "query": query}, status="failed", risk_level="A1", next_tool="v1_clean_import_guide", reason="补充关键词后重试。")
    hits: list[dict[str, Any]] = []
    scanned = 0
    for path in _iter_text_files(root_path, max_files=max_files):
        scanned += 1
        try:
            if path.suffix.lower() == ".docx":
                text = _extract_docx(path, 6000).get("text", "")
            elif path.suffix.lower() == ".pdf":
                text = _extract_pdf_degraded(path, 6000).get("text", "")
            else:
                text = _safe_read_text(path, 700_000)
        except Exception:
            continue
        score = _score_text(text, toks)
        if score <= 0:
            continue
        first_line = 1
        lines = text.splitlines()
        for idx, line in enumerate(lines, 1):
            if any(tok in line.lower() for tok in toks):
                first_line = idx
                break
        hits.append({
            "score": score,
            "path": _rel(root_path, path),
            "line": first_line,
            "summary": _redact("\n".join(lines[max(0, first_line-2): first_line+2]), 600),
        })
    hits.sort(key=lambda x: (-x["score"], x["path"]))
    return _envelope(
        "workspace_text_search",
        f"workspace text search scanned {scanned} files and found {len(hits)} hits.",
        {"query": query, "tokens": toks, "scanned_files": scanned, "hit_count": len(hits), "hits": hits[: max(1, min(int(limit), 20))]},
        risk_level="A1",
        next_tool="document_text_extract" if hits else "v1_clean_import_guide",
        reason="命中文件后可提取全文；未命中则调整关键词或转经验搜索。",
        evidence=[{"kind": "workspace", "path": str(root_path)}],
    )


def _conversation_candidates(root_path: Path) -> list[Path]:
    candidates: list[Path] = []
    env = os.environ.get("TIANGONG_HUIHUA_DIR")
    if env:
        candidates.append(Path(env).expanduser())
    candidates.extend([
        root_path / ".tiangong" / "huihua",
        root_path / ".tiangong" / "conversations",
        root_path / ".tiangong_runtime" / "runtime_store.json",
        root_path / "artifacts" / "runtime_feedback" / "renwu_liuhen.jsonl",
        root_path / "artifacts" / "runtime_feedback" / "context_compression.jsonl",
        root_path / "reports",
    ])
    out: list[Path] = []
    seen: set[str] = set()
    for candidate in candidates:
        try:
            p = candidate.resolve()
            if not p.exists():
                continue
            files = [p] if p.is_file() else []
            if p.is_dir():
                for pat in ("*.jsonl", "*.json", "*.txt", "*.md"):
                    files.extend(sorted(p.glob(pat))[:200])
            for file in files:
                key = str(file)
                if file.is_file() and key not in seen:
                    seen.add(key)
                    out.append(file)
        except Exception:
            continue
    return out[:500]


def conversation_history_search(query: str, root: str | Path = ".", limit: int = 5) -> dict[str, Any]:
    root_path = _workspace(root)
    toks = _tokens(query)
    if not toks:
        return _envelope("conversation_history_search", "查询为空。", {"hits": [], "query": query}, status="failed", next_tool="v1_clean_import_guide", reason="补充会话关键词后重试。")
    hits: list[dict[str, Any]] = []
    scanned_files = scanned_records = 0
    for path in _conversation_candidates(root_path):
        scanned_files += 1
        for line_no, record in _iter_json_records(path):
            scanned_records += 1
            text = _object_text(record, 3000)
            score = _score_text(text, toks)
            if score > 0:
                hits.append({"score": score, "source": _rel(root_path, path), "line": line_no, "summary": _redact(text, 700)})
            if scanned_records >= 6000:
                break
        if scanned_records >= 6000:
            break
    hits.sort(key=lambda x: (-x["score"], x["source"], x["line"]))
    return _envelope(
        "conversation_history_search",
        f"conversation history search scanned {scanned_files} files and found {len(hits)} hits.",
        {"query": query, "hit_count": len(hits), "scanned_files": scanned_files, "scanned_records": scanned_records, "hits": hits[: max(1, min(int(limit), 20))]},
        risk_level="A1",
        next_tool="task_pattern_search" if hits else "experience_mentor_search",
        reason="历史会话命中后可复用任务模式；未命中则搜经验库。",
    )


def task_pattern_search(query: str, root: str | Path = ".", limit: int = 5, days: int = 90, success_only: bool = True) -> dict[str, Any]:
    root_path = _workspace(root)
    toks = _tokens(query)
    candidate_files = [
        root_path / "artifacts" / "runtime_feedback" / "renwu_liuhen.jsonl",
        root_path / "reports" / "handoff.jsonl",
        root_path / ".tiangong_runtime" / "runtime_store.json",
    ]
    records: list[dict[str, Any]] = []
    scanned = 0
    for path in candidate_files:
        if not path.exists() or not path.is_file():
            continue
        for line_no, record in _iter_json_records(path):
            scanned += 1
            text = _object_text(record, 4000)
            score = _score_text(text, toks) if toks else 1
            if score <= 0:
                continue
            if success_only and isinstance(record, Mapping):
                status = str(record.get("status") or record.get("zhuangtai") or record.get("state") or "").lower()
                if status and status not in {"completed", "success", "ok", "passed", "done", "完成"}:
                    continue
            if isinstance(record, Mapping):
                title = str(record.get("mubiao") or record.get("goal") or record.get("title") or record.get("summary") or "")
                steps_raw = record.get("steps") or record.get("buzhou") or record.get("tool_chain") or []
            else:
                title, steps_raw = text[:120], []
            if isinstance(steps_raw, list):
                chain = " → ".join(str((s.get("tool_name") or s.get("gongju_ming") or s) if isinstance(s, Mapping) else s)[:60] for s in steps_raw[:12])
            else:
                chain = str(steps_raw)[:500]
            records.append({
                "score": score,
                "source": _rel(root_path, path),
                "line": line_no,
                "title": _redact(title, 220),
                "reusable_chain": chain,
                "summary": _redact(text, 700),
            })
    records.sort(key=lambda x: (-x["score"], x["source"], x["line"]))
    return _envelope(
        "task_pattern_search",
        f"task pattern search scanned {scanned} records and found {len(records)} reusable candidates.",
        {"query": query, "days": days, "success_only": success_only, "hit_count": len(records), "patterns": records[: max(1, min(int(limit), 20))]},
        risk_level="A1",
        next_tool="v1_clean_import_guide",
        reason="由 LLM 判断是否复用历史链路；工具不自动执行。",
    )


def _skill_dirs(root_path: Path) -> list[Path]:
    candidates = [root_path / ".linyuanzhe" / "skills", root_path / "tiangong_agent_runtime" / "skills", root_path / "skills", Path.home() / ".tiangong" / "skills"]
    out: list[Path] = []
    for base in candidates:
        try:
            if base.exists() and base.is_dir():
                out.extend([p for p in sorted(base.iterdir()) if p.is_dir() and (p / "SKILL.md").exists()])
        except Exception:
            continue
    return out


def experience_mentor_search(query: str = "", root: str | Path = ".", limit: int = 5) -> dict[str, Any]:
    root_path = _workspace(root)
    toks = _tokens(query)
    hits: list[dict[str, Any]] = []
    for skill_dir in _skill_dirs(root_path):
        skill_md = skill_dir / "SKILL.md"
        try:
            text = _safe_read_text(skill_md, 600_000)
        except Exception:
            continue
        score = _score_text(text + " " + skill_dir.name, toks) if toks else 1
        if score <= 0:
            continue
        title = ""
        for line in text.splitlines():
            clean = line.strip().lstrip("# ").strip()
            if clean:
                title = clean[:120]
                break
        paragraph = "\n".join(text.splitlines()[:8])
        hits.append({"score": score, "name": skill_dir.name, "title": title or skill_dir.name, "path": _rel(root_path, skill_md), "summary": _redact(paragraph, 800)})
    # Fallback: task/conversation records as experience evidence.
    if not hits and toks:
        conv = conversation_history_search(query, root_path, limit=limit)
        for item in conv.get("result", {}).get("hits", [])[:limit]:
            hits.append({"score": item.get("score", 1), "name": f"record:{item.get('source')}", "title": "历史留痕经验", "path": item.get("source"), "summary": item.get("summary")})
    hits.sort(key=lambda x: (-int(x.get("score", 0)), str(x.get("path", ""))))
    return _envelope(
        "experience_mentor_search",
        f"experience mentor search found {len(hits)} reusable experience entries.",
        {"query": query, "hit_count": len(hits), "experiences": hits[: max(1, min(int(limit), 20))]},
        risk_level="A1",
        next_tool="learning_master_plan" if hits else "tool_skill_blueprint",
        reason="找到经验后可进入学习精通或资产草案。",
    )


def document_text_extract(path: str, root: str | Path = ".", max_chars: int = 20000) -> dict[str, Any]:
    root_path = _workspace(root)
    target = _inside(root_path, path)
    if not target.exists() or not target.is_file():
        return _envelope("document_text_extract", "目标文档不存在。", {"path": path}, status="failed", risk_level="A1", next_tool="workspace_text_search", reason="先搜索或确认路径。")
    ext = target.suffix.lower()
    max_chars = max(1000, min(int(max_chars), 200_000))
    try:
        if ext == ".docx":
            extracted = _extract_docx(target, max_chars)
        elif ext == ".pdf":
            extracted = _extract_pdf_degraded(target, max_chars)
        elif ext in {".csv", ".tsv"}:
            delimiter = "\t" if ext == ".tsv" else ","
            rows: list[list[str]] = []
            with target.open("r", encoding="utf-8", errors="replace", newline="") as f:
                for row in csv.reader(f, delimiter=delimiter):
                    rows.append(row)
                    if len(rows) >= 60:
                        break
            text = "\n".join(" | ".join(cell for cell in row) for row in rows)[:max_chars]
            extracted = {"format": ext.lstrip("."), "text": text, "rows_sampled": len(rows), "chars": len(text), "degraded": False}
        elif ext in DOCUMENT_EXTENSIONS or not ext:
            text = _safe_read_text(target, max_chars * 4)
            extracted = {"format": ext.lstrip(".") or "text", "text": _redact(text, max_chars), "chars": min(len(text), max_chars), "degraded": False}
        else:
            return _envelope("document_text_extract", f"不支持的文档格式：{ext}", {"path": path, "extension": ext}, status="failed", next_tool="v1_clean_import_guide", reason="换用受支持的文档或独立文档系统。")
    except Exception as exc:
        return _envelope("document_text_extract", f"文档提取失败：{type(exc).__name__}: {exc}", {"path": path, "error": str(exc)}, status="failed", next_tool="v1_clean_import_guide", reason="保留失败证据并考虑降级读取。")
    sample = extracted.get("text", "")[:1200]
    return _envelope(
        "document_text_extract",
        f"document text extracted from {_rel(root_path, target)}.",
        {"path": _rel(root_path, target), "size_bytes": target.stat().st_size, "sha256_16": hashlib.sha256(target.read_bytes()).hexdigest()[:16], **extracted, "summary": _redact(sample, 1200)},
        risk_level="A1",
        next_tool="learning_master_plan",
        reason="提取材料后可进入学习/摘要/经验沉淀。",
        evidence=[{"kind": "file", "path": _rel(root_path, target), "note": "read_only_extract"}],
    )


def web_readability_extract(html_or_text: str = "", url: str = "", max_chars: int = 12000) -> dict[str, Any]:
    raw = str(html_or_text or "")
    if not raw and url:
        return _envelope(
            "web_readability_extract",
            "未执行联网抓取；仅支持已提供 HTML/正文的可读性清洗。",
            {"url": url, "degraded": True, "requires_external_web_fetcher": True},
            status="skipped",
            risk_level="A1",
            next_tool="v1_clean_import_guide",
            reason="真实联网搜索/抓取需独立搜索网页系统接入 Provider。",
        )
    if not raw:
        return _envelope("web_readability_extract", "缺少 HTML 或正文。", {"text": ""}, status="failed", risk_level="A1")
    text = re.sub(r"(?is)<(script|style|noscript).*?>.*?</\1>", " ", raw)
    text = re.sub(r"(?is)<br\s*/?>", "\n", text)
    text = re.sub(r"(?is)</p>|</div>|</h[1-6]>", "\n", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = html.unescape(text)
    lines = [" ".join(line.split()) for line in text.splitlines()]
    lines = [line for line in lines if len(line) >= 2]
    counter = Counter(TOKEN_RE.findall(" ".join(lines[:200]).lower()))
    cleaned = "\n".join(lines)[: max(1000, min(int(max_chars), 100_000))]
    return _envelope(
        "web_readability_extract",
        "web readability text cleaned from supplied content; no network fetch performed.",
        {"url": url, "chars": len(cleaned), "text": _redact(cleaned, max_chars), "top_terms": counter.most_common(20), "network_fetch_performed": False},
        risk_level="A1",
        next_tool="learning_master_plan",
        reason="清洗网页正文后可进入学习精通或材料总结。",
    )


def learning_master_plan(goal: str, sources: list[str] | str | None = None, target_depth: str = "auto") -> dict[str, Any]:
    goal = str(goal or "").strip()
    if not goal:
        return _envelope("learning_master_plan", "缺少学习目标。", {"goal": goal}, status="failed", risk_level="A2", next_tool="v1_clean_import_guide", reason="补充学习目标。")
    depth = target_depth if target_depth and target_depth.lower() != "auto" else _depth_for_goal(goal)
    if isinstance(sources, str):
        source_items = [x.strip() for x in re.split(r"[\n,，;；]+", sources) if x.strip()]
    else:
        source_items = [str(x) for x in (sources or [])]
    scored: list[dict[str, Any]] = []
    for src in source_items[:20]:
        low = src.lower()
        score = 0.55
        if any(w in low for w in ("official", "docs", "manual", "readme", "官方", "规范")):
            score += 0.25
        if any(w in low for w in ("pytest", "运行结果", "实测", "benchmark", "验证")):
            score += 0.18
        if any(w in low for w in ("论坛", "自媒体", "搬运", "未知")):
            score -= 0.18
        if any(w in low for w in ("deprecated", "旧版", "过时")):
            score -= 0.22
        score = max(0.1, min(0.98, score))
        scored.append({"source": src[:240], "score": round(score, 2), "level": "高可信" if score >= 0.78 else "中可信" if score >= 0.55 else "低可信"})
    avg = round(sum(x["score"] for x in scored) / len(scored), 2) if scored else None
    chains = {
        "L1": ["概念边界", "最小示例", "适用/不适用条件"],
        "L2": ["常规用法", "常见坑", "小练习"],
        "L3": ["任务实践", "失败归因", "验收清单"],
        "L4": ["精品案例", "多源交叉验证", "高质量范式抽取", "实践验证"],
        "L5": ["学习治理", "精品范式", "实践转化", "Tool/Skill 草案", "Runtime 复检", "候选资产化"],
    }
    ask_user = depth in {"L4", "L5"} and len(goal) < 80
    result = {
        "goal": goal,
        "depth": depth,
        "depth_chain": chains.get(depth, chains["L2"]),
        "source_reliability": {"average": avg, "items": scored},
        "clarification_needed": ask_user,
        "clarification_questions": [
            "这次是只完成当前任务，还是要沉淀为长期可复用能力？",
            "精品方向更偏官方规范、工程实测、行业最佳实践，还是用户历史偏好？",
        ] if ask_user else [],
        "assetization_policy": "只进入候选；未经实践验证、Tool/Skill 标准验收与 Runtime 复检，不注册正式资产。",
        "recommended_outputs": ["学习摘要", "关键步骤", "风险/冲突点", "实践验证", "可沉淀候选"],
        "route": ["document_text_extract/web_readability_extract", "learning_master_plan", "experience_mentor_search", "tool_skill_blueprint" if depth == "L5" else "handoff_digest"],
    }
    return _envelope(
        "learning_master_plan",
        f"learning mastery plan generated at depth {depth}.",
        result,
        risk_level="A2",
        next_tool="tool_skill_blueprint" if depth == "L5" else "experience_mentor_search",
        reason="L5 目标进入资产草案；非 L5 可先复用经验或交付摘要。",
    )


def tool_skill_blueprint(goal: str, asset_type: str = "tool+skill", name_hint: str = "") -> dict[str, Any]:
    goal = str(goal or "").strip()
    name_hint = str(name_hint or "").strip()
    if not goal and not name_hint:
        return _envelope("tool_skill_blueprint", "缺少 Tool/Skill 生产目标。", {"goal": goal}, status="failed", risk_level="A2", next_tool="v1_clean_import_guide", reason="补充目标后重试。")
    text = f"{goal} {name_hint} {asset_type}"
    risk = _risk_level(text, default="A2")
    slug_source = name_hint or goal[:40] or "tool_skill"
    slug = re.sub(r"[^0-9A-Za-z_]+", "_", slug_source).strip("_").lower()[:48] or "tool_skill_candidate"
    tool_name = slug if not slug.startswith("tool_") else slug[5:]
    scenarios = [x[:32] for x in re.split(r"[，,。；;、\n\s]+", goal) if len(x.strip()) >= 2][:16]
    test_matrix = [
        {"case": "schema_required_fields", "purpose": "输入输出契约字段完整", "must_pass": True},
        {"case": "missing_input_error", "purpose": "缺参返回结构化错误", "must_pass": True},
        {"case": "dry_run_default", "purpose": "默认不产生副作用", "must_pass": True},
        {"case": "idempotency", "purpose": "同一请求不重复执行副作用", "must_pass": True},
        {"case": "runtime_boundary", "purpose": "Skill 只读，Tool 经 Runtime 调度", "must_pass": True},
        {"case": "a5_confirmation", "purpose": "A5 生成确认票据而非自动执行", "must_pass": risk == "A5"},
        {"case": "secret_redaction", "purpose": "疑似密钥不全文输出", "must_pass": True},
        {"case": "failure_visible", "purpose": "异常路径可见且可回放", "must_pass": True},
    ]
    manifest = {
        "tool_id": f"tool_{tool_name}",
        "tool_name": tool_name,
        "version": "0.1.0-draft-clean-import",
        "description": f"面向【{goal[:80] or name_hint}】的 v2 原生工具草案。",
        "input_schema": {
            "type": "object",
            "properties": {
                "目标": {"type": "string", "description": "用户目标或任务说明"},
                "输入材料": {"type": "string", "description": "文本、路径、ID 或摘要"},
                "dry_run": {"type": "boolean", "description": "默认 true；只生成预案，不执行副作用"},
            },
            "required": ["目标"],
        },
        "output_schema": {"type": "object", "required": ["status", "summary", "data", "risk_level"]},
        "risk_level_initial": risk,
        "side_effect_policy": "draft_only" if risk in {"A0", "A1", "A2"} else "runtime_planned_audited",
        "status": "draft_only_not_registered",
    }
    skill = {
        "skill_name": name_hint or f"{tool_name}_skill",
        "status": "draft_only_not_activated",
        "applicable_scenarios": scenarios,
        "procedure_steps": ["归一目标", "设计输入/输出契约", "补齐风险边界", "生成最小验证用例", "进入 Runtime 候选审查"],
        "validation_steps": ["Skill 不执行动作", "不得编造事实", "必须包含失败处理", "工具注册需另过 Runtime 复检"],
        "quality_score_target": 0.92,
    }
    result = {
        "goal": goal,
        "asset_type": asset_type,
        "risk_level": risk,
        "requires_confirmation": risk == "A5",
        "tool_manifest_draft": manifest,
        "skill_version_draft": skill,
        "test_matrix": test_matrix,
        "acceptance_gate": "所有 must_pass=True 通过，且质量评分 >= 0.85，才允许进入候选队列；不得直接注册。",
        "candidate_hash": _hash_payload({"manifest": manifest, "skill": skill, "test_matrix": test_matrix}),
    }
    return _envelope(
        "tool_skill_blueprint",
        "Tool/Skill blueprint generated as draft only; no registration performed.",
        result,
        risk_level=risk,
        next_tool="queue_skill_candidates" if "skill" in asset_type.lower() else "queue_tool_production_requests",
        reason="草案生成后交给 v2 现有候选队列，不直接注册。",
    )
