# Q17 LLM 长链模拟 CLI 修复记录

## 背景

用户复测“模拟 LLM 进行长链工作”时，离线 mock 主脑路径容易暴露两个 CLI 级问题：

1. 中文长链提示如“检查项目并输出总结”未稳定激活 work/runtime 工具链，可能退回普通 `[MOCK] 已收到...` 聊天回显。
2. 包含“总结”的代码修复提示会被 mock planner 硬编码为读取 `README.md`，但当前交付包没有根目录 `README.md`，从而产生 `path_not_found` / `failed_recoverable`。
3. `run_python_quality_check` 原先通过 subprocess 调用 `compileall`，会输出绝对 workspace 路径，并生成 `__pycache__/*.pyc`，不适合离线长链验收和干净交付树复测。

## 修复

- `backend/project/tiangong_agent_shell/model_client_mock.py`
  - 扩展中文/英文 work markers：检查、验证、诊断、测试、质检、定位、模拟、长链、工作、项目等。
  - `总结/summary` 不再触发固定 `README.md` 读取，而是使用 `return_analysis` 做长链收口。
  - 仅显式 read/readme 请求才走 `read_file`。

- `backend/project/tiangong_agent_runtime/adapters/python_test_adapter.py`
  - `compileall` 路径改为内存语法编译检查：不写 `__pycache__` / `*.pyc`。
  - 输出相对 workspace 摘要，不再打印绝对临时路径。
  - pytest subprocess 增加 `PYTHONDONTWRITEBYTECODE=1`，并对 workspace 绝对路径做脱敏。

- `scripts/verify_l6738_mock_llm_long_chain_cli.py`
  - 新增 CLI 级离线 verifier。
  - 覆盖两个中文长链 mock 提示。
  - 要求 rc=0、出现 `[工作链] ... failures=0`、无未配置模型提示、无 `path_not_found`、无 README.md 误读、无绝对临时路径、无 pycache/pyc 污染。

## 复测摘要

- `python -S scripts/verify_l6738_mock_llm_long_chain_cli.py`：PASS
- `LINYUANZHE_RUN_FULL_SMOKE=1 python -S backend/project/run_l67255_adaptive_work_loop_smoke.py`：PASS
- `LINYUANZHE_RUN_FULL_SMOKE=1 python -S backend/project/run_l6730_human_deepseek_full_chain_pressure_smoke.py`：PASS
- `python -S frontend/linyuanzhe_frontend/run_frontend_humanized_longchain_qa_smoke_l67252.py`：PASS
