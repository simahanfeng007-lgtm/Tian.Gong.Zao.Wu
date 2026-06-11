# CHANGELOG L6.72.12

## OrganSignalCard / 器官信号标准层

- 新增 `tiangong_agent_shell.organ_signal_card`。
- 新增 `OrganSignalCard`、`OrganSignalScore`、`emit_organ_signal_card`、`select_organ_signal_cards`、`trace_organ_signal_cards`。
- PromptCompiler 接入 `organ_signal_cards`，并兼容 legacy `memory_cards` / `skill_cards`。
- ordinary_chat 下动态器官信号区硬阻断 PlannerCard。
- trace_only 卡片不进入模型上下文。
- 含密钥标记的摘要自动脱敏。
- 新增 `run_organ_signal_card_smoke_l67212.py` 与跨平台启动脚本。

## 边界

- 不改 kernel。
- 不改 Runtime 主链。
- 不新增执行入口。
- 不复制 v1。
- 不启动后台 loop。
