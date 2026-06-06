# L6.51 Provider Smoke CI Allowlist

CI 中无受控凭证时只能运行 mock/provider-contract 测试；有受控凭证时才运行真实在线 smoke。

## Allowlist Tools

1. `model_chat_adapter`
2. `build_l6_38_provider_integration`
3. `return_analysis`
4. `evaluate_quality_gate`
5. `audit_bridge_export`

## CI Rule

- 默认 CI：不要求真实 DeepSeek 凭证，不因缺凭证失败。
- 手动凭证 CI：必须读取受控环境变量，禁止写入报告。
- 所有日志必须走 `safe_logging` 脱敏。
