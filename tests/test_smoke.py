import networkx as nx

from acla.metrics import graph_edge_density, overlap_summary
from acla.nonoverlap import detect_nonoverlapping


def test_nonoverlap_smoke():
    graph = nx.karate_club_graph()
    labels, communities, score = detect_nonoverlapping(graph, iterations=10, seed=42)
    assert set(labels) == set(graph.nodes())
    assert sum(len(c) for c in communities) == graph.number_of_nodes()
    assert -0.5 <= score <= 1.0


def test_density():
    graph = nx.path_graph(4)
    assert abs(graph_edge_density(graph) - 0.5) < 1e-12


def test_overlap_summary():
    summary = overlap_summary({0: {0}, 1: {0, 1}, 2: {1}})
    assert summary == {"communities": 2, "overlapping_nodes": 1, "overlapping_communities": 2}
