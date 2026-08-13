from __future__ import annotations

from collections.abc import Iterable

import networkx as nx
from networkx.algorithms.community.quality import modularity


def partition_modularity(graph: nx.Graph, communities: Iterable[set], *, weighted: bool = False) -> float:
    communities = list(communities)
    if len(communities) <= 1:
        return 0.0
    return float(modularity(graph, communities, weight="weight" if weighted else None))


def graph_edge_density(graph: nx.Graph) -> float:
    return float(nx.density(graph))


def top_betweenness_nodes(graph: nx.Graph, n: int = 3, *, weighted: bool = False):
    scores = nx.betweenness_centrality(graph, weight="weight" if weighted else None)
    return sorted(scores.items(), key=lambda item: item[1], reverse=True)[:n]


def overlap_summary(memberships: dict) -> dict[str, int]:
    labels = set()
    overlapping_nodes = 0
    overlap_labels = set()
    for _, memberships_for_node in memberships.items():
        labels.update(memberships_for_node)
        if len(memberships_for_node) > 1:
            overlapping_nodes += 1
            overlap_labels.update(memberships_for_node)
    return {
        "communities": len(labels),
        "overlapping_nodes": overlapping_nodes,
        "overlapping_communities": len(overlap_labels),
    }
