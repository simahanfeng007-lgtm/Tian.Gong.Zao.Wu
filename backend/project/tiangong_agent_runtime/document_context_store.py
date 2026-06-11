"""L6.72.45 文档解析上下文、引用、追问与导出闭环。

边界：
- 只保存解析后的安全文本片段、表格/幻灯片/PDF 摘要、元信息和引用编号。
- 不保存 Office/PDF/图片/压缩包原始字节。
- 不把 stderr/raw tool result 投影到主会话。
- 导出文件仍由 WorkspaceGuard / ExecutionSpine / Audit 承接。
"""

from __future__ import annotations

import hashlib
import os
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable



def _state_root(workspace: Path, root_name: str = ".linyuanzhe/document_contexts") -> Path:
    override = os.environ.get("LINYUANZHE_STATE_DIR") or os.environ.get("TIANGONG_STATE_DIR")
    if override:
        return Path(override).expanduser().resolve() / root_name.replace(".linyuanzhe/", "")
    return workspace / root_name

CONTEXT_SCHEMA = "tiangong.l6_72_45.document_context.v1"
_INDEX_SCHEMA = "tiangong.l6_72_45.document_context_index.v1"
_MAX_BLOCK_TEXT = 1600
_MAX_CONTEXT_BLOCKS = 120
_MAX_EXPORT_BLOCKS = 80


def safe_text(value: Any, limit: int = 2000) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\x00", "")
    text = "".join(ch for ch in text if ch.isprintable() or ch in "\n\r\t")
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = text.strip()
    if len(text) > limit:
        return text[: max(0, limit - 1)].rstrip() + "…"
    return text


def digest(value: Any, length: int = 16) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode("utf-8", errors="ignore")).hexdigest()[:length]


def path_digest(path: Any) -> str:
    try:
        normalized = str(Path(str(path or "")).expanduser().resolve(strict=False))
    except Exception:
        normalized = str(path or "")
    return digest(normalized.lower(), 16)


def context_dir(workspace: str | Path) -> Path:
    root = Path(workspace).expanduser().resolve()
    path = root / ".linyuanzhe" / "document_contexts"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _index_path(workspace: str | Path) -> Path:
    return context_dir(workspace) / "index.json"


def _context_path(workspace: str | Path, document_id: str) -> Path:
    clean = re.sub(r"[^a-zA-Z0-9_.-]", "_", str(document_id or ""))[:80]
    return context_dir(workspace) / f"{clean}.json"


def load_index(workspace: str | Path) -> dict[str, Any]:
    path = _index_path(workspace)
    if not path.exists():
        return {"schema": _INDEX_SCHEMA, "documents": {}, "path_index": {}, "last_document_id": ""}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data.setdefault("schema", _INDEX_SCHEMA)
            data.setdefault("documents", {})
            data.setdefault("path_index", {})
            data.setdefault("last_document_id", "")
            return data
    except Exception:
        pass
    return {"schema": _INDEX_SCHEMA, "documents": {}, "path_index": {}, "last_document_id": ""}


def save_index(workspace: str | Path, index: dict[str, Any]) -> None:
    path = _index_path(workspace)
    payload = {
        "schema": _INDEX_SCHEMA,
        "updated_at": datetime.now().isoformat(timespec="seconds"),
        "last_document_id": safe_text(index.get("last_document_id"), 120),
        "documents": dict(index.get("documents") or {}),
        "path_index": dict(index.get("path_index") or {}),
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _document_id_for_result(result: dict[str, Any]) -> str:
    payload = {
        "file_path_digest": path_digest(result.get("file_path")),
        "file_name": result.get("file_name"),
        "size_bytes": result.get("size_bytes"),
        "summary": safe_text(result.get("summary"), 240),
    }
    return f"doc_{digest(payload, 16)}"


def _append_block(
    blocks: list[dict[str, Any]],
    *,
    kind: str,
    title: str,
    text: Any,
    local_id: str = "",
    meta: dict[str, Any] | None = None,
) -> None:
    body = safe_text(text, _MAX_BLOCK_TEXT)
    if not body:
        return
    key = body.lower()
    if any(item.get("text", "").lower() == key for item in blocks):
        return
    block_index = len(blocks) + 1
    local = local_id or f"sec{block_index}"
    blocks.append(
        {
            "local_id": safe_text(local, 80),
            "kind": safe_text(kind, 60),
            "title": safe_text(title, 160),
            "text": body,
            "meta": dict(meta or {}),
        }
    )


def _rows_to_text(rows: Iterable[Any], *, row_limit: int = 12, cell_limit: int = 90) -> str:
    lines: list[str] = []
    for idx, row in enumerate(rows):
        if idx >= row_limit:
            break
        if isinstance(row, (list, tuple)):
            line = " | ".join(safe_text(cell, cell_limit) for cell in row)
        else:
            line = safe_text(row, cell_limit)
        if line.strip(" |"):
            lines.append(line)
    return "\n".join(lines)


def build_citation_blocks(result: dict[str, Any]) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []

    for idx, item in enumerate(result.get("key_sections") or [], start=1):
        _append_block(blocks, kind="section", title=f"关键段落 {idx}", text=item, local_id=f"sec{idx}")

    for idx, page in enumerate(result.get("pages") or [], start=1):
        if isinstance(page, dict):
            page_index = page.get("index") or idx
            text = page.get("text") or page.get("content")
        else:
            page_index = idx
            text = page
        _append_block(
            blocks,
            kind="page",
            title=f"PDF 第 {page_index} 页",
            text=text,
            local_id=f"p{page_index}",
            meta={"page": page_index},
        )

    for sheet_index, sheet in enumerate(result.get("sheets") or [], start=1):
        if not isinstance(sheet, dict):
            continue
        name = safe_text(sheet.get("name") or f"Sheet{sheet_index}", 80)
        headers = [safe_text(x, 60) for x in (sheet.get("headers") or []) if safe_text(x, 60)]
        header = "表头：" + ", ".join(headers) if headers else ""
        rows_text = _rows_to_text(sheet.get("rows_preview") or [])
        body = "\n".join(x for x in (header, rows_text) if x)
        _append_block(blocks, kind="sheet", title=f"工作表 {name}", text=body, local_id=f"sheet{sheet_index}", meta={"sheet": name})

    for slide_index, slide in enumerate(result.get("slides") or [], start=1):
        if not isinstance(slide, dict):
            continue
        idx = slide.get("index") or slide_index
        text = "\n".join(safe_text(x, 220) for x in (slide.get("text") or []) if safe_text(x, 220))
        _append_block(blocks, kind="slide", title=f"幻灯片 {idx}", text=text, local_id=f"slide{idx}", meta={"slide": idx})

    for table_index, table in enumerate(result.get("tables") or [], start=1):
        if not isinstance(table, dict):
            continue
        body = _rows_to_text(table.get("rows_preview") or [])
        _append_block(blocks, kind="table", title=f"表格 {safe_text(table.get('name') or table_index, 80)}", text=body, local_id=f"table{table_index}")

    preview = safe_text(result.get("content_preview"), 8000)
    if preview:
        _append_block(blocks, kind="preview", title="正文预览", text=preview, local_id="preview")

    return blocks[:_MAX_CONTEXT_BLOCKS]


def build_document_context(result: dict[str, Any]) -> dict[str, Any]:
    document_id = safe_text(result.get("document_id") or _document_id_for_result(result), 80)
    blocks = build_citation_blocks(result)
    for block in blocks:
        local_id = block.get("local_id") or f"sec{len(blocks)}"
        block["citation_id"] = f"{document_id}#{local_id}"
    search_text = "\n".join(block.get("text", "") for block in blocks)
    return {
        "schema": CONTEXT_SCHEMA,
        "document_id": document_id,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "metadata": {
            "file_name": safe_text(result.get("file_name"), 180),
            "file_path_digest": path_digest(result.get("file_path")),
            "file_path": safe_text(result.get("file_path"), 500),
            "file_type": safe_text(result.get("file_type"), 80),
            "suffix": safe_text(result.get("suffix"), 20),
            "parser": safe_text(result.get("parser"), 120),
            "status": safe_text(result.get("status"), 40),
            "size_bytes": int(result.get("size_bytes") or 0),
            "summary": safe_text(result.get("summary"), 600),
        },
        "blocks": blocks,
        "search_text_digest": digest(search_text, 20),
        "raw_bytes_hidden": True,
        "safe_projection_only": True,
    }


def attach_context_fields(result: dict[str, Any], ctx: dict[str, Any]) -> dict[str, Any]:
    enriched = dict(result)
    document_id = safe_text(ctx.get("document_id"), 80)
    citation_blocks = [
        {
            "citation_id": block.get("citation_id"),
            "local_id": block.get("local_id"),
            "kind": block.get("kind"),
            "title": block.get("title"),
            "text": safe_text(block.get("text"), 360),
        }
        for block in (ctx.get("blocks") or [])[:24]
        if isinstance(block, dict)
    ]
    enriched["document_id"] = document_id
    enriched["citation_blocks"] = citation_blocks
    enriched["context_available"] = bool(citation_blocks)
    enriched["next_suggestions"] = [
        "可以继续追问该文档：指定关键词、页码、工作表、幻灯片编号或引用编号。",
        "可以使用 document_export 导出 md/txt/json 摘要与引用片段。",
        "需要修改原文时进入长链模式：先生成 document_rewrite_plan；明确 old_text/new_text 后用 document_apply_rewrite 生成修订副本/写回；需要撤销时用 document_rollback。",
    ]
    summary = str(enriched.get("human_readable_summary") or "")
    addendum = "\n".join(
        [
            "- 文档上下文：已建立，可追问 / 引用 / 导出。",
            f"- 文档 ID：{document_id}",
            f"- 引用片段：{len(citation_blocks)} 个。",
        ]
    )
    enriched["human_readable_summary"] = (summary.rstrip() + "\n" + addendum).strip() if summary else addendum
    return enriched


def save_document_context(workspace: str | Path, result: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    ctx = build_document_context(result)
    document_id = safe_text(ctx.get("document_id"), 80)
    _context_path(workspace, document_id).write_text(json.dumps(ctx, ensure_ascii=False, indent=2), encoding="utf-8")
    index = load_index(workspace)
    index.setdefault("documents", {})[document_id] = {
        "file_name": ctx.get("metadata", {}).get("file_name", ""),
        "file_type": ctx.get("metadata", {}).get("file_type", ""),
        "parser": ctx.get("metadata", {}).get("parser", ""),
        "created_at": ctx.get("created_at", ""),
        "citation_count": len(ctx.get("blocks") or []),
        "file_path_digest": ctx.get("metadata", {}).get("file_path_digest", ""),
    }
    digest_key = ctx.get("metadata", {}).get("file_path_digest", "")
    if digest_key:
        index.setdefault("path_index", {})[digest_key] = document_id
    index["last_document_id"] = document_id
    save_index(workspace, index)
    return ctx, attach_context_fields(result, ctx)


def load_document_context(workspace: str | Path, *, document_id: str = "", path: str | Path | None = None) -> dict[str, Any] | None:
    index = load_index(workspace)
    requested_id = safe_text(document_id, 100)
    if path and not requested_id:
        requested_id = str(index.get("path_index", {}).get(path_digest(path), ""))
    if not requested_id:
        requested_id = safe_text(index.get("last_document_id"), 100)
    if not requested_id:
        return None
    path_obj = _context_path(workspace, requested_id)
    if not path_obj.exists():
        return None
    try:
        data = json.loads(path_obj.read_text(encoding="utf-8"))
    except Exception:
        return None
    if isinstance(data, dict) and data.get("schema") == CONTEXT_SCHEMA:
        return data
    return None


def _query_terms(query: str) -> list[str]:
    text = safe_text(query, 400).lower()
    tokens = re.findall(r"[a-zA-Z0-9_\-]{2,}|[\u4e00-\u9fff]{1,}", text)
    terms: list[str] = []
    seen: set[str] = set()
    stop = {"帮我", "这个", "那个", "文档", "里面", "一下", "总结", "查询", "看看", "是否", "还有", "哪些", "什么"}
    for token in tokens:
        token = token.strip().lower()
        if not token or token in stop or token in seen:
            continue
        seen.add(token)
        terms.append(token)
        if len(terms) >= 12:
            break
    return terms


def _score_block(block: dict[str, Any], terms: list[str], raw_query: str) -> int:
    hay = "\n".join([str(block.get("title") or ""), str(block.get("text") or ""), str(block.get("local_id") or "")]).lower()
    if not terms:
        return 1
    score = 0
    for term in terms:
        if term in hay:
            score += 3 + hay.count(term)
    local_id = str(block.get("local_id") or "").lower()
    if local_id and local_id in raw_query.lower():
        score += 8
    return score


def query_document_context(ctx: dict[str, Any], query: str, *, top_k: int = 6) -> dict[str, Any]:
    terms = _query_terms(query)
    blocks = [block for block in (ctx.get("blocks") or []) if isinstance(block, dict)]
    scored = [(block, _score_block(block, terms, query)) for block in blocks]
    positives = [(block, score) for block, score in scored if score > 0]
    if not positives and blocks:
        positives = [(block, 1) for block in blocks[:top_k]]
    positives.sort(key=lambda item: (-item[1], str(item[0].get("local_id") or "")))
    limit = max(1, min(int(top_k or 6), 20))
    matches = []
    for block, score in positives[:limit]:
        matches.append(
            {
                "citation_id": block.get("citation_id"),
                "local_id": block.get("local_id"),
                "kind": block.get("kind"),
                "title": block.get("title"),
                "score": score,
                "text": safe_text(block.get("text"), 900),
            }
        )
    metadata = dict(ctx.get("metadata") or {})
    lines = ["【文档追问】"]
    lines.append(f"- 文件名：{metadata.get('file_name', '')}")
    lines.append(f"- 文档 ID：{ctx.get('document_id', '')}")
    lines.append(f"- 查询：{safe_text(query, 260)}")
    if not matches:
        lines.append("- 结果：未命中明显片段。建议换关键词、页码、工作表名或幻灯片编号。")
        status = "partial"
    else:
        lines.append(f"- 命中片段：{len(matches)} 个。")
        for idx, match in enumerate(matches[:6], start=1):
            lines.append(f"  {idx}. [{match.get('citation_id')}] {safe_text(match.get('title'), 120)}：{safe_text(match.get('text'), 180)}")
        status = "ok"
    lines.append("- 边界：回答只基于已解析安全片段，不包含原始二进制、stderr 或工具 raw result。")
    return {
        "status": status,
        "document_id": ctx.get("document_id", ""),
        "file_name": metadata.get("file_name", ""),
        "query": safe_text(query, 600),
        "terms": terms,
        "matches": matches,
        "answer_summary": "\n".join(lines),
        "raw_bytes_hidden": True,
        "safe_projection_only": True,
    }


def public_context_payload(ctx: dict[str, Any], *, max_blocks: int = _MAX_EXPORT_BLOCKS) -> dict[str, Any]:
    return {
        "schema": CONTEXT_SCHEMA,
        "document_id": ctx.get("document_id", ""),
        "created_at": ctx.get("created_at", ""),
        "metadata": dict(ctx.get("metadata") or {}),
        "blocks": [
            {
                "citation_id": block.get("citation_id"),
                "local_id": block.get("local_id"),
                "kind": block.get("kind"),
                "title": block.get("title"),
                "text": safe_text(block.get("text"), 1200),
            }
            for block in (ctx.get("blocks") or [])[:max_blocks]
            if isinstance(block, dict)
        ],
        "raw_bytes_hidden": True,
        "safe_projection_only": True,
    }


def render_context_markdown(ctx: dict[str, Any], query_result: dict[str, Any] | None = None) -> str:
    payload = public_context_payload(ctx)
    meta = payload.get("metadata", {})
    lines = [
        f"# 文档解析摘要：{safe_text(meta.get('file_name'), 180)}",
        "",
        f"- 文档 ID：{payload.get('document_id', '')}",
        f"- 文件类型：{safe_text(meta.get('file_type'), 80)}",
        f"- 解析方式：{safe_text(meta.get('parser'), 120)}",
        f"- 状态：{safe_text(meta.get('status'), 40)}",
        f"- 摘要：{safe_text(meta.get('summary'), 600)}",
        "- 边界：仅导出已解析安全片段与引用编号；不包含原始二进制、stderr 或工具 raw result。",
        "",
    ]
    if query_result:
        lines.extend(["## 查询命中", "", f"查询：{safe_text(query_result.get('query'), 300)}", ""])
        for match in query_result.get("matches") or []:
            lines.extend([f"### {safe_text(match.get('citation_id'), 120)} {safe_text(match.get('title'), 160)}", "", safe_text(match.get("text"), 1200), ""])
    lines.extend(["## 引用片段", ""])
    for block in payload.get("blocks") or []:
        lines.extend([f"### {safe_text(block.get('citation_id'), 120)} {safe_text(block.get('title'), 160)}", "", safe_text(block.get("text"), 1200), ""])
    return "\n".join(lines).rstrip() + "\n"


def render_context_text(ctx: dict[str, Any], query_result: dict[str, Any] | None = None) -> str:
    md = render_context_markdown(ctx, query_result=query_result)
    text = re.sub(r"^#+\s*", "", md, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def build_rewrite_plan(ctx: dict[str, Any], instruction: str, *, output_path: str = "", output_format: str = "") -> dict[str, Any]:
    query = query_document_context(ctx, instruction, top_k=8)
    metadata = dict(ctx.get("metadata") or {})
    steps = [
        "确认修改目标：输出新文件、覆盖原文件或只生成补丁建议。",
        "根据引用片段定位修改范围；未命中片段时先补充关键词或页码/工作表/幻灯片编号。",
        "生成改写方案与差异说明；不静默覆盖原文。",
        "需要真实写入时进入长链模式：明确 old_text/new_text 后调用 document_apply_rewrite；默认生成修订副本，覆盖前自动备份，并生成 document_rollback 回滚凭据。",
    ]
    lines = ["【文档修改计划】"]
    lines.append(f"- 文件名：{metadata.get('file_name', '')}")
    lines.append(f"- 文档 ID：{ctx.get('document_id', '')}")
    lines.append(f"- 修改要求：{safe_text(instruction, 400)}")
    if output_path:
        lines.append(f"- 建议输出路径：{safe_text(output_path, 260)}")
    if output_format:
        lines.append(f"- 建议输出格式：{safe_text(output_format, 80)}")
    lines.append("- 命中证据：")
    for match in (query.get("matches") or [])[:6]:
        lines.append(f"  - [{match.get('citation_id')}] {safe_text(match.get('title'), 100)}：{safe_text(match.get('text'), 160)}")
    lines.append("- 执行步骤：")
    for idx, step in enumerate(steps, start=1):
        lines.append(f"  {idx}. {step}")
    lines.append("- 下一步：若用户确认且修改单元明确，使用 document_apply_rewrite；如需撤销，使用 document_rollback operation_id。")
    lines.append("- 边界：本工具只生成修改计划，不直接写入、不覆盖、不绕过 QualityGate。")
    return {
        "status": "ok",
        "document_id": ctx.get("document_id", ""),
        "file_name": metadata.get("file_name", ""),
        "instruction": safe_text(instruction, 800),
        "output_path": safe_text(output_path, 500),
        "output_format": safe_text(output_format, 80),
        "evidence": query.get("matches") or [],
        "rewrite_steps": steps,
        "answer_summary": "\n".join(lines),
        "raw_bytes_hidden": True,
        "safe_projection_only": True,
    }
