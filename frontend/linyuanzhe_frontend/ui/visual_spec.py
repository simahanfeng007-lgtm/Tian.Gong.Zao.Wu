from __future__ import annotations

"""STEP19 / L6.58 真实后端实例联调与 RC 前置收口规格。

该模块供 smoke test、演示验收和后续 UI 生产链引用。
它不参与 Runtime 执行，也不授予任何工具/模型权限。
"""

THEME_NAME = "极夜桌面驾驶舱"
COLOR_SYSTEM = "linyuanzhe-dark-night"
HOMEPAGE_STRUCTURE_VERSION = "STEP19-l658-real-runtime-rc-preflight-shell"

HOME_VISUAL_PRIORITIES = (
    "主聊天区最大",
    "固定聊天输入栏必须可见",
    "输入栏在首页底部固定",
    "首页右侧保留任务快照、质量门、审计摘要、对话引导四张轻量卡片",
    "计划 ID 与完整执行步骤移入执行详情页",
    "执行摘要大数字移入执行详情页",
    "底部状态栏固定 9 字段：runtime_status / provider_model / budget_pool / budget_used_ratio / gate_status / audit_id / memory_mode / tools_allowed / latency_ms",
    "发送按钮旁保留停止 / 复位 / 重连三个任务控制入口",
    "流式状态行展示 stream_state / seq / reconnect_attempts / visible / hidden",
    "流式输出采用 EventBuffer + DeltaMerger + RenderScheduler + VirtualTranscript",
    "Agent UI Event 只作为显示契约，不作为命令契约",
)

DESKTOP_POLISH_REQUIREMENTS = (
    "顶部工具栏克制：新建任务 / 导入计划 / 设置",
    "左侧导航六项：聊天 / 执行 / 记忆 / 自我迭代 / 四路径 / 设置",
    "首页只显示主要数据",
    "首页必须能直接输入和发送消息",
    "右侧状态摘要不得超过四张卡片，且对话引导不得展示完整计划",
    "二级详情渐进披露",
    "真实任务只通过 L6.58 Runtime SSE / Agent UI / RC 预检契约端点提交",
    "Provider 设置页只向 /settings/provider 提交写入请求，回执只展示 configured/digest/错误态",
    "正式合成前必须完成真实 Runtime 实例预检；契约服务器回归不能替代真实联调",
    "QualityGate 行动守卫卡只能提交确认请求，不能前端放行",
    "审计/回滚卡片只读展示，不能前端写审计或应用回滚",
    "前端仍禁止裸调 Provider SDK、Adapter、工具、记忆、审计、回滚",
    "停止/复位按钮只向 Runtime 提交控制请求，不直接停止工具或复位内核",
    "视觉色彩从 Design Tokens 派生，避免散落硬编码扩大",
    "联调与 RC 预检报告只写 Runtime URL digest，不写明文地址或 Provider 凭证",
    "端到端 smoke 与 RC 预检必须验证 assistant_final -> run_terminal 顺序",
)

SCREENSHOT_ACCEPTANCE_REQUIREMENTS = (
    "截图必须能看到固定聊天输入栏",
    "截图首页不得出现执行摘要大数字卡片",
    "截图首页不得出现完整执行链表格",
    "截图右侧只能是任务快照、质量门、审计摘要、对话引导",
    "截图必须保留底部 9 字段状态栏",
    "截图必须能看到停止 / 复位 / 重连控制入口或其状态行",
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
    "light_day_theme_for_linyuanzhe",
)
