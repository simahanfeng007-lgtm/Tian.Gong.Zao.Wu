from __future__ import annotations

import ast
import json
import re
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", "node_modules", "venv", ".venv"}
TEXT_EXTS = {".py", ".txt", ".md", ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".sh", ".bat"}
SENSITIVE_AREAS = {"reports", "docs", "mock_data", "fixtures", "tests"}
provider_import_re = re.compile(r"^\s*(?:from\s+(openai|anthropic|deepseek|google\.generativeai|zhipuai|dashscope|volcenginesdk|cohere)\b|import\s+(openai|anthropic|deepseek|google\.generativeai|zhipuai|dashscope|volcenginesdk|cohere)\b)", re.M)
secret_regexes = {
    "real_sk_key_like": re.compile(r"(?i)\bsk-[A-Za-z0-9_\-]{12,}\b"),
    "bearer_token_like": re.compile(r"(?i)\bBearer\s+[A-Za-z0-9_\-\.]{12,}\b"),
    "api_key_equals_literal": re.compile(r"(?i)\bapi_key="),
    "provider_key_env_literal": re.compile(r"DEEPSEEK_API_KEY"),
    "raw_provider_endpoint_assignment": re.compile(r"(?i)\b(?:base_url|provider_url|api_base|endpoint)\s*[:=]\s*[\"']?https?://(?!127\.0\.0\.1|localhost)[^\s\"']+"),
}


def iter_files():
    for p in ROOT.rglob("*"):
        if not p.is_file() or any(part in SKIP_DIRS for part in p.parts):
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        yield p


def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")


def area(rel: Path) -> str:
    parts = set(rel.parts)
    return "sensitive_artifact" if parts & SENSITIVE_AREAS else "source_or_launcher"


def main() -> int:
    leak_hits = []
    marker_refs = []
    import_hits = []
    bare_hits = []
    for p in iter_files():
        rel = p.relative_to(ROOT)
        txt = read(p)
        ar = area(rel)
        for name, rx in secret_regexes.items():
            for m in rx.finditer(txt):
                item = {"file": str(rel), "line": txt.count("\n", 0, m.start()) + 1, "pattern": name, "match": "<redacted>"}
                # In source code, redaction-rule marker strings are informational, not leaks. Real key-like and bearer are always leaks.
                if ar == "sensitive_artifact" or name in {"real_sk_key_like", "bearer_token_like", "raw_provider_endpoint_assignment"}:
                    leak_hits.append(item)
                else:
                    marker_refs.append(item)
        if p.suffix.lower() == ".py":
            for m in provider_import_re.finditer(txt):
                import_hits.append({"file": str(rel), "line": txt.count("\n", 0, m.start()) + 1, "import": m.group(1) or m.group(2)})
            try:
                tree = ast.parse(txt, filename=str(p))
            except SyntaxError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ExceptHandler) and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                    bare_hits.append({"file": str(rel), "line": getattr(node, "lineno", None), "kind": "except_pass"})
    result = {
        "checked_at": datetime.now().isoformat(timespec="seconds"),
        "secret_scan": {"ok": not leak_hits, "hit_count": len(leak_hits), "hits": leak_hits[:200]},
        "source_marker_reference_scan": {"ok": True, "hit_count": len(marker_refs), "note": "source redaction/config marker references only; not logged secrets", "hits": marker_refs[:100]},
        "provider_sdk_import_scan": {"ok": not import_hits, "hit_count": len(import_hits), "hits": import_hits[:200]},
        "bare_except_pass_scan": {"ok": not bare_hits, "hit_count": len(bare_hits), "hits": bare_hits[:200]},
    }
    out = ROOT / "reports" / "scan_l659.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: {"ok": v["ok"], "hit_count": v["hit_count"]} for k, v in result.items() if isinstance(v, dict) and "ok" in v}, ensure_ascii=False, indent=2))
    return 0 if result["secret_scan"]["ok"] and result["provider_sdk_import_scan"]["ok"] and result["bare_except_pass_scan"]["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
