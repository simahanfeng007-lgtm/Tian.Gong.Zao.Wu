# FE01 STEP23 / L6.62 运行观测台

本轮新增桌面端二级页「观测」，用于展示 Runtime SSE / Agent UI 事件的只读 Trace 投影。

## 范围

- 只读展示 run、planner、tool、quality_gate、audit、rollback、assistant、terminal、error 分类。
- 展示事件计数、last_seq、SSE 收口顺序、错误数量、待确认数量、预算与质量门摘要。
- run_id / task_id 只显示 digest。
- payload 只展示脱敏摘要。
- 不展示原始 prompt、密钥、端点、路径、完整工具参数。

## 边界

观测台没有任何执行权限：

- 不调用 Provider。
- 不调用工具。
- 不写长期记忆。
- 不写审计。
- 不应用回滚。
- 不绕过 QualityGate。

## 验证

```bash
python scripts/observability_preflight_l662.py
python scripts/verify_l662_release.py
```

真实 Runtime 解阻仍由 L6.61 的真实联调脚本负责。L6.62 只补运行观测能力，不改变 ready_for_combine 的判定规则。
