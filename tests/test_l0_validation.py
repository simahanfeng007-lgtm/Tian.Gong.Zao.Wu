import tiangong_kernel.l0_primitives.validation as module
from phase8_helpers import assert_enum_values, assert_module_dataclasses
from tiangong_kernel.l0_primitives.validation import TestKind, ValidationKind, VerificationKind, AssertionKind, TestState, ValidationState, VerificationState


def test_l0_validation_objects_construct_freeze_serialize_hash_and_enum_values():
    assert_module_dataclasses(module)
    assert_enum_values(TestKind, {'UNIT': 'unit', 'PERFORMANCE': 'performance'})
    assert_enum_values(ValidationKind, {'USER_REQUIREMENT': 'user_requirement', 'RECOVERY_VALIDATION': 'recovery_validation'})
    assert_enum_values(VerificationKind, {'CONTRACT_VERIFICATION': 'contract_verification', 'TOOL_RESULT_VERIFICATION': 'tool_result_verification'})
    assert_enum_values(AssertionKind, {'STRUCTURAL': 'structural', 'SAFETY': 'safety'})
    assert_enum_values(TestState, {'READY': 'ready', 'SKIPPED': 'skipped'})
    assert_enum_values(ValidationState, {'PASSED': 'passed', 'FLAKY': 'flaky'})
    assert_enum_values(VerificationState, {'BLOCKED': 'blocked', 'ARCHIVED': 'archived'})
