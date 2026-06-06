# 五大模型官方文档 factsheet 摘要（hotfix3 P2/P3 最终修复 / 2026-06-05）

## DeepSeek V4

- provider_id：deepseek_v4
- 官方引用：`https://api-docs.deepseek.com/news/news260424`
- 默认模型：deepseek-v4-flash
- 支持模型：deepseek-v4-flash / deepseek-v4-pro
- 协议：OpenAI Chat Completions compatible / Anthropic compatible
- 上下文：1M tokens
- 最大输出：384K
- 支持：streaming、tool calls、JSON output、thinking/non-thinking、context caching
- 已知退役：deepseek-chat / deepseek-reasoner 按官方 V4 公告退役
- 未核验：多模态、文件/音频/视频输入、batch、安全拒绝 shape

## Xiaomi MiMo

- provider_id：mimo
- 官方引用：`https://mimo.mi.com/; https://platform.xiaomimimo.com/docs/en-US/quick-start/model; https://platform.xiaomimimo.com/docs/en-US/updates/model; https://platform.xiaomimimo.com/docs/en-US/price/pay-as-you-go; https://platform.xiaomimimo.com/docs/en-US/price/tokenplan/quick-access; https://platform.xiaomimimo.com/docs/en-US/price/tokenplan/price-comparison; https://platform.xiaomimimo.com/docs/en-US/quick-start/error-codes; https://platform.xiaomimimo.com/docs/en-US/quick-start/model-hyperparameters`
- 默认模型：mimo-v2.5-pro
- 模型 ID 口径：MiMo 模型 ID 一律小写；当前 supported_model_ids 为：mimo-v2.5-pro, mimo-v2.5, mimo-v2.5-asr, mimo-v2-flash, mimo-v2-pro, mimo-v2-omni。
- API 面：同时建模 `token_plan_api` 与 `ordinary_api`。Token Plan API Key 与 Pay-as-you-go ordinary API Key 按官方前缀区分，二者互相独立、不可混用。L4 仅保存 endpoint_ref / credential_scope_ref，不释放真实 endpoint 给插件。
- 官方能力证据：model/rate-limits 页确认 mimo-v2.5-pro、mimo-v2.5、mimo-v2-flash、mimo-v2.5-asr 等模型能力、上下文、输出与 RPM/TPM；model release 页确认 V2.5 系列发布时间和 1M 上下文；pay-as-you-go、token plan、error codes、model hyperparameters 已加入引用。
- 上下文：mimo-v2.5 / mimo-v2.5-pro 1M context；mimo-v2-flash 256K；ASR/TTS 以官方模型页为准。
- 最大输出：默认 factsheet 按文本主线 128K 建模；flash/ASR/TTS 子模型以官方模型页为准。
- 支持：streaming、function call、structured output、web search、thinking/full-modal ability（按模型差异）、多模态输入。
- 本地部署：open-weight / local branch 只能通过 service port 预留，不得在 L4 裸起推理进程。
- 未核验：JSON mode、file input、batch、普通 API 精确 endpoint、安全拒绝 shape。

## GLM-5.1

- provider_id：glm_5_1
- 官方引用：`https://docs.z.ai/cn/guides/llm/glm-5.1; https://docs.z.ai/cn/api-reference/model-api`
- 默认模型：glm-5.1
- 协议：OpenAI-compatible chat completions / Z.AI native 参数
- 上下文：200K
- 最大输出：128K / 131072 tokens
- 支持：streaming、thinking mode、function call、context cache、structured output
- 端点：general endpoint 与 coding endpoint 需区分
- 未核验：JSON mode、文件输入、batch、精确 rate limit、安全拒绝 shape

## MiniMax M3

- provider_id：minimax_m3
- 官方引用：`https://platform.minimax.io/docs/guides/models-intro; https://platform.minimax.io/docs/guides/text-ai-coding-tools; https://platform.minimax.io/docs/guides/pricing-token-plan`
- 默认模型：MiniMax-M3
- 协议：OpenAI-compatible / Anthropic-compatible
- 上下文：1M
- 最大输出：推荐 128K，参数文档给出更高上限
- 支持：streaming、tool/function calling、thinking、multimodal image/video、cache/pricing/rate-limit refs
- 未核验：structured output、JSON mode、文件输入、音频输入、batch、安全拒绝 shape

## GPT-5.5

- provider_id：gpt_5_5
- 官方引用：`https://developers.openai.com/api/docs/models/gpt-5.5; https://developers.openai.com/api/docs/guides/latest-model; https://developers.openai.com/api/docs/pricing`
- 默认模型：gpt-5.5
- 协议：OpenAI Responses API；Chat Completions 兼容情况需以后续官方文档为准
- 上下文：1,050,000 tokens
- 最大输出：128K
- 支持：streaming、function calling、structured outputs、reasoning.effort、text/image/file input、Responses built-in tools、prompt cache retention、Batch
- 未核验：Chat Completions 兼容、音频/视频输入、精确 rate limit 数值
