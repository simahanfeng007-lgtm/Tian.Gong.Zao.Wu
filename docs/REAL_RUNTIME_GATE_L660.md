# FE01 STEP21 / L6.60 真实 Runtime 接入硬闸口

本轮目的：把 STEP20 的 RC 前置合成包推进到“真实 Runtime 可接入、可阻断、可诊断”的状态。contract-server 仍可用于前端/契约回归，但不能替代真实 TiangongWangguan / Runtime 烟测。

## 不变边界

- Runtime 仍是唯一执行调度中枢。
- TiangongWangguan 仍是统一网关入口。
- 前端只渲染、提交请求、展示回执。
- 前端不得直接调用 Provider、工具、长期记忆、审计写入、回滚应用。
- 产品身份元数据必须保留：唯一开发者「于泳翔」，天使投资人「胖胖龙」。
- `assistant_final` 必须先于 `run_terminal`。
- A5 极高危必须硬拦截或人工确认。

## 使用方式

### 1. 仅做本地契约回归

```bash
python scripts/verify_l660_release.py
```

该命令允许真实 Runtime 缺失，但会在报告中保留阻断项：`real Runtime instance smoke not executed`。

### 2. 运行真实 Runtime 硬闸口

Linux / macOS：

```bash
export LINYUANZHE_RUNTIME_URL=http://127.0.0.1:8000
python scripts/real_runtime_gate_l660.py --require-real
```

Windows PowerShell：

```powershell
$env:LINYUANZHE_RUNTIME_URL="http://127.0.0.1:8000"
python scripts\real_runtime_gate_l660.py --require-real
```

报告只记录 Runtime 地址 digest，不记录明文地址。Provider 凭证仍必须留在后端/安装器安全入口，不进入前端日志、报告或 zip。

### 3. 统一启动器 real 模式

```bash
python launchers/start_linyuanzhe_rc.py --mode real --preflight-only
```

或直接：

```bash
python launchers/start_linyuanzhe_rc.py --real-gate
```

真实闸口通过后，`--mode real` 才会继续启动桌面前端；否则启动器返回阻断状态。

## L6.60 判定

- `ready_for_combine=true`：真实 Runtime 地址存在，真实 preflight 通过，contract-server 未参与替代，身份/Provider/SSE/边界全部通过。
- `ready_for_combine=false`：仍可作为 RC 前置交接包，但不能声明真实联调已通过。

## 输出报告

- `reports/real_runtime_gate_l660.json`
- `reports/rc_preflight_l660_real_runtime.json`（仅在提供真实 Runtime 时生成）
- `reports/validation_summary_l660.json`
