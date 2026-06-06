# 天工造物 v2 · 临渊者

**DeepSeek Native Cognitive Runtime** | 于泳翔 | 天使投资人：胖胖龙

## 架构

```
CLI Shell → RuntimeEntry → ExecutionSpine → Tool Registry
                ├── 记忆系统 (MemoryRecall / ForgetReview)
                ├── 情志引擎 (七情六欲 / EMA 临时+稳定两层)
                ├── 生命周期 (自由意志时钟 / 自主目标队列)
                ├── 四路径投影 → Planner 统一消费
                └── Provider 受控接入 (DeepSeek v4-pro/flash)
```

## 产品身份

| 字段 | 值 |
|------|-----|
| 产品名 | 天工造物 / 临渊者 |
| 开发者 | 于泳翔 |
| 天使投资人 | 胖胖龙 |
| 元数据端点 | /metadata/product |

## 快速开始

```bash
pip install openai pyyaml
export DEEPSEEK_API_KEY="sk-xxx"
python run_agent.py
```

## 许可证

Apache License 2.0
