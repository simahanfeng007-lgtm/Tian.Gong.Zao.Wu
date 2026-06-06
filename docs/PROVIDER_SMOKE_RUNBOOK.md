# Provider Smoke Runbook

本 Runbook 固化 L6.50 真实 DeepSeek Provider 受控接入烟测流程。真实在线烟测只能在受控凭证环境执行，不允许将 API Key、Bearer、endpoint 原文写入源码、日志、报告、fixture 或 zip。

## 凭证来源

允许：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_BASE_URL`
- `DEEPSEEK_MODEL`
- 或 canonical `TIANGONG_API_KEY / TIANGONG_BASE_URL / TIANGONG_MODEL`

禁止：

- 前端裸调 Provider SDK。
- 测试脚本裸调 Provider SDK。
- 临时工具裸调 Provider SDK。
- 任何明文凭证落盘。

## 必跑项

1. Mock Provider 合同烟测。
2. deepseek-v4-pro 基础对话。
3. deepseek-v4-pro Plan 生成。
4. deepseek-v4-flash 快速响应。
5. 凭证脱敏扫描。

## L6.50 冻结结果

| 项目 | 结果 |
|---|---|
| Mock 烟测 | 7/7 pass |
| 真实在线烟测 | 4/4 pass |
| deepseek-v4-pro 基础对话 | 2.3s pass |
| deepseek-v4-pro Plan 生成 | 5.0s pass |
| deepseek-v4-flash | 0.8s pass |
| 凭证脱敏 | 无泄漏 |
| CI allowlist | 5 工具 |

## 失败处理

- 401/403：标记 `provider_auth_failed`，只返回用户安全摘要。
- 429：标记 `provider_rate_limited`，允许降级或稍后重试。
- timeout：标记 `provider_timeout`，不得阻塞 Runtime 收口。
- 非 JSON/空响应：进入 `plan_schema` 失败审计或虚拟返回，不绕 QualityGate。
- 疑似 A5：QualityGate 必须硬拦截或人工确认。
