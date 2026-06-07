# FE01 STEP21 / L6.60 阻断项报告

## 当前阻断

1. `real Runtime instance smoke not executed`
2. `LINYUANZHE_RUNTIME_URL not provided`

## 阻断等级

- P1 / RC 合成前置阻断。
- 不影响本地契约回归与前端包体结构交接。
- 阻止声明真实 Runtime 联调已通过。

## 解阻方式

1. 启动真实 TiangongWangguan / Runtime。
2. 设置 `LINYUANZHE_RUNTIME_URL` 指向真实网关地址。
3. 执行：

```bash
python scripts/real_runtime_gate_l660.py --require-real
```

4. 当 `reports/real_runtime_gate_l660.json` 中 `ready_for_combine=true` 后，再进入安装包 RC 封装。
