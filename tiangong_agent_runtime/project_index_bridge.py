"""L6.16 项目感知与文件索引桥。

该桥属于外壳运行层：只扫描工作区内文件结构和安全元数据，不读取完整源码，
不写长期记忆，不触碰 tiangong_kernel 主体。它给 LLM 装甲提供“项目雷达”。
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from time import time
from typing import Any
import json

from .workspace_guard import WorkspaceGuard, WorkspaceViolation

EXCLUDED_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    ".idea",
    ".vscode",
}
SENSITIVE_NAMES = {".env", ".env.local", "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}
SENSITIVE_PARTS = {".ssh", ".gnupg", "credentials", "secrets", "secret", "tokens"}
KEY_FILE_NAMES = {
    "readme.md",
    "readme.txt",
    "pyproject.toml",
    "requirements.txt",
    "requirements-dev.txt",
    "setup.py",
    "setup.cfg",
    "pytest.ini",
    "tox.ini",
    "package.json",
    "tsconfig.json",
    "vite.config.ts",
    "vite.config.js",
    "dockerfile",
    "docker-compose.yml",
    "makefile",
    "license",
    "license.md",
    "uv.lock",
    "poetry.lock",
}
ENTRY_FILE_NAMES = {"run_agent.py", "main.py", "app.py", "cli.py", "__main__.py", "manage.py"}
CONFIG_SUFFIXES = {".toml", ".ini", ".cfg", ".json", ".yaml", ".yml"}
TEXT_SUFFIXES = {".py", ".md", ".txt", ".toml", ".json", ".yaml", ".yml", ".ini", ".cfg"}


@dataclass(frozen=True)
class ProjectFileRecord:
    path: str
    kind: str
    suffix: str
    size: int
    role: str = "ordinary"

    def public_dict(self) -> dict[str, Any]:
        return {"path": self.path, "kind": self.kind, "suffix": self.suffix, "size": self.size, "role": self.role}


@dataclass(frozen=True)
class ProjectIndexSnapshot:
    schema: str
    root: str
    scanned_at: float
    files_count: int
    dirs_count: int
    skipped_count: int
    key_files: list[str] = field(default_factory=list)
    entry_points: list[str] = field(default_factory=list)
    test_files: list[str] = field(default_factory=list)
    config_files: list[str] = field(default_factory=list)
    package_dirs: list[str] = field(default_factory=list)
    top_dirs: list[str] = field(default_factory=list)
    file_type_counts: dict[str, int] = field(default_factory=dict)
    sample_files: list[dict[str, Any]] = field(default_factory=list)
    risk_notes: list[str] = field(default_factory=list)
    truncated: bool = False

    def public_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "root": self.root,
            "scanned_at": self.scanned_at,
            "files_count": self.files_count,
            "dirs_count": self.dirs_count,
            "skipped_count": self.skipped_count,
            "key_files": list(self.key_files),
            "entry_points": list(self.entry_points),
            "test_files": list(self.test_files),
            "config_files": list(self.config_files),
            "package_dirs": list(self.package_dirs),
            "top_dirs": list(self.top_dirs),
            "file_type_counts": dict(self.file_type_counts),
            "sample_files": list(self.sample_files),
            "risk_notes": list(self.risk_notes),
            "truncated": self.truncated,
        }

    def summary_text(self) -> str:
        lines = [
            "L6.16 项目雷达扫描结果：",
            f"- root: {self.root}",
            f"- files: {self.files_count}",
            f"- dirs: {self.dirs_count}",
            f"- skipped: {self.skipped_count}",
            f"- key_files: {', '.join(self.key_files[:12]) or '<无>'}",
            f"- entry_points: {', '.join(self.entry_points[:12]) or '<无>'}",
            f"- test_files: {', '.join(self.test_files[:12]) or '<无>'}",
            f"- package_dirs: {', '.join(self.package_dirs[:12]) or '<无>'}",
            f"- file_types: {dict(list(self.file_type_counts.items())[:12])}",
        ]
        if self.truncated:
            lines.append("- truncated: true，扫描达到 max_files 上限。")
        if self.risk_notes:
            lines.append(f"- risk_notes: {'; '.join(self.risk_notes[:8])}")
        return "\n".join(lines)

    def planner_hint(self) -> str:
        lines = ["项目结构摘要（L6.16 只读项目雷达，不含完整源码/密钥）："]
        lines.append(f"- 根目录：{self.root}")
        lines.append(f"- 文件/目录数量：files={self.files_count}, dirs={self.dirs_count}, skipped={self.skipped_count}")
        if self.key_files:
            lines.append(f"- 关键文件：{', '.join(self.key_files[:12])}")
        if self.entry_points:
            lines.append(f"- 入口文件：{', '.join(self.entry_points[:10])}")
        if self.package_dirs:
            lines.append(f"- Python 包目录：{', '.join(self.package_dirs[:10])}")
        if self.test_files:
            lines.append(f"- 测试文件：{', '.join(self.test_files[:10])}")
        if self.config_files:
            lines.append(f"- 配置文件：{', '.join(self.config_files[:10])}")
        return "\n".join(lines)[:2400]


class ProjectIndexBridge:
    """当前进程内项目索引桥。"""

    def __init__(self) -> None:
        self._snapshot: ProjectIndexSnapshot | None = None

    @property
    def snapshot(self) -> ProjectIndexSnapshot | None:
        return self._snapshot

    def reset(self) -> None:
        self._snapshot = None

    def scan(
        self,
        workspace: str | Path,
        *,
        path: str | Path = ".",
        max_depth: int = 6,
        max_files: int = 1500,
    ) -> ProjectIndexSnapshot:
        guard = WorkspaceGuard(workspace)
        root = guard.resolve_for_read(path)
        if not root.exists():
            raise WorkspaceViolation(f"扫描路径不存在：{path}")
        if root.is_file():
            root = root.parent
        max_depth = max(1, min(int(max_depth or 6), 12))
        max_files = max(1, min(int(max_files or 1500), 10000))

        files: list[ProjectFileRecord] = []
        key_files: list[str] = []
        entry_points: list[str] = []
        test_files: list[str] = []
        config_files: list[str] = []
        package_dirs: list[str] = []
        risk_notes: list[str] = []
        top_dir_counter: Counter[str] = Counter()
        suffix_counter: Counter[str] = Counter()
        dirs_count = 0
        skipped_count = 0
        truncated = False

        stack: list[tuple[Path, int]] = [(root, 0)]
        while stack:
            current, depth = stack.pop()
            if depth > max_depth:
                skipped_count += 1
                continue
            try:
                children = sorted(current.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
            except OSError:
                skipped_count += 1
                continue
            for child in children:
                rel = _relative(child, guard.workspace)
                if _is_sensitive(child):
                    skipped_count += 1
                    risk_notes.append(f"跳过敏感路径：{rel}")
                    continue
                if child.is_symlink():
                    skipped_count += 1
                    continue
                if child.is_dir():
                    if child.name.lower() in EXCLUDED_DIRS:
                        skipped_count += 1
                        continue
                    dirs_count += 1
                    top_dir = rel.split("/", 1)[0]
                    if top_dir and top_dir != ".":
                        top_dir_counter[top_dir] += 1
                    if (child / "__init__.py").exists():
                        package_dirs.append(rel)
                    stack.append((child, depth + 1))
                    continue
                if not child.is_file():
                    skipped_count += 1
                    continue
                if len(files) >= max_files:
                    truncated = True
                    skipped_count += 1
                    continue
                try:
                    stat = child.stat()
                except OSError:
                    skipped_count += 1
                    continue
                suffix = child.suffix.lower() or "<none>"
                suffix_counter[suffix] += 1
                role = _classify_role(child, rel)
                record = ProjectFileRecord(rel, "file", suffix, int(stat.st_size), role)
                files.append(record)
                top_dir = rel.split("/", 1)[0]
                if top_dir and top_dir != rel:
                    top_dir_counter[top_dir] += 1
                lowered_name = child.name.lower()
                if lowered_name in KEY_FILE_NAMES:
                    key_files.append(rel)
                if lowered_name in ENTRY_FILE_NAMES:
                    entry_points.append(rel)
                if role == "test":
                    test_files.append(rel)
                if role == "config":
                    config_files.append(rel)

        snapshot = ProjectIndexSnapshot(
            schema="tiangong.l6_16.project_index.v1",
            root=_relative(root, guard.workspace) if root != guard.workspace else ".",
            scanned_at=time(),
            files_count=len(files),
            dirs_count=dirs_count,
            skipped_count=skipped_count,
            key_files=sorted(_dedupe(key_files))[:80],
            entry_points=sorted(_dedupe(entry_points))[:80],
            test_files=sorted(_dedupe(test_files))[:120],
            config_files=sorted(_dedupe(config_files))[:120],
            package_dirs=sorted(_dedupe(package_dirs))[:120],
            top_dirs=[name for name, _ in top_dir_counter.most_common(20)],
            file_type_counts=dict(suffix_counter.most_common(24)),
            sample_files=[record.public_dict() for record in files[:80]],
            risk_notes=sorted(_dedupe(risk_notes))[:40],
            truncated=truncated,
        )
        self._snapshot = snapshot
        return snapshot

    def public_dict(self) -> dict[str, Any]:
        if self._snapshot is None:
            return {"schema": "tiangong.l6_16.project_index.v1", "status": "empty", "message": "暂无项目索引，请先执行 /scan。"}
        return self._snapshot.public_dict()

    def build_planner_hint(self) -> str:
        return self._snapshot.planner_hint() if self._snapshot is not None else ""

    def export_json(self, path: str | Path) -> Path:
        target = Path(path).expanduser().resolve()
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self.public_dict()
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return target


def _relative(path: Path, workspace: Path) -> str:
    try:
        return path.resolve().relative_to(workspace.resolve()).as_posix()
    except ValueError:
        return path.name


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _is_sensitive(path: Path) -> bool:
    lowered_parts = {part.lower() for part in path.parts}
    if path.name.lower() in SENSITIVE_NAMES:
        return True
    if path.suffix.lower() in SENSITIVE_SUFFIXES:
        return True
    return bool(lowered_parts.intersection(SENSITIVE_PARTS))


def _classify_role(path: Path, rel: str) -> str:
    lowered = rel.lower().replace("\\", "/")
    name = path.name.lower()
    if "/tests/" in f"/{lowered}" or name.startswith("test_") or name.endswith("_test.py"):
        return "test"
    if name in KEY_FILE_NAMES:
        return "key"
    if name in ENTRY_FILE_NAMES:
        return "entry"
    if path.suffix.lower() in CONFIG_SUFFIXES:
        return "config"
    if path.suffix.lower() in TEXT_SUFFIXES:
        return "source_or_text"
    return "ordinary"
