# Q22 Dialogue / Analysis Work-Mode Boundary Fix

## 修复目标

Q21 只覆盖了“忙呢？”这类短寒暄。Windows 桌面端如果左下角停在“工作”，用户继续问普通问题或分析问题，例如：

- 为什么会这样啊，我问他话，它给我回复这个
- 这是什么问题？
- 这个错误是什么意思？
- 帮我分析一下这个报错
- 现在这个能做长链工作了？
- 我这个是不是还没有网关，无法链接微信，飞书

旧行为仍可能把它们送进 Runtime / ActivationForm / 工具链，进而暴露“主脑本轮未激活工具链 / Runtime 工具任务失败”。

## 修复内容

- 扩展前端 `work_modes.py` 的安全分流：
  - 工作模式下的普通提问、解释提问、能力/状态提问、报错含义分析，自动按聊天提交。
  - 真正的读取、写入、修复、运行、打包、接入、部署等动作仍保持工作模式。
- 扩展桌面本地桥 `linyuanzhe_local_runtime_bridge_l671.py`：
  - 即使旧 payload 强行带 `activation_requested/tools_requested`，只要用户消息是非执行型普通问题，也会在桥接层降级为聊天。
  - Provider 模式也受保护，不再把普通问题带进工具链失败路径。
- 更新 UI 状态提示：
  - 区分“寒暄/普通提问”和“普通问题/分析问题”。
- 新增验证脚本：
  - `scripts/verify_l6738_q22_dialogue_analysis_work_mode_boundary.py`

## 回归摘要

Fresh tree regression:

- `scripts/verify_l6738_q22_dialogue_analysis_work_mode_boundary.py` PASS
- `scripts/verify_l6738_q21_casual_chat_work_mode_route.py` PASS
- `scripts/verify_l6738_q20_windows_double_click_launcher.py` PASS
- `scripts/verify_l6738_q19_history_entry_permissions.py` PASS
- `scripts/verify_l6738_q18_write_fix_pack_loop.py` PASS
- `scripts/verify_l6738_mock_llm_long_chain_cli.py` PASS
- `frontend/linyuanzhe_frontend/run_work_mode_activation_smoke_l67225.py` PASS
- `frontend/linyuanzhe_frontend/run_l67254_conversation_workflow_separation_smoke.py` PASS
- `backend/project/run_agent.py --mock --status` PASS，未污染包根

## 边界

- “这个错误是什么意思？”：聊天/解释。
- “请读取 C:\Users\a\Desktop\x.txt 并总结”：工作/执行。
- “为什么会这样？”：聊天/解释。
- “请检查这个项目，定位 bug，修复并给出总结”：工作/执行。
