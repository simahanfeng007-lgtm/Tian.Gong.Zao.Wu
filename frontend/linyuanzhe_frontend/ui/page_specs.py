from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PageSpec:
    key: str
    label: str
    icon: str
    description: str


PAGE_DEFINITIONS: Tuple[PageSpec, ...] = (
    PageSpec("chat", "聊天", "▣", "首页：主聊天区、固定输入栏、右侧任务快照/质量门/审计/对话引导"),
    PageSpec("execution", "执行", "⟡", "二级页：执行链 timeline、质量门、恢复续接、确认票据摘要"),
    PageSpec("sessions", "任务", "▥", "二级页：多任务 Session 塔台、搜索、恢复、等待确认、失败归档与快捷键"),
    PageSpec("observability", "观测", "⌁", "二级页：Trace、事件、预算、质量门、错误与 SSE 收口顺序，只读展示"),
    PageSpec("files", "文件", "⇪", "二级页：文件传输请求、附件交接、下载/上传回执与边界说明"),
    PageSpec("workspace", "工作区", "▤", "二级页：Agent Workspace、沙箱边界、目录白名单、文件授权与下载中转回执"),
    PageSpec("connectors", "连接器", "⧉", "二级页：MCP / 连接器注册表、白名单、隔离、只读投影与注册请求"),
    PageSpec("memory", "记忆", "◫", "二级页：脱敏记忆摘要、digest、evidence_ref"),
    PageSpec("iteration", "自我迭代", "◈", "二级页：自我迭代候选、用户确认、回滚与测试要求"),
    PageSpec("four_paths", "四路径", "☷", "二级页：执行/记忆/情志/生命周期统一状态投影"),
    PageSpec("installer", "安装", "▧", "二级页：安装器 RC 前置结构、版本槽、启动自检、打包 dry-run、发布 manifest 与离线修复骨架"),
    PageSpec("settings", "设置", "⚙", "二级页：API 输入、主模型选择、模型搜索与边界策略"),
)

EXTRA_PAGE_DEFINITIONS: Tuple[PageSpec, ...] = (
    PageSpec("hooks", "规则", "⌬", "二级页：HookBus 确定性规则、阻断记录、请求守卫与事件守卫，只读展示"),
)

ALL_PAGE_DEFINITIONS: Tuple[PageSpec, ...] = PAGE_DEFINITIONS + EXTRA_PAGE_DEFINITIONS
PAGE_BY_KEY = {item.key: item for item in ALL_PAGE_DEFINITIONS}
DEFAULT_PAGE = "chat"

HOME_ALLOWED_MODULES = (
    "主聊天区",
    "固定聊天输入栏",
    "右侧任务快照卡",
    "右侧质量门卡",
    "右侧审计摘要卡",
    "右侧对话引导卡",
    "附件按钮",
    "中断任务按钮",
    "工作区授权入口",
    "连接器注册表入口",
    "任务 Session 入口",
    "安装器 RC 状态入口",
    "底部系统状态栏",
)

HOME_REMOVED_MODULES = (
    "首页执行摘要大数字",
    "首页成功/阻塞/待确认大卡片",
    "首页完整执行链",
    "首页复杂进度面板",
    "首页计划 ID 长字段",
    "首页完整执行步骤",
)

FORBIDDEN_HOME_MODULES = (
    "完整执行链表格",
    "完整审计链",
    "完整 prompt",
    "完整工具调用参数",
    "完整记忆正文",
    "完整恢复计划",
    "完整生命周期候选",
    "完整情感画像",
    "完整交付物 manifest",
    "原始文件路径",
    "原始文件内容",
    "原始安装路径",
    "完整安装日志",
    "自动应用更新",
    "前端应用回滚",
    "开放 MCP 市场安装",
    "连接器原始 endpoint",
    "连接器原始密钥",
    "首页执行摘要大数字",
    "API 明文密钥",
    "主模型 API Key 输入框",
    "密钥",
    "账号",
    "真实路径",
    "隐私数据",
)
