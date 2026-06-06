# 天工造物 L3 第三阶段开发日志

日期：2026-06-03
阶段：Skill 直显与 ToolGroup 释放编排评分

## 开发基线

采用 L3 第二阶段质检后修复版作为基座：`tiangong_l3_phase2_quality_repair_package_20260603.zip`。该基座内部路径为 ASCII 稳定路径，避免第二阶段质检中指出的 zip 中文文件名编码问题。

## 本阶段新增源码

1. `tiangong_kernel/l3_orchestration/skill_visibility.py`
   - 新增 Skill 直显请求引用、显示候选、显示排序、显示建议、选择建议、激活建议、停用建议、不匹配建议、澄清建议、Skill 状态转移建议。
   - 新增稳定 Skill 候选排序函数 `build_skill_display_ranking`。

2. `tiangong_kernel/l3_orchestration/tool_group_release_advice.py`
   - 新增 ToolGroup 解析请求引用、释放候选、释放排序、释放建议、最小充分释放建议、租约请求建议、ToolGroup 状态转移建议。
   - 新增稳定 ToolGroup 释放候选排序函数 `build_tool_group_release_ranking`。

3. `tiangong_kernel/l3_orchestration/skill_tool_math.py`
   - 新增 Skill / ToolGroup 评分基础对象与评分项：SkillMatchScore、SkillRelevanceScore、SkillContinuityScore、SkillReadinessScore、SkillRiskAwarenessHint、ToolGroupNeedScore、ToolGroupMinimalityScore、ToolExposureCostScore、ToolGroupExposureCostScore、ToolGroupReadinessScore、ToolGroupCompletenessScore、ToolGroupSufficiencyScore、ReversibilityIndex、StabilityIndex。
   - 新增 SkillToolMathInput、SkillToolMathResult、SkillToolRecommendation。
   - 新增轻量、确定性、可解释评分函数，并映射到第一阶段 MathScoreVector。

4. `tiangong_kernel/l3_orchestration/skill_tool_route.py`
   - 新增 SkillToolRouteCandidate、SkillToolRouteRanking。
   - 新增 RunSkillDisplayAdvice、TaskSkillSelectionAdvice、TurnSkillActivationAdvice、StepToolGroupReleaseAdvice。
   - 新增 SkillToolResumeAdvice、SkillToolInterruptionAdvice、SkillToolContinuityAdvice。
   - 新增稳定路径排序函数 `build_skill_tool_route_ranking`。

5. `tiangong_kernel/l3_orchestration/skill_tool_transition.py`
   - 新增 SkillToolTransitionKind、SkillToolStateTransitionSuggestion。
   - 只输出状态转移建议，不修改 L2，不触发下游层。

6. `tiangong_kernel/l3_orchestration/__init__.py`
   - 追加第三阶段公共导出。

## 本阶段新增测试

1. `tests/l3_phase3_builders.py`
2. `tests/test_l3_phase3_imports_and_compatibility.py`
3. `tests/test_l3_phase3_skill_visibility_advice.py`
4. `tests/test_l3_phase3_tool_group_release_advice.py`
5. `tests/test_l3_phase3_math_scoring_and_ranking.py`
6. `tests/test_l3_phase3_serialization_hash_stability.py`
7. `tests/test_l3_phase3_boundary_no_execution.py`

## 边界说明

本阶段所有新增对象均为 frozen + slots dataclass 或 Enum。评分函数为纯内存、确定性、可解释的建议生成，不调用模型、不调用工具、不访问网络、不执行 shell、不读写真实文件、不访问数据库、不授予租约、不进行 L5 边界裁决、不发起 L4 执行请求。

## 验证摘要

1. `python -m compileall -q tiangong_kernel tests`：通过。
2. L3 第三阶段目标测试：17 passed。
3. `python -m pytest -q tests -k 'l3_phase1 or l3_phase2 or l3_phase3'`：47 passed, 502 deselected。
4. `python -m pytest -q tests`：549 passed。
5. L0/L1/L2 Python 源码 hash 对比：MATCH。
