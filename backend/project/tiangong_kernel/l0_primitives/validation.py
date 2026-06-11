"""L0 测试、校验、验证、评估与回归事实语言原语。

本模块在 L0 中的职责：定义测试、需求校验、规格验证、断言、评估、覆盖和回归引用。
本模块只表达：验证相关事实引用与状态。
本模块明确不做：测试执行、模型评测、形式化验证、运行时验证或性能测量。
禁止事项：不得启动测试框架，不得执行断言，不得运行评测或基线检测。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from .identity import RefId, TypedRef

class TestKind(str, Enum):
    """测试类别：表达测试事实类型；UNKNOWN 表示测试类别未知。"""
    UNIT="unit"; INTEGRATION="integration"; SYSTEM="system"; STRUCTURAL="structural"; REGRESSION="regression"; PROPERTY="property"; SCENARIO="scenario"; RECOVERY="recovery"; SECURITY="security"; PERFORMANCE="performance"; UNKNOWN="unknown"
class ValidationKind(str, Enum):
    """校验类别：表达是否符合需求、场景或用户意图；UNKNOWN 表示校验类别未知。"""
    USER_REQUIREMENT="user_requirement"; GOAL_SATISFACTION="goal_satisfaction"; ARTIFACT_VALIDATION="artifact_validation"; DATA_VALIDATION="data_validation"; SCHEMA_VALIDATION="schema_validation"; COMPATIBILITY_VALIDATION="compatibility_validation"; RECOVERY_VALIDATION="recovery_validation"; UNKNOWN="unknown"
class VerificationKind(str, Enum):
    """验证类别：表达是否满足规格、合约、约束或不变量；UNKNOWN 表示验证类别未知。"""
    CONTRACT_VERIFICATION="contract_verification"; CONSTRAINT_VERIFICATION="constraint_verification"; INVARIANT_VERIFICATION="invariant_verification"; PRECONDITION_CHECK="precondition_check"; POSTCONDITION_CHECK="postcondition_check"; RUNTIME_VERIFICATION="runtime_verification"; FORMAL_VERIFICATION="formal_verification"; TOOL_RESULT_VERIFICATION="tool_result_verification"; UNKNOWN="unknown"
class AssertionKind(str, Enum):
    """断言类别：表达可判定断言的语义类型；UNKNOWN 表示断言类别未知。"""
    STRUCTURAL="structural"; BEHAVIORAL="behavioral"; CONTRACT="contract"; INVARIANT="invariant"; RESULT="result"; SAFETY="safety"; UNKNOWN="unknown"
class TestState(str, Enum):
    """测试状态：表达测试事实生命周期；UNKNOWN 表示状态未知。"""
    PROPOSED="proposed"; READY="ready"; RUNNING="running"; PASSED="passed"; FAILED="failed"; PARTIAL="partial"; BLOCKED="blocked"; FLAKY="flaky"; SKIPPED="skipped"; ARCHIVED="archived"; UNKNOWN="unknown"
class ValidationState(str, Enum):
    """校验状态：表达校验事实生命周期；UNKNOWN 表示状态未知。"""
    PROPOSED="proposed"; READY="ready"; RUNNING="running"; PASSED="passed"; FAILED="failed"; PARTIAL="partial"; BLOCKED="blocked"; FLAKY="flaky"; SKIPPED="skipped"; ARCHIVED="archived"; UNKNOWN="unknown"
class VerificationState(str, Enum):
    """验证状态：表达验证事实生命周期；UNKNOWN 表示状态未知。"""
    PROPOSED="proposed"; READY="ready"; RUNNING="running"; PASSED="passed"; FAILED="failed"; PARTIAL="partial"; BLOCKED="blocked"; FLAKY="flaky"; SKIPPED="skipped"; ARCHIVED="archived"; UNKNOWN="unknown"
@dataclass(frozen=True, slots=True)
class TestRef:
    """测试引用。作用：表达对组件、运行、计划、效果、产物、插件、迁移、恢复或系统行为的测试事实引用；所属 L0 边界：只保存 test_id、kind 与 state；不能执行测试。字段：value 为 test_id。"""
    value: RefId; kind: TestKind=TestKind.UNKNOWN; state: TestState=TestState.UNKNOWN; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("TestRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class TestResultRef:
    """测试结果引用。作用：表达测试结果集合引用；所属 L0 边界：只保存 result_id 与 test_ref；不能运行测试。字段：value 为结果引用 ID。"""
    value: RefId; test_ref: TestRef|None=None; passed: bool|None=None; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("TestResultRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class ValidationRef:
    """校验引用。作用：表达是否符合需求、场景或用户意图的校验事实；所属 L0 边界：只保存 validation_id、kind 与 state；不能执行校验。字段：kind 为校验类别。"""
    value: RefId; kind: ValidationKind=ValidationKind.UNKNOWN; state: ValidationState=ValidationState.UNKNOWN; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("ValidationRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class VerificationRef:
    """验证引用。作用：表达是否满足规格、合约、约束或不变量的验证事实；所属 L0 边界：只保存 verification_id、kind 与 state；不能执行验证。字段：kind 为验证类别。"""
    value: RefId; kind: VerificationKind=VerificationKind.UNKNOWN; state: VerificationState=VerificationState.UNKNOWN; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("VerificationRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AssertionRef:
    """断言引用。作用：表达可判定断言引用；所属 L0 边界：只保存 assertion_id、kind 与 target_ref；不能执行断言。字段：kind 为断言类别。"""
    value: RefId; kind: AssertionKind=AssertionKind.UNKNOWN; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AssertionRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class AssertionResultRef:
    """断言结果引用。作用：表达断言结果引用事实；所属 L0 边界：只保存 result_id 与 assertion_ref；不能判断断言。字段：passed 为布尔结果事实。"""
    value: RefId; assertion_ref: AssertionRef|None=None; passed: bool|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("AssertionResultRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class EvaluationRef:
    """评估引用。作用：表达对模型、Agent、Run、Skill、工具链或系统表现的评估事实；所属 L0 边界：只保存 evaluation_id 与 target_ref；不能执行评估。字段：value 为评估引用 ID。"""
    value: RefId; target_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("EvaluationRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class EvaluationResultRef:
    """评估结果引用。作用：表达评估结果引用事实；所属 L0 边界：只保存 result_id 与 evaluation_ref；不能计算评分。字段：score_ref 为分值引用。"""
    value: RefId; evaluation_ref: EvaluationRef|None=None; score_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("EvaluationResultRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class CoverageRef:
    """覆盖引用。作用：表达测试或验证覆盖范围引用；所属 L0 边界：只保存 coverage_id 与 target_ref；不能计算覆盖率。字段：value 为覆盖引用 ID。"""
    value: RefId; target_ref: TypedRef|None=None; evidence_refs: tuple[TypedRef,...]=field(default_factory=tuple); schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("CoverageRef.schema_version cannot be empty")
@dataclass(frozen=True, slots=True)
class RegressionRef:
    """回归引用。作用：表达与历史基线相比是否退化的事实引用；所属 L0 边界：只保存 regression_id 与 baseline_ref；不能检测退化。字段：baseline_ref 为历史基线引用。"""
    value: RefId; baseline_ref: TypedRef|None=None; current_ref: TypedRef|None=None; schema_version: str="0.1"
    def __post_init__(self)->None:
        if not self.schema_version: raise ValueError("RegressionRef.schema_version cannot be empty")

# 防止测试框架把以 Test 开头的 L0 枚举/引用误识别为测试类。
TestKind.__test__ = False
TestState.__test__ = False
TestRef.__test__ = False
TestResultRef.__test__ = False
