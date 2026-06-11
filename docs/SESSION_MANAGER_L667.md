# FE01 STEP28 / L6.67 多任务 Session 管理器

## 目标

在不改变后端 Runtime 主链、不赋予前端执行权限的前提下，为桌面端新增任务塔台：

- 多任务 Session 只读列表
- 运行中 / 等待确认 / 阻断 / 可恢复 / 已完成状态汇总
- 任务搜索
- Session 恢复请求
- 快捷键入口

## 边界

前端允许：

- 读取 Runtime / TiangongWangguan 返回的 Session PublicProjection
- 对本地投影做搜索过滤
- 向 Runtime 提交 `/sessions/resume`、`/sessions/search` 请求 envelope
- 展示 Runtime 回执、audit digest、session digest

前端禁止：

- 直接恢复工具
- 直接切换 Runtime Run
- 直接写长期记忆
- 直接写审计
- 直接应用回滚
- 绕过 QualityGate
- 显示原始 Run ID、Task ID、路径、密钥或 endpoint 明文

## 新增契约

- `contracts/session_manager.py`
- `SESSION_MANAGER_CONTRACT_VERSION = tiangong.l6_67.session_manager.v1`
- `/sessions/list`
- `/sessions/resume`
- `/sessions/search`
- `/sessions/archive`（预留）

## 桌面端入口

- 新增「任务」二级页
- 顶栏新增「任务塔台」按钮
- 首页输入栏左侧新增「任务」按钮

## 快捷键

- `F5`：刷新投影
- `Ctrl+F`：打开任务页 / 搜索入口
- `Ctrl+R`：恢复选中或可恢复任务
- `Ctrl+.`：中断当前任务请求

## 修复项

修复 L6.66 包中 SSE 文件授权请求的 HookBus 参数错位：

- 原问题：`request_file_authorization` 调用 `_evaluate_hook` 时混入 `HOOK_STAGE_PRE_CONNECTOR_REGISTRATION_REQUEST`，真实 SSE 客户端可能触发 TypeError。
- 修复：文件授权只走 `HOOK_STAGE_PRE_WORKSPACE_AUTHORIZATION_REQUEST`。

## 验证

- `python scripts/session_manager_preflight_l667.py`
- `python scripts/verify_l667_release.py`
