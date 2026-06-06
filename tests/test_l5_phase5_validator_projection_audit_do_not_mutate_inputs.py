import copy
from l5_phase5_helpers import all_valid_declarations, validate_all, valid_projection, valid_audit_index


def test_validator_projection_audit_do_not_mutate_inputs():
    data = all_valid_declarations()
    before = copy.deepcopy(data)
    report = validate_all(**data)
    projection = valid_projection()
    index = valid_audit_index()
    assert report.passed
    assert projection.projection_digest
    assert index.audit_digest
    assert data == before
