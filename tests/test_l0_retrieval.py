import tiangong_kernel.l0_primitives.retrieval as module
from phase8_helpers import assert_enum_values, assert_module_dataclasses
from tiangong_kernel.l0_primitives.retrieval import IndexKind, IndexState, QueryKind, RetrievalKind, RetrievalState


def test_l0_retrieval_objects_construct_freeze_serialize_hash_and_enum_values():
    assert_module_dataclasses(module)
    assert_enum_values(IndexKind, {'FULL_TEXT': 'full_text', 'HYBRID': 'hybrid'})
    assert_enum_values(IndexState, {'PROPOSED': 'proposed', 'STALE': 'stale'})
    assert_enum_values(QueryKind, {'KEYWORD': 'keyword', 'DIAGNOSTIC': 'diagnostic'})
    assert_enum_values(RetrievalKind, {'MEMORY_RETRIEVAL': 'memory_retrieval', 'HYBRID_RETRIEVAL': 'hybrid_retrieval'})
    assert_enum_values(RetrievalState, {'AUTHORIZED': 'authorized', 'EMPTY': 'empty'})
