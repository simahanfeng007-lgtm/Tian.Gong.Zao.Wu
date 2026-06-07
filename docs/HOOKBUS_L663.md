# FE01 STEP24 / L6.63 HookBus 确定性规则层

## 定位

L6.63 在桌面端新增 HookBus 确定性规则层。它是前端外层的本地守卫和只读投影层，只负责校验请求信封、校验 Runtime 公共事件、生成脱敏 HookRecord，并把结果展示到「规则」二级页。

HookBus 不执行工具、不调用 Provider、不写长期记忆、不写审计、不应用回滚，也不绕过 QualityGate。所有真正执行仍必须进入 TiangongWangguan / Runtime。

## 覆盖阶段

- `pre_chat_submit`：聊天请求提交前检查前端越权标记。
- `pre_provider_settings_submit`：Provider 设置提交前检查只写不回显契约。
- `pre_confirmation_submit`：确认请求提交前检查票据与决策词表。
- `pre_control_request`：停止 / 复位请求提交前检查仅请求 Runtime。
- `pre_self_iteration_confirm`：自我迭代确认前检查候选与禁止前端直接应用。
- `pre_event_apply`：Runtime 事件进入前端状态投影前检查。
- `post_event_apply`：事件投影后生成脱敏摘要与警告。
- `pre_finalize`：最终收口前检查 assistant_final 与 run_terminal 顺序。
- `on_error`：前端捕获错误时生成可观测 HookRecord。

## 硬规则

1. A5 极高危不得被前端或 Runtime 公共事件标记为直接通过；必须阻断或进入人工确认。
2. `run_terminal` 不得早于 `assistant_final`。
3. Provider 设置只允许写入请求；前端展示只能显示 configured / digest，不得回显原值。
4. 控制请求、确认请求、自我迭代确认均只能提交给 Runtime，不得由前端直接执行。
5. HookRecord 必须脱敏，不保存密钥、令牌、真实路径、真实 endpoint 或 run/task 原文。

## 验证入口

```bash
python scripts/hookbus_preflight_l663.py
python -m linyuanzhe_frontend.run_hookbus_smoke
python scripts/verify_l663_release.py
```

也可以使用：

```bash
launchers/run_hookbus_preflight_l663.sh
launchers/verify_l663_release.sh
```

Windows 使用同名 `.bat`。

## RC 状态

L6.63 只补确定性规则层，不解除真实 Runtime 阻断。若没有真实 Runtime 地址，`ready_for_combine` 仍必须保持 false。
