from __future__ import annotations

"""STEP31Q / L6.71.7 首页对话优先与导航瘦身规格。

该模块供 smoke test、演示验收和后续 UI 生产链引用。
它只描述前端显示，不参与 Runtime 执行，也不授予任何工具/模型权限。
"""

THEME_NAME = "中性 AI 工作台"
COLOR_SYSTEM = "linyuanzhe-neutral-workbench-step31m"
HOMEPAGE_STRUCTURE_VERSION = "STEP31Q-l6715-markdown-chat-shell"

HOME_VISUAL_PRIORITIES = (
    "主聊天区最大，占据首屏视觉中心",
    "固定聊天输入栏必须可见",
    "右侧 Runtime 信息默认折叠为会话信息栏",
    "首页不常驻四张监控卡",
    "质量门、审计、执行链只展示摘要，详情进入二级页",
    "左侧导航只保留 5 个顶层入口：会话 / 任务 / 记忆 / 系统 / 设置",
    "底部状态栏固定 4 字段：就绪 / 模式 / 质量门 / 审计",
    "发送区只保留附件、发送、中断、任务入口，停止/复位/重连下沉",
    "聊天正文支持基础 Markdown：标题 / 列表 / 代码块 / 行内代码 / 加粗 / 链接识别",
    "流式输出采用 EventBuffer + DeltaMerger + RenderScheduler + VirtualTranscript，并保留换行",
    "Agent UI Event 只作为显示契约，不作为命令契约",
)

DESKTOP_POLISH_REQUIREMENTS = (
    "顶部工具栏克制：新会话 / 设置",
    "左侧导航使用短中文标签，避免图标和复杂术语抢占主会话",
    "首页只显示能帮助继续对话的状态",
    "首页必须能直接输入和发送消息",
    "二级详情渐进披露",
    "Provider 设置页以向导承载 Provider、Base URL、API Key、主模型和检查配置",
    "Provider 设置只向 /settings/provider 提交写入请求，回执只展示 configured/digest/错误态",
    "正式合成前必须完成真实 Runtime 实例预检；契约服务器回归不能替代真实联调",
    "QualityGate 行动守卫卡只能提交确认请求，不能前端放行",
    "审计/回滚卡片只读展示，不能前端写审计或应用回滚",
    "前端仍禁止裸调 Provider SDK、Adapter、工具、记忆、审计、回滚",
    "视觉色彩从 Design Tokens 派生，避免散落硬编码扩大",
    "联调与 RC 预检报告只写 Runtime URL digest，不写明文地址或 Provider 凭证",
    "端到端 smoke 与 RC 预检必须验证 assistant_final -> run_terminal 顺序",
)

SCREENSHOT_ACCEPTANCE_REQUIREMENTS = (
    "截图必须能看到固定聊天输入栏",
    "截图首页不得出现执行摘要大数字卡片",
    "截图首页不得出现完整执行链表格",
    "截图右侧默认是折叠会话信息栏，不是四张监控卡",
    "截图必须保留底部 4 字段中文状态栏",
    "截图不得像浏览器 Web 后台或监控大屏",
)

FORBIDDEN_VISUAL_DIRECTIONS = (
    "web_dashboard",
    "browser_address_bar",
    "sci_fi_big_screen",
    "game_hud",
    "dense_table_homepage",
    "homepage_metric_overload",
    "neon_overload",
)
