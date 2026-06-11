from __future__ import annotations

from linyuanzhe_frontend.contracts.provider_settings import normalize_host_access_scope

"""Small UI-only localization layer for the Tk desktop frontend.

This module intentionally translates display text only. It must never rename
Runtime contract keys, Python identifiers, or JSON payload field names.
"""

from typing import Any

_PERMISSION_LABELS = {
    "runtime_governed": "运行时管控（工具可用）",
    "disabled": "已禁用（工具不可用）",
}
_PERMISSION_VALUES = {v: k for k, v in _PERMISSION_LABELS.items()}
_PERMISSION_VALUES.update({"运行时管控": "runtime_governed", "禁用": "disabled"})

_HOST_ACCESS_LABELS = {
    "system_drive": "全电脑 / 系统盘",
    "user_home": "用户目录",
    "project_workspace": "项目工作区",
    "custom_root": "自定义根目录",
}
_HOST_ACCESS_VALUES = {v: k for k, v in _HOST_ACCESS_LABELS.items()}
_HOST_ACCESS_VALUES.update({
    "全电脑": "system_drive",
    "系统盘": "system_drive",
    "全电脑/系统盘": "system_drive",
    "桌面/下载/全电脑": "system_drive",
    "用户主目录": "user_home",
    "项目目录": "project_workspace",
    "工作区": "project_workspace",
    "自定义": "custom_root",
})


def host_access_scope_label(value: Any) -> str:
    key = normalize_host_access_scope(value)
    return _HOST_ACCESS_LABELS.get(key, _HOST_ACCESS_LABELS["system_drive"])


def host_access_scope_value(value: Any) -> str:
    return normalize_host_access_scope(value)

_EXACT = {
    "runtime_governed": "运行时管控（工具可用）",
    "disabled": "已禁用（工具不可用）",
    "provider": "真实模型",
    "mock": "未配置模型接口",
    "forced_mock": "未配置模型接口",
    "not_configured": "未配置模型接口",
    "auto": "自动",
    "ready": "就绪",
    "idle": "待机",
    "running": "运行中",
    "queued": "排队中",
    "completed": "已完成",
    "succeeded": "已成功",
    "failed": "失败",
    "blocked": "已阻断",
    "recoverable": "可恢复",
    "waiting_confirmation": "等待确认",
    "confirmation_required": "需要确认",
    "not_tested": "未检测",
    "passed": "通过",
    "pass": "通过",
    "warn": "警告",
    "fail": "失败",
    "error": "错误",
    "missing_credentials": "缺少接口配置",
    "provider_check_failed": "模型服务联调失败",
    "provider_runtime_error": "模型服务运行错误",
    "provider_auth_error": "接口密钥认证失败",
    "provider_timeout": "模型服务超时",
    "provider_rate_limited": "模型服务限频",
    "saved_waiting_runtime": "已保存，等待运行时接管",
    "client_error": "前端客户端错误",
    "local_bridge_ready": "本地桥接就绪",
    "local_desktop_bridge_ready": "本地桌面桥接就绪",
    "local_bridge": "本地桥接",
    "rule_only": "规则规划",
    "frontend_no_direct_write": "前端禁止直接写入",
    "rc_preinstall": "候选安装前置",
    "available": "可用",
    "none": "无",
    "unknown": "未知",
    "true": "是",
    "false": "否",
    "True": "是",
    "False": "否",
}

_FIELD_LABELS = {
    "source_kind": "来源类型",
    "runtime_status": "运行时状态",
    "model_provider": "模型服务",
    "planner_mode": "规划模式",
    "tool_execution_mode": "权限模式",
    "persona_name": "本体名称",
    "base_url_display": "服务地址显示",
    "connection_status": "连接状态",
    "metadata_endpoint": "元数据端点",
    "unique_developer": "开发者",
    "angel_investor": "天使投资人",
    "provider_public": "服务商",
    "model_public": "模型",
    "readiness": "就绪状态",
    "missing_fields": "缺少字段",
    "backend_mode": "后端模式",
    "provider_config_state": "模型配置状态",
    "config_error_code": "配置错误码",
    "last_provider_check": "最近联调",
    "last_provider_error": "最近错误",
    "last_provider_next": "下一步",
    "config_audit_id": "配置审计",
    "api_key_configured": "接口密钥已配置",
    "api_key_digest": "密钥摘要指纹",
    "base_url_configured": "服务地址已配置",
    "base_url_digest": "服务地址摘要指纹",
    "config_message": "配置消息",
    "provider_hint": "模型服务提示",
    "context_digest": "上下文摘要指纹",
    "digest": "摘要指纹",
    "evidence_ref": "证据引用",
    "mode": "模式",
    "visible_msgs": "可见消息",
    "contract": "契约",
    "state": "状态",
    "last_message": "最近消息",
    "stage": "阶段",
    "version": "版本",
    "developer": "开发者",
    "angel": "天使投资人",
    "update_channel": "更新通道",
    "startup_self_check_state": "启动自检状态",
    "rollback_ready": "回滚就绪",
    "offline_repair_available": "离线修复可用",
    "path_digest": "路径摘要指纹",
    "rollback": "回滚",
    "verified": "已验证",
    "channel": "通道",
    "Budget": "预算",
    "Gate": "质量门",
    "Latency": "延迟",
    "Runtime": "运行时",
}

_PHRASES = (
    ("RuntimeClient", "运行时客户端"),
    ("Runtime SSE", "运行时流式事件"),
    ("Runtime", "运行时"),
    ("QualityGate", "质量门"),
    ("HookBus", "规则总线"),
    ("Agent UI", "智能体界面"),
    ("ExecutionSpine", "执行脊柱"),
    ("Planner", "规划器"),
    ("Observability", "观测"),
    ("Trace", "轨迹"),
    ("Provider SDK", "模型服务开发包"),
    ("Provider", "模型服务"),
    ("Mock/JSON", "未配置/只读报告"),
    ("Mock", "未配置模型接口"),
    ("DataUp", "数据更新"),
    ("Workspace", "工作区"),
    ("Connector", "连接器"),
    ("Session", "任务会话"),
    ("PublicProjection", "公共投影"),
    ("SSE", "流式事件"),
    ("run_terminal", "运行收口事件"),
    ("assistant_final", "最终回复事件"),
    ("configured", "已配置"),
    ("digest", "摘要指纹"),
    ("pending", "待生成"),
    ("ready", "就绪"),
    ("blocked", "已阻断"),
    ("requires_confirmation", "需要确认"),
    ("contract", "契约"),
    ("state", "状态"),
    ("stage", "阶段"),
    ("status", "状态"),
    ("progress", "进度"),
    ("audit", "审计"),
    ("dry-run", "干运行"),
    ("dry_run", "干运行"),
    ("frontend", "前端"),
    ("backend", "后端"),
    ("Base URL", "服务地址 Base URL"),
    ("API Key", "接口密钥 API Key"),
    ("mcp_server", "MCP 服务"),
    ("local_connector", "本地连接器"),
    ("remote_connector", "远程连接器"),
    ("document_connector", "文档连接器"),
    ("browser_connector", "浏览器连接器"),
    ("workflow_connector", "工作流连接器"),
    ("read", "只读"),
    ("write", "写入"),
    ("bytes", "字节"),
)


def permission_mode_label(value: Any) -> str:
    raw = str(value or "").strip()
    return _PERMISSION_LABELS.get(raw, raw or _PERMISSION_LABELS["runtime_governed"])


def permission_mode_value(label_or_value: Any) -> str:
    raw = str(label_or_value or "").strip()
    if raw in _PERMISSION_LABELS:
        return raw
    return _PERMISSION_VALUES.get(raw, "runtime_governed")


CONNECTOR_KIND_LABELS = {
    "mcp_server": "MCP 服务",
    "local_connector": "本地连接器",
    "remote_connector": "远程连接器",
    "document_connector": "文档连接器",
    "browser_connector": "浏览器连接器",
    "workflow_connector": "工作流连接器",
}
CONNECTOR_KIND_VALUES = {v: k for k, v in CONNECTOR_KIND_LABELS.items()}


def connector_kind_label(value: Any) -> str:
    raw = str(value or "").strip()
    return CONNECTOR_KIND_LABELS.get(raw, raw or CONNECTOR_KIND_LABELS["mcp_server"])


def connector_kind_value(label_or_value: Any) -> str:
    raw = str(label_or_value or "").strip()
    if raw in CONNECTOR_KIND_LABELS:
        return raw
    return CONNECTOR_KIND_VALUES.get(raw, "mcp_server")


def ui_text(value: Any) -> str:
    text = str(value if value is not None else "")
    if not text:
        return ""
    if text in _FIELD_LABELS:
        return _FIELD_LABELS[text]
    if text in _EXACT:
        return _EXACT[text]
    out = text
    for src, dst in _PHRASES:
        out = out.replace(src, dst)
    return out
