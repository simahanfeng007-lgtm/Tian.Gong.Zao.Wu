from l5_phase5_helpers import valid_dependency_graph


def test_dependency_graph_has_only_explicit_nodes_edges():
    graph = valid_dependency_graph()
    assert graph.node_refs == ("node:a", "node:b")
    assert graph.edge_refs == (("node:b", "node:a", "edge:requires"),)
    assert not hasattr(graph, "package_path")
    assert not hasattr(graph, "module_path")
