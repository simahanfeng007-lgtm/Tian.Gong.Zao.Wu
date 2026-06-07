"""工作区边界保护。"""

from __future__ import annotations

from pathlib import Path


SENSITIVE_NAMES = {
    ".env",
    ".env.local",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
}
SENSITIVE_SUFFIXES = {".pem", ".key", ".p12", ".pfx", ".crt", ".cer"}
SENSITIVE_PARTS = {".ssh", ".gnupg", "credentials", "secrets", "secret", "tokens"}


class WorkspaceViolation(ValueError):
    pass


class WorkspaceGuard:
    def __init__(self, workspace: str | Path) -> None:
        self.workspace = Path(workspace).expanduser().resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)

    def resolve_for_read(self, path: str | Path) -> Path:
        resolved = self._resolve(path)
        self._ensure_inside_workspace(resolved)
        self._ensure_not_sensitive(resolved)
        return resolved

    def resolve_for_write(self, path: str | Path) -> Path:
        resolved = self._resolve(path)
        self._ensure_inside_workspace(resolved)
        self._ensure_not_sensitive(resolved)
        return resolved

    def resolve_for_artifact(self, path: str | Path) -> Path:
        resolved = self._resolve(path)
        self._ensure_inside_workspace(resolved)
        self._ensure_not_sensitive(resolved)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        return resolved

    def _resolve(self, path: str | Path) -> Path:
        raw = Path(path)
        if not raw.is_absolute():
            raw = self.workspace / raw
        return raw.expanduser().resolve()

    def _ensure_inside_workspace(self, resolved: Path) -> None:
        try:
            resolved.relative_to(self.workspace)
        except ValueError as exc:
            raise WorkspaceViolation(f"路径越出工作区：{resolved}") from exc

    def _ensure_not_sensitive(self, resolved: Path) -> None:
        lowered_parts = {part.lower() for part in resolved.parts}
        if resolved.name.lower() in SENSITIVE_NAMES:
            raise WorkspaceViolation(f"禁止访问敏感文件：{resolved.name}")
        if resolved.suffix.lower() in SENSITIVE_SUFFIXES:
            raise WorkspaceViolation(f"禁止访问敏感后缀：{resolved.suffix}")
        if lowered_parts.intersection(SENSITIVE_PARTS):
            raise WorkspaceViolation("禁止访问敏感目录或凭证路径。")
