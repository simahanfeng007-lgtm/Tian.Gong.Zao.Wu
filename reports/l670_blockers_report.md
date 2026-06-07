# FE01 STEP31 / L6.70 阻断项报告

生成时间：2026-06-07T09:59:59

## 当前阻断项

1. real Runtime instance smoke not executed。
2. LINYUANZHE_RUNTIME_URL not provided。
3. ready_for_combine=false。
4. final_installer_allowed=false。
5. windows_installer_artifact_emitted=false。

## 阻断性质

这是外部真实 Runtime 环境阻断，不是 contract-server 回归失败。当前环境没有真实 TiangongWangguan / Runtime URL，因此不能执行真实 endpoint smoke，也不能把 RC 标为完成。

## 已修复的前置缺陷

- `real_runtime_gate_l660.py` 与 `rc_preflight_l659.py` 的 Provider 探测参数不匹配已修复。
- 已用本地无服务地址做参数兼容性探针：失败原因变为真实端点不可达 / SSE 未完成，而不是 argparse 参数错误。

## 解阻命令

Windows PowerShell：

```powershell
$env:LINYUANZHE_RUNTIME_URL="http://127.0.0.1:你的端口"
python scripts/real_runtime_unlock_l661.py --require-real --out reports/real_runtime_unlock_l670.json
python scripts/real_runtime_endpoint_smoke_l670.py --require-real
python scripts/verify_l670_release.py
```

Linux / macOS：

```bash
export LINYUANZHE_RUNTIME_URL="http://127.0.0.1:你的端口"
python3 scripts/real_runtime_unlock_l661.py --require-real --out reports/real_runtime_unlock_l670.json
python3 scripts/real_runtime_endpoint_smoke_l670.py --require-real
python3 scripts/verify_l670_release.py
```

## 不允许事项

- 不允许把 contract-server 结果写成真实联调通过。
- 不允许输出 exe/msi。
- 不允许写入 Provider 假 key / 假 endpoint。
- 不允许前端绕过 Runtime / QualityGate / HookBus。
