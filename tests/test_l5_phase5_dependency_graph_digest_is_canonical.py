from l5_phase5_helpers import valid_dependency_graph


def test_dependency_graph_digest_is_stable_for_edge_order():
    a = valid_dependency_graph(edge_refs=(("node:b", "node:a", "edge:requires"), ("node:c", "node:a", "edge:optional")))
    b = valid_dependency_graph(edge_refs=(("node:c", "node:a", "edge:optional"), ("node:b", "node:a", "edge:requires")))
    assert a.edge_refs == b.edge_refs
    assert a.graph_digest == b.graph_digest


def test_dependency_graph_digest_changes_on_content_change():
    a = valid_dependency_graph()
    b = valid_dependency_graph(node_refs=("node:a", "node:c"))
    assert a.graph_digest != b.graph_digest
