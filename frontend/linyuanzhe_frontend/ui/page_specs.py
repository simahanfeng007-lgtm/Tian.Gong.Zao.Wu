from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PageSpec:
    key: str
    label: str
    icon: str
    description: str


# STEP31Q: 顶层导航只保留 5 个入口。详细执行链、观测、文件、连接、迭代、安装等
# 仍保留为可访问页面，但不再挤占首页左侧主导航。
PAGE_DEFINITIONS: Tuple[PageSpec, ...] = (
    PageSpec("chat", "会话", "", "首页：主聊天区、固定输入栏、会话信息折叠栏"),
    PageSpec("sessions", "任务", "", "任务列表、搜索、恢复请求、等待确认、失败归档"),
    PageSpec("memory", "记忆", "", "脱敏记忆摘要、digest、evidence_ref、文件/工作区入口"),
    PageSpec("four_paths", "系统", "", "执行、记忆、情志、生命周期、连接、迭代、安装与 DataUp 更新入口"),
    PageSpec("settings", "设置", "", "Provider 向导、主模型、外观与 Runtime 只读接入配置"),
)

EXTRA_PAGE_DEFINITIONS: Tuple[PageSpec, ...] = (
    PageSpec("execution", "执行详情", "", "执行链、质量门、恢复续接、确认票据摘要"),
    PageSpec("observability", "运行观测", "", "Trace、事件、预算、质量门、错误与 SSE 收口顺序，只读展示"),
    PageSpec("files", "文件交接", "", "文件传输请求、附件交接、下载/上传回执与边界说明"),
    PageSpec("workspace", "工作区", "", "Workspace、沙箱边界、目录白名单、文件授权与下载中转回执"),
    PageSpec("connectors", "连接器", "", "MCP / 连接器注册表、白名单、隔离、只读投影与注册请求"),
    PageSpec("iteration", "迭代", "", "迭代候选、用户确认、回滚与测试要求"),
    PageSpec("installer", "安装", "", "安装器 RC、版本槽、启动自检、打包 dry-run 与离线修复骨架"),
    PageSpec("hooks", "规则", "", "HookBus 规则、阻断记录、请求守卫与事件守卫，只读展示"),
)

ALL_PAGE_DEFINITIONS: Tuple[PageSpec, ...] = PAGE_DEFINITIONS + EXTRA_PAGE_DEFINITIONS
PAGE_BY_KEY = {item.key: item for item in ALL_PAGE_DEFINITIONS}
DEFAULT_PAGE = "chat"

HOME_ALLOWED_MODULES = (
    "主聊天区",
    "固定聊天输入栏",
    "折叠式会话信息栏",
    "任务摘要",
    "质量门摘要",
    "审计摘要",
    "对话建议",
    "附件按钮",
    "中断任务按钮",
    "底部极简状态栏",
    "系统页 DataUp 更新入口",
)

HOME_REMOVED_MODULES = (
    "首页四张右侧监控卡",
    "首页执行摘要大数字",
    "首页成功/阻塞/待确认大卡片",
    "首页完整执行链",
    "首页复杂进度面板",
    "首页计划 ID 长字段",
    "首页完整执行步骤",
    "首页预算/消耗/命中率指标条",
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
    "首页自动应用更新",
    "首页前端应用回滚",
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
