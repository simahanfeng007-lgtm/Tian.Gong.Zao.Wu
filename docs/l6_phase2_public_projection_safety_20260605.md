# L6 第二阶段 Public Projection Safety

- checked_objects: L6PublicProjection, L6PublicProjection, L6PluginDiscoverableProjection, L6ContractPatchPublicProjection
- leak_count: 0
- negative_constructor_checks: {'raw_credential_rejected': True, 'external_endpoint_rejected': True, 'execution_marker_rejected': True}
- passed: True

检查具体泄露值/URL/凭证赋值/执行 marker；字段名如 contains_external_endpoint 属于安全布尔声明，不视为泄露。
