# FE01 STEP31 / L6.70 真实 Runtime 联调解阻说明

## 目标

L6.70 只处理真实 Runtime 联调与 RC 解阻，不构建正式 Windows 安装包。

必须满足：

1. `LINYUANZHE_RUNTIME_URL` 指向真实 TiangongWangguan / Runtime。
2. `/health/runtime`、`/metadata/product`、`/settings/provider` 等核心只读端点可读。
3. Provider 设置默认只读探测，不向真实 Runtime 写入假 key / 假 endpoint。
4. `/chat/stream-events` 的 SSE 事件满足 `assistant_final -> run_terminal`。
5. 文件传输、工作区授权、连接器注册、Session 恢复/搜索、确认请求、中断/停止/复位均只作为 Runtime envelope，由 Runtime / QualityGate / HookBus 裁决。
6. 报告不得泄露 Runtime URL 明文、Provider Key、Bearer、endpoint secret。

## Windows PowerShell

```powershell
$env:LINYUANZHE_RUNTIME_URL="http://127.0.0.1:你的端口"
python scripts/real_runtime_unlock_l661.py --require-real --out reports/real_runtime_unlock_l670.json
python scripts/real_runtime_endpoint_smoke_l670.py --require-real
python scripts/verify_l670_release.py
```

## Windows CMD

```bat
set LINYUANZHE_RUNTIME_URL=http://127.0.0.1:你的端口
python scripts\real_runtime_unlock_l661.py --require-real --out reports\real_runtime_unlock_l670.json
python scripts\real_runtime_endpoint_smoke_l670.py --require-real
python scripts\verify_l670_release.py
```

## Linux / macOS

```bash
export LINYUANZHE_RUNTIME_URL="http://127.0.0.1:你的端口"
python3 scripts/real_runtime_unlock_l661.py --require-real --out reports/real_runtime_unlock_l670.json
python3 scripts/real_runtime_endpoint_smoke_l670.py --require-real
python3 scripts/verify_l670_release.py
```

## 当前硬阻断

如果没有 `LINYUANZHE_RUNTIME_URL`：

- `ready_for_combine=false`
- `real_runtime_smoke_passed=false`
- `final_installer_allowed=false`
- `windows_installer_artifact_emitted=false`

不允许将 contract-server 回归结果标记为真实联调通过。
