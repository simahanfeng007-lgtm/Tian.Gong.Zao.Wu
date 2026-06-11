# CHANGELOG L6.63

## 新增

- 新增 `contracts/hook_bus.py`。
- 新增 RuntimeSnapshot HookBus 字段：`hook_records`、`hook_stats`、`hook_last_blocker`、`hook_export_digest`。
- 新增 SSE Runtime Client HookBus 接线。
- 新增桌面端「规则」二级页。
- 新增 HookBus smoke 与 preflight。
- 新增 L6.63 发布验证脚本与启动器入口。

## 修复

- 将必须执行的 A5、终端顺序、Provider 只写不回显、确认票据、控制请求边界从提示词约束升级为确定性本地规则。
- Provider 设置 HookRecord 只保留 configured / digest 投影，不保留原始凭证或真实服务地址。

## 不变边界

- 不改后端核心主链。
- 不新增前端工具执行能力。
- 不新增前端记忆写入能力。
- 不新增前端审计写入能力。
- 不新增前端回滚应用能力。
- 真实 Runtime 未烟测前，不把 `ready_for_combine` 标为 true。
