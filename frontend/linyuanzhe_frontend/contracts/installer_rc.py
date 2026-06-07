from __future__ import annotations

"""L6.68 installer RC pre-stage contract.

The desktop frontend may display installer/update/recovery projections and launch
preflight helpers. It must not install packages, mutate version slots, upload
crash reports, apply rollback, or rewrite Runtime files directly. Real install,
update, rollback, and repair actions must be owned by the installer controller,
Runtime/TiangongWangguan, or an explicit user-run maintenance script.
"""

from dataclasses import asdict, dataclass, field
from hashlib import sha256
from typing import Any, Dict, Iterable, List, Mapping

INSTALLER_RC_CONTRACT_VERSION = "tiangong.l6_68.installer_rc.v1"
INSTALLER_MANIFEST_ENDPOINT = "/installer/manifest"
STARTUP_SELF_CHECK_ENDPOINT = "/installer/startup/self-check"
UPDATE_CHECK_ENDPOINT = "/installer/update/check"
REPAIR_REQUEST_ENDPOINT = "/installer/repair/request"
ROLLBACK_PLAN_ENDPOINT = "/installer/rollback/plan"

SLOT_STATES = {"active", "candidate", "rollback", "standby", "disabled", "broken"}
CHECK_STATUSES = {"pass", "warn", "fail", "blocked", "pending", "skipped"}


def _safe_text(value: Any, max_len: int = 180) -> str:
    text = "" if value is None else str(value)
    lowered = text.lower()
    for needle in ("api_key", "secret", "token", "password", "bearer", "sk-"):
        if needle in lowered:
            text = "<redacted>"
            break
    text = text.replace("\r", " ").replace("\n", " ").strip()
    if len(text) > max_len:
        return text[: max_len - 1] + "…"
    return text


def _digest(value: Any, length: int = 16) -> str:
    text = "" if value is None else str(value)
    return sha256(text.encode("utf-8", errors="ignore")).hexdigest()[:length] if text else ""


@dataclass(frozen=True)
class VersionSlotProjection:
    slot_name: str
    version_label: str = "L6.68-rc-preinstall"
    state: str = "standby"
    path_digest: str = ""
    package_sha256_digest: str = ""
    created_at: str = "当前"
    last_verified: str = "未验证"
    rollback_capable: bool = False
    startup_self_check_required: bool = True
    message: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "VersionSlotProjection":
        state = _safe_text(data.get("state", "standby"), 40).lower() or "standby"
        if state not in SLOT_STATES:
            state = "standby"
        raw_path = data.get("path") or data.get("install_path") or data.get("slot_name") or ""
        return cls(
            slot_name=_safe_text(data.get("slot_name", data.get("name", "slot")), 80),
            version_label=_safe_text(data.get("version_label", data.get("version", "L6.68-rc-preinstall")), 80),
            state=state,
            path_digest=_safe_text(data.get("path_digest", ""), 80) or _digest(raw_path),
            package_sha256_digest=_safe_text(data.get("package_sha256_digest", data.get("sha256_digest", "")), 80),
            created_at=_safe_text(data.get("created_at", "当前"), 80),
            last_verified=_safe_text(data.get("last_verified", "未验证"), 80),
            rollback_capable=bool(data.get("rollback_capable", False)),
            startup_self_check_required=bool(data.get("startup_self_check_required", True)),
            message=_safe_text(data.get("message", ""), 220),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class StartupSelfCheckRecord:
    check_id: str
    name: str
    status: str = "pending"
    severity: str = "info"
    message: str = "等待自检"
    last_run: str = "未运行"
    blocks_startup: bool = False
    remediation_hint: str = ""

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "StartupSelfCheckRecord":
        status = _safe_text(data.get("status", "pending"), 40).lower() or "pending"
        if status not in CHECK_STATUSES:
            status = "pending"
        return cls(
            check_id=_safe_text(data.get("check_id", data.get("id", "check")), 80),
            name=_safe_text(data.get("name", "启动自检项"), 120),
            status=status,
            severity=_safe_text(data.get("severity", "info"), 40),
            message=_safe_text(data.get("message", "等待自检"), 220),
            last_run=_safe_text(data.get("last_run", "未运行"), 80),
            blocks_startup=bool(data.get("blocks_startup", status in {"fail", "blocked"})),
            remediation_hint=_safe_text(data.get("remediation_hint", ""), 220),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CrashReportProjection:
    report_id_digest: str
    status: str = "empty"
    crash_count: int = 0
    last_crash_at: str = "无"
    safe_summary: str = "暂无崩溃报告"
    local_only: bool = True
    upload_allowed: bool = False
    message: str = "崩溃报告默认本地保存，禁止自动上传。"

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "CrashReportProjection":
        raw_id = data.get("report_id") or data.get("id") or data.get("safe_summary") or "crash-report"
        return cls(
            report_id_digest=_safe_text(data.get("report_id_digest", ""), 80) or _digest(raw_id),
            status=_safe_text(data.get("status", "empty"), 80),
            crash_count=max(0, int(data.get("crash_count", 0) or 0)),
            last_crash_at=_safe_text(data.get("last_crash_at", "无"), 80),
            safe_summary=_safe_text(data.get("safe_summary", "暂无崩溃报告"), 220),
            local_only=bool(data.get("local_only", True)),
            upload_allowed=bool(data.get("upload_allowed", False)),
            message=_safe_text(data.get("message", "崩溃报告默认本地保存，禁止自动上传。"), 220),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RepairActionRecord:
    action_id: str
    title: str
    status: str = "available"
    requires_user_confirmation: bool = True
    message: str = "等待用户显式执行维护脚本"
    route_to_installer_only: bool = True
    no_frontend_apply: bool = True
    no_runtime_core_mutation: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "RepairActionRecord":
        return cls(
            action_id=_safe_text(data.get("action_id", data.get("id", "repair")), 80),
            title=_safe_text(data.get("title", "离线修复动作"), 120),
            status=_safe_text(data.get("status", "available"), 80),
            requires_user_confirmation=bool(data.get("requires_user_confirmation", True)),
            message=_safe_text(data.get("message", "等待用户显式执行维护脚本"), 220),
            route_to_installer_only=bool(data.get("route_to_installer_only", True)),
            no_frontend_apply=bool(data.get("no_frontend_apply", True)),
            no_runtime_core_mutation=bool(data.get("no_runtime_core_mutation", True)),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class InstallerManifestProjection:
    contract_version: str = INSTALLER_RC_CONTRACT_VERSION
    product_name: str = "天工造物 / 临渊者"
    package_stage: str = "rc_preinstall"
    install_mode: str = "engineering_package"
    version_label: str = "FE01 STEP29 / L6.68"
    unique_developer: str = "于泳翔"
    angel_investor: str = "胖胖龙"
    active_slot: str = "active"
    rollback_slot: str = "rollback"
    update_channel: str = "internal_rc"
    install_root_digest: str = "INSTALL-ROOT-MOCK"
    startup_self_check_state: str = "pending"
    crash_report_state: str = "empty"
    rollback_ready: bool = True
    offline_repair_available: bool = True
    updater_skeleton_only: bool = True
    installer_build_allowed: bool = False
    slots: List[VersionSlotProjection] = field(default_factory=list)
    startup_checks: List[StartupSelfCheckRecord] = field(default_factory=list)
    crash_reports: List[CrashReportProjection] = field(default_factory=list)
    repair_actions: List[RepairActionRecord] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> "InstallerManifestProjection":
        slots = [VersionSlotProjection.from_mapping(x) for x in data.get("slots", data.get("version_slots", [])) or [] if isinstance(x, Mapping)]
        checks = [StartupSelfCheckRecord.from_mapping(x) for x in data.get("startup_checks", data.get("self_checks", [])) or [] if isinstance(x, Mapping)]
        crash = [CrashReportProjection.from_mapping(x) for x in data.get("crash_reports", []) or [] if isinstance(x, Mapping)]
        repairs = [RepairActionRecord.from_mapping(x) for x in data.get("repair_actions", data.get("repairs", [])) or [] if isinstance(x, Mapping)]
        raw_root = data.get("install_root") or data.get("install_path") or data.get("product_name") or ""
        return cls(
            contract_version=_safe_text(data.get("contract_version", data.get("installer_rc_contract", INSTALLER_RC_CONTRACT_VERSION)), 100),
            product_name=_safe_text(data.get("product_name", "天工造物 / 临渊者"), 120),
            package_stage=_safe_text(data.get("package_stage", "rc_preinstall"), 80),
            install_mode=_safe_text(data.get("install_mode", "engineering_package"), 80),
            version_label=_safe_text(data.get("version_label", data.get("version", "FE01 STEP29 / L6.68")), 100),
            unique_developer=_safe_text(data.get("unique_developer", "于泳翔"), 80),
            angel_investor=_safe_text(data.get("angel_investor", "胖胖龙"), 80),
            active_slot=_safe_text(data.get("active_slot", "active"), 80),
            rollback_slot=_safe_text(data.get("rollback_slot", "rollback"), 80),
            update_channel=_safe_text(data.get("update_channel", "internal_rc"), 80),
            install_root_digest=_safe_text(data.get("install_root_digest", ""), 80) or _digest(raw_root),
            startup_self_check_state=_safe_text(data.get("startup_self_check_state", "pending"), 80),
            crash_report_state=_safe_text(data.get("crash_report_state", "empty"), 80),
            rollback_ready=bool(data.get("rollback_ready", True)),
            offline_repair_available=bool(data.get("offline_repair_available", True)),
            updater_skeleton_only=bool(data.get("updater_skeleton_only", True)),
            installer_build_allowed=bool(data.get("installer_build_allowed", False)),
            slots=slots,
            startup_checks=checks,
            crash_reports=crash,
            repair_actions=repairs,
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def installer_rc_policy() -> Dict[str, Any]:
    return {
        "contract_version": INSTALLER_RC_CONTRACT_VERSION,
        "frontend_display_only": True,
        "frontend_may_build_installer": False,
        "frontend_may_apply_update": False,
        "frontend_may_apply_rollback": False,
        "frontend_may_upload_crash_report": False,
        "startup_self_check_is_preflight_only": True,
        "offline_repair_defaults_to_dry_run": True,
        "version_slot_mutation_requires_explicit_installer_controller": True,
        "runtime_core_mutation_forbidden": True,
    }


def summarize_checks(checks: Iterable[StartupSelfCheckRecord]) -> Dict[str, int]:
    items = list(checks)
    return {
        "total": len(items),
        "pass": sum(1 for item in items if item.status == "pass"),
        "warn": sum(1 for item in items if item.status == "warn"),
        "fail": sum(1 for item in items if item.status == "fail"),
        "blocked": sum(1 for item in items if item.status == "blocked" or item.blocks_startup),
        "pending": sum(1 for item in items if item.status == "pending"),
    }
