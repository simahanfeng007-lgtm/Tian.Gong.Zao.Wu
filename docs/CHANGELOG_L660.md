# FE01 STEP21 / L6.60 变更记录

## 新增

1. `scripts/real_runtime_gate_l660.py`：真实 Runtime 硬闸口。缺少真实地址时输出阻断报告；`--require-real` 下返回非零。
2. `scripts/verify_l660_release.py`：一键执行 compileall、contract-server preflight、扫描、真实闸口阻断检查。
3. `launchers/start_linyuanzhe_rc.py`：新增 `--real-gate` 与 `--runtime-url` 参数，real 模式启动前强制跑真实闸口。
4. `launchers/run_real_runtime_gate_l660.bat` / `.sh`：真实闸口快捷脚本。
5. `docs/REAL_RUNTIME_GATE_L660.md`：真实接入说明。

## 未做

1. 未改后端核心主链。
2. 未让前端直接调用 Provider 或工具。
3. 未把 contract-server 结果伪装为真实 Runtime 联调结果。
4. 未写入任何 Provider 凭证或真实 Runtime 地址明文。

## 当前状态

在未提供真实 `LINYUANZHE_RUNTIME_URL` 的环境中，本包应表现为：验证通过、真实联调阻断、`ready_for_combine=false`。
