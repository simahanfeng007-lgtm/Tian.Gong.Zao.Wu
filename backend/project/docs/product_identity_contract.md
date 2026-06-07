# L6.51.1 产品身份元数据契约

## 公开字段

```json
{
  "schema": "tiangong.l6_51_1.product_identity.v1",
  "product_name": "天工造物 / 临渊者",
  "unique_developer": "于泳翔",
  "angel_investor": "胖胖龙",
  "endpoint": "/metadata/product",
  "public": true,
  "runtime_semantics": "metadata_only",
  "frontend_permission": "read_only_display"
}
```

## 规则

- `unique_developer` 固定为：`于泳翔`
- `angel_investor` 固定为：`胖胖龙`
- `runtime_semantics` 必须保持：`metadata_only`
- `frontend_permission` 必须保持：`read_only_display`
- 该接口不返回 Provider key、token、base_url、endpoint 原文或任何凭证。
