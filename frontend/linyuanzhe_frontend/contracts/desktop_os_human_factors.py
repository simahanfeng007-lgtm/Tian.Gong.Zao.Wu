from __future__ import annotations

"""Desktop OS human-factors quality contract for L6.72.34.

This module is intentionally UI-framework neutral.  It converts common desktop
OS expectations into static checks that can be run in CI/smoke without opening a
GUI window.  It does not grant execution authority; it only audits the desktop
shell surface, contracts and transport defaults.
"""

from dataclasses import dataclass, asdict
from typing import Any, Dict, Iterable, List, Mapping

DESKTOP_OS_HUMAN_FACTORS_CONTRACT_VERSION = "tiangong.l6_72_30.desktop_os_human_factors.v1"


@dataclass(frozen=True)
class DesktopRequirement:
    key: str
    label: str
    required: bool = True


REQUIREMENTS: tuple[DesktopRequirement, ...] = (
    DesktopRequirement("primary_task_visible", "主任务区优先，不让诊断栏挤占输入/阅读空间"),
    DesktopRequirement("responsive_layout", "720×480 到宽屏窗口均不应裁剪核心文字"),
    DesktopRequirement("clear_modes", "聊天/工作双模式必须可见且可切换；code/file/document/long_chain 由 LLM 填 ActivationForm"),
    DesktopRequirement("state_visibility", "任务状态、心跳、当前工具、失败原因必须可见"),
    DesktopRequirement("cancel_recover", "长任务必须有停止、重连、复位和诊断复制"),
    DesktopRequirement("keyboard_access", "键盘提交、换行、快捷键和中文 IME 防误发"),
    DesktopRequirement("accessibility_basics", "字号、行距、主题、对比度与可读字体可调"),
    DesktopRequirement("privacy_secret_guard", "密钥、token、本地真实路径不得直接显示"),
    DesktopRequirement("friendly_errors", "连接/模型/超时错误必须给用户下一步"),
    DesktopRequirement("persistence_export", "本地历史、只读回放、导出与清理可用"),
    DesktopRequirement("no_internal_signal_leak", "return_analysis 等内部信号不得进入聊天气泡"),
    DesktopRequirement("runtime_authority", "前端只提交意图和审批，不能直接执行工具"),
)


def requirement_keys() -> List[str]:
    return [item.key for item in REQUIREMENTS]


def audit_capability_flags(flags: Mapping[str, Any]) -> Dict[str, Any]:
    """Evaluate a desktop shell capability map.

    The caller passes booleans collected from static modules or a runtime
    snapshot.  Missing required flags are failures.  Unknown flags are ignored.
    """

    required = {item.key for item in REQUIREMENTS if item.required}
    passed = [key for key in required if bool(flags.get(key))]
    failed = sorted(required.difference(passed))
    return {
        "contract": DESKTOP_OS_HUMAN_FACTORS_CONTRACT_VERSION,
        "ok": not failed,
        "passed": sorted(passed),
        "failed": failed,
        "coverage_ratio": round(len(passed) / max(1, len(required)), 4),
        "frontend_executes_tools": False,
    }


def default_expected_flags() -> Dict[str, bool]:
    return {key: True for key in requirement_keys()}
