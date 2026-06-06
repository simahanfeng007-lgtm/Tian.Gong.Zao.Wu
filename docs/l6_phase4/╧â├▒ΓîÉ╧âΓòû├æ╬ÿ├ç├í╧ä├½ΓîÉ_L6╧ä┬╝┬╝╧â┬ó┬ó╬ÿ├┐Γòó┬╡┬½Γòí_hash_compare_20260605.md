# L6 第四阶段 Hash Compare

- `tiangong_kernel/l0_primitives`: old_files=58, new_files=58, added=0, removed=0, changed=0
- `tiangong_kernel/l1_ports`: old_files=65, new_files=65, added=0, removed=0, changed=0
- `tiangong_kernel/l2_state`: old_files=70, new_files=70, added=0, removed=0, changed=0
- `tiangong_kernel/l3_orchestration`: old_files=87, new_files=87, added=0, removed=0, changed=0
- `tiangong_kernel/l4_action_grounding`: old_files=187, new_files=187, added=0, removed=0, changed=0
- `tiangong_kernel/l4_execution`: old_files=38, new_files=38, added=0, removed=0, changed=0
- `tiangong_kernel/l5_plugin_host`: old_files=70, new_files=70, added=0, removed=0, changed=0
- `tiangong_kernel/l6_plugins/common`: old_files=24, new_files=24, added=0, removed=0, changed=0
- `tiangong_kernel/l6_plugins/mind`: old_files=23, new_files=23, added=0, removed=0, changed=0
- `tiangong_kernel/l6_plugins/__init__.py`: changed=True; reason=non-breaking export addition for cognitive_continuity.

结论：L0-L5、L6 common、L6 mind 均无新增、删除或变更；仅 L6 顶层 `__all__` 追加 cognitive_continuity 导出。
