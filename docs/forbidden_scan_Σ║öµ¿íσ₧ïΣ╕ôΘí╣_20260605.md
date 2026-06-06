# Forbidden scan（五模型 hotfix3）

- status：pass
- blocking_findings：0
- inert_text_notes：9
- scanned_roots：tiangong_kernel/l1_ports, tiangong_kernel/l2_state, tiangong_kernel/l3_orchestration, tiangong_kernel/l4_action_grounding, tiangong_kernel/l5_plugin_host

说明：`api_key=` / `token=` 等字符串若只作为危险字段检测词表出现，归类为 inert_text_notes，不作为真实凭据读取或模型裸调。
