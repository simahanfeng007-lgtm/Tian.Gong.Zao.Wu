# Q18 真实长链与写修打包闭环修复日志

日期：2026-06-11  
基线：L6.73.8 Q17 LLM 长链模拟修复版

## 本轮覆盖范围

1. 真实长链工作区压力测试
   - `backend/project/run_l6730_human_deepseek_full_chain_pressure_smoke.py`
   - `frontend/linyuanzhe_frontend/run_real_host_execution_acceptance_smoke_l67232.py`
2. 长链 + 写文件 + 修复 + 打包闭环
   - `backend/project/run_agent.py --mock --once ...`
   - 新增 verifier：`scripts/verify_l6738_q18_write_fix_pack_loop.py`

## 新发现并修复的问题

### Q18-P1-001：HookBus 高频事件投影过慢

现象：`run_l6730_human_deepseek_full_chain_pressure_smoke.py` full 模式第 24 个场景失败，500 个工作台事件投影耗时超过阈值。  
根因：`HookBus.export_digest()` / `stats()` 在高频路径中反复对 HookRecord 做 `asdict()` 深拷贝。  
修复：
- `frontend/linyuanzhe_frontend/contracts/hook_bus.py`
- 为统计与 digest 增加缓存，新增事件时统一失效。
- digest 改为轻量字段串联后哈希，避免 dataclass 深拷贝。

### Q18-P1-002：真实主机执行 smoke 在 Linux/macOS 的 system_drive 场景误把状态写到 `/`

现象：真实主机 full smoke 的 `system_drive` 场景中，工作区为 `/`，Runtime 启动阶段尝试创建 `/.linyuanzhe`，导致 `PermissionError`。  
根因：桌面桥接把主机读取路径与 Runtime 状态路径绑定到同一个 workspace；active asset 读取函数也会用 artifact 写路径进行只读加载。  
修复：
- `desktop/linyuanzhe_local_runtime_bridge_l671.py`
  - 桥接 subprocess 强制使用 `python -S`。
  - 设置 `PYTHONNOUSERSITE=1`、`PYTHONDONTWRITEBYTECODE=1`，避免宿主 sitecustomize / artifact_tool 噪声与 pycache。
  - 将 `LINYUANZHE_STATE_DIR` / `TIANGONG_STATE_DIR` / PromptTrace 重定向到临时状态目录。
- `backend/project/tiangong_agent_runtime/learning_asset_activation.py`
  - `load_active_assets()` 改用只读路径解析。
  - 写入场景才创建 active asset state root。
  - 支持 `LINYUANZHE_STATE_DIR` / `TIANGONG_STATE_DIR` 覆盖状态根。

### Q18-P1-003：自适应修复成功后不会恢复执行原计划剩余步骤

现象：模拟 LLM 长链“写文件 → 修复 → 测试 → 打包 → 总结”时，质量检查失败触发一次修复并复检通过，但原计划后续打包步骤不会继续执行。  
根因：AdaptiveWorkLoop V1 只负责一次 repair plan；Runtime 在 repair 通过后直接收口，没有恢复执行原计划失败点之后的安全尾部。  
修复：
- `backend/project/tiangong_agent_runtime/runtime_entry.py`
  - 在自适应修复通过后，恢复执行原计划失败步骤之后的剩余步骤一次。
  - 不重跑失败步骤，不启动后台循环，仍保持“一次修复 + 一次受控恢复”的有界行为。
  - 公共投影过滤绝对路径和 `.linyuanzhe/reports/__pycache__` 等内部产物引用，避免 CLI 输出内部状态路径。

### Q18-P2-001：Mock Planner 写文件识别范围过窄，链式中文提示会把后续指令吞进文件内容

现象：`创建 CHANGELOG.txt 内容：Q18 marker；修复项目；运行测试；打包交付；输出总结` 会把“修复/测试/打包/总结”也写入 CHANGELOG。  
修复：
- `backend/project/tiangong_agent_shell/model_client_mock.py`
  - 写文件路径识别扩展到 `.txt/.md/.json/.py/.yml/.yaml/.toml`。
  - 中文链式提示中，`内容：...；修复/测试/打包/总结` 会只抽取内容片段，不吞后续计划指令。

## 新增 verifier

```bash
python -S scripts/verify_l6738_q18_write_fix_pack_loop.py
```

验证内容：
- mock LLM 长链进入 work 模式。
- 写入 `CHANGELOG.txt`。
- 对预置 `broken.py` 缺冒号错误执行一次自适应修复。
- 修复后恢复执行原计划剩余步骤。
- 生成 `dist/model_planner_demo.zip` 与 `.sha256`。
- ZIP 中包含 `CHANGELOG.txt` / `broken.py`，且不包含 `.linyuanzhe`、`reports`、`__pycache__`、`*.pyc`、绝对路径或反斜杠路径。
- verifier 不污染交付包根。

## 回归摘要

| 回归项 | 结果 |
|---|---:|
| `backend/project/run_agent.py --mock --status` | PASS |
| `scripts/verify_l6738_mock_llm_long_chain_cli.py` | PASS |
| `scripts/verify_l6738_q18_write_fix_pack_loop.py` | PASS |
| `backend/project/run_l67255_adaptive_work_loop_smoke.py` full | PASS |
| `backend/project/run_l6730_human_deepseek_full_chain_pressure_smoke.py` full | PASS，30/30 |
| `frontend/linyuanzhe_frontend/run_real_host_execution_acceptance_smoke_l67232.py` full | PASS |
| `frontend/linyuanzhe_frontend/run_frontend_humanized_longchain_qa_smoke_l67252.py` | PASS，80/80 |
| 包根 `.linyuanzhe/reports/__pycache__/*.pyc` | 0 |
