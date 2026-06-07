# FE01 STEP22 / L6.61 真实 Runtime 联调解阻

## 目标

本步骤只解决一个问题：用真实 TiangongWangguan / Runtime 地址解除 `ready_for_combine=false`。没有真实地址时，脚本必须阻断，不能用 contract-server 伪造。

## 命令

Linux / macOS：

```bash
export LINYUANZHE_RUNTIME_URL="真实 Runtime 地址"
python scripts/real_runtime_unlock_l661.py --require-real
```

Windows PowerShell：

```powershell
$env:LINYUANZHE_RUNTIME_URL="真实 Runtime 地址"
python scripts/real_runtime_unlock_l661.py --require-real
```

## Provider 设置安全变化

L6.60 的真实闸口会复用前端探针。L6.61 已修正为：真实 Runtime 默认只读检查 Provider 投影，不向真实配置写入样例值。

只有显式指定以下模式时才会提交 Provider 写入烟测：

```bash
export LINYUANZHE_PROVIDER_WRITE_MODE="smoke"
export LINYUANZHE_PROVIDER_SMOKE_KEY="专用烟测凭证"
export LINYUANZHE_PROVIDER_SMOKE_BASE_URL="专用烟测服务地址"
python scripts/real_runtime_unlock_l661.py --require-real --provider-write-mode smoke
```

报告仍只写 digest 和状态，不写 Runtime 地址、Provider 凭证或 Provider 服务地址明文。

## 解阻条件

1. `/health/runtime` 可读。
2. `/metadata/product` 可读，且产品身份保留：唯一开发者 `于泳翔`，天使投资人 `胖胖龙`。
3. `/settings/provider` 可读，且只返回脱敏投影。
4. `/chat/stream-events` 可完成只读 smoke。
5. SSE 收口顺序仍为 `assistant_final -> run_terminal`。
6. 前端边界仍为只渲染、提交请求、展示回执，不裸调 Provider、工具、记忆、审计、回滚。

## 仍然禁止

- 用 contract-server 代替真实 Runtime 结果。
- 在报告、日志、fixture、zip 中写 Runtime 地址或 Provider 凭证明文。
- 前端绕过 TiangongWangguan 或 Runtime。
- 前端直接调用 Provider SDK、工具、记忆、审计、回滚。
