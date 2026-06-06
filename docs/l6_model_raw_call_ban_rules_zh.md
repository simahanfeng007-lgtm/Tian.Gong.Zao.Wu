# L6 插件裸调模型禁止规则说明

本规则为五大模型高适配专项的 L6 前置约束。L6 插件只允许声明模型能力需求，不允许直接连接 provider。

## 插件允许声明

- ModelCapabilityRequirement
- ModelProviderPreference
- ModelQualityRequirement
- ModelLatencyRequirement
- ModelContextRequirement
- ModelToolUseRequirement
- ModelMultimodalRequirement
- ModelCostPreference
- ModelFallbackPreference

## 插件禁止事项

1. 禁止 import openai / anthropic / google.genai / dashscope / zhipuai / minimax / deepseek。
2. 禁止使用 requests/httpx/urllib 直连模型域名。
3. 禁止写 provider base_url。
4. 禁止读取、保存或传递明文 provider key。
5. 禁止插件直接实例化 model client。
6. 禁止插件直接调用 L4 live adapter。
7. 禁止插件绕过 L3 生成 live dispatch。
8. 禁止插件绕过 L5 permit。
9. 插件只能消费 L4 标准化 ModelOutputEnvelope / ModelProviderFailureEnvelope。

## 扫描落点

新增模块：`tiangong_kernel/l5_plugin_host/model_capability_invariants.py`

核心函数：`scan_plugin_source_for_raw_model_access(source)`

核心不变量：

- PluginModelCapabilityRequirementOnlyInvariant
- NoPluginRawModelSDKInvariant
- NoPluginRawHTTPModelCallInvariant
