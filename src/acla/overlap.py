"""Exploratory overlap-aware A-CLA extension.

Derived from the recovered historical `Code/Overlap/A-CLA_refin_01_01.py`.
The final manuscript frames overlap analysis as exploratory and the core A-CLA
method as non-overlapping. This module is therefore explicitly an extension.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Hashable, Optional

import networkx as nx
import numpy as np
from networkx.algorithms.community.quality import modularity as nx_modularity


def _communities_from_partition(partition: dict) -> list[set]:
    by_label: dict[int, set] = defaultdict(set)
    for node, label in partition.items():
        by_label[label].add(node)
    return [c for c in by_label.values() if c]


def _partition_from_communities(communities: list[set]) -> dict:
    return {node: cid for cid, comm in enumerate(communities) for node in comm}


def _modularity(graph: nx.Graph, partition: dict, use_weights: bool) -> float:
    communities = _communities_from_partition(partition)
    if len(communities) <= 1:
        return 0.0
    return nx_modularity(graph, communities, weight="weight" if use_weights else None)


def _normalize01(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    lo, hi = float(values.min()), float(values.max())
    if hi - lo < 1e-12:
        return np.zeros_like(values)
    return (values - lo) / (hi - lo)


def _adaptive_alpha(
    graph: nx.Graph,
    *,
    use_weights: bool,
    alpha_min: float,
    alpha_max: float,
    alpha_base: float,
    alpha_degree: float,
    alpha_betweenness: float,
) -> dict:
    weight_name = "weight" if use_weights else None
    degrees = dict(graph.degree(weight=weight_name))
    max_degree = max(degrees.values()) if degrees else 1.0
    bc = nx.betweenness_centrality(graph, weight=weight_name, normalized=True)
    nodes = list(graph.nodes())
    deg_arr = np.array([degrees[n] for n in nodes], dtype=float)
    bc_arr = np.array([bc[n] for n in nodes], dtype=float)
    deg_norm = deg_arr / (max_degree if max_degree > 0 else 1.0)
    bc_norm = (bc_arr - bc_arr.min()) / (bc_arr.max() - bc_arr.min() + 1e-12)
    alpha = alpha_base + alpha_degree * deg_norm + alpha_betweenness * bc_norm
    alpha = np.clip(alpha, alpha_min, alpha_max)
    return {node: float(value) for node, value in zip(nodes, alpha)}


def _local_scores(graph: nx.Graph, node, labels: dict, community_count: int, use_weights: bool) -> np.ndarray:
    scores = np.zeros(community_count, dtype=float)
    total = 0.0
    for neighbor in graph.neighbors(node):
        weight = float(graph[node][neighbor].get("weight", 1.0)) if use_weights else 1.0
        scores[labels[neighbor]] += weight
        total += weight
    if total > 0:
        scores /= total
    return scores


def _global_gains(graph: nx.Graph, labels: dict, node, community_count: int, current_q: float, use_weights: bool) -> np.ndarray:
    gains = np.zeros(community_count, dtype=float)
    base = labels[node]
    for candidate in range(community_count):
        if candidate == base:
            continue
        moved = dict(labels)
        moved[node] = candidate
        gains[candidate] = _modularity(graph, moved, use_weights) - current_q
    return gains


def _update_probability(vector: np.ndarray, action: int, alpha: float) -> np.ndarray:
    target = np.zeros_like(vector)
    target[action] = 1.0
    return (1.0 - alpha) * vector + alpha * target


def detect_overlap_extension(
    graph: nx.Graph,
    *,
    iterations: int = 300,
    seed: int = 42,
    use_weights: bool = True,
    beta_global: float = 0.35,
    alpha_min: float = 0.03,
    alpha_max: float = 0.25,
    alpha_base: float = 0.03,
    alpha_degree: float = 0.12,
    alpha_betweenness: float = 0.10,
    convergence_tolerance: float = 0.01,
    convergence_patience: int = 8,
    new_community_penalty: float = 0.05,
    tau: float = 0.30,
    delta: float = 0.05,
) -> tuple[list[set], dict, dict, dict]:
    """Run the recovered exploratory overlap-aware extension.

    Returns `(overlapping_communities, memberships, probabilities, hard_labels)`.
    """
    # The recovered script creates a NumPy RNG but its action choice is deterministic argmax.
    np.random.default_rng(seed)
    nodes = list(graph.nodes())
    n_nodes = len(nodes)
    hard_labels = {node: i for i, node in enumerate(nodes)}
    community_count = n_nodes
    probabilities = {
        node: np.eye(1, community_count, k=hard_labels[node]).ravel()
        for node in nodes
    }
    alpha_map = _adaptive_alpha(
        graph,
        use_weights=use_weights,
        alpha_min=alpha_min,
        alpha_max=alpha_max,
        alpha_base=alpha_base,
        alpha_degree=alpha_degree,
        alpha_betweenness=alpha_betweenness,
    )

    patience = convergence_patience
    for _ in range(1, iterations + 1):
        communities = _communities_from_partition(hard_labels)
        community_count = len(communities)
        hard_labels = _partition_from_communities(communities)
        current_q = _modularity(graph, hard_labels, use_weights)
        changed = 0

        for node in nodes:
            local = _local_scores(graph, node, hard_labels, community_count, use_weights)
            global_gain = _global_gains(graph, hard_labels, node, community_count, current_q, use_weights)
            local = np.append(local, new_community_penalty)
            global_gain = np.append(global_gain, 0.0)
            normalized_global = _normalize01(global_gain)
            combined = (1.0 - beta_global) * local + beta_global * normalized_global
            action = int(np.argmax(combined)) if combined.size else 0

            if action == community_count:
                target_label = max(hard_labels.values()) + 1
            else:
                target_label = action

            vector = probabilities[node]
            required = community_count + 1
            if vector.shape[0] != required:
                resized = np.zeros(required, dtype=float)
                length = min(vector.shape[0], community_count)
                resized[:length] = vector[:length]
                vector = resized
            probabilities[node] = _update_probability(vector, action, alpha_map[node])

            previous = hard_labels[node]
            hard_labels[node] = target_label
            if previous != target_label:
                changed += 1

        changed_fraction = changed / max(n_nodes, 1)
        if changed_fraction <= convergence_tolerance:
            patience -= 1
        else:
            patience = convergence_patience
        if patience <= 0:
            break

    communities = _communities_from_partition(hard_labels)
    hard_labels = _partition_from_communities(communities)

    memberships: dict[Hashable, set[int]] = {}
    for node, vector in probabilities.items():
        if vector.size == 0:
            memberships[node] = set()
            continue
        maximum = float(np.max(vector))
        keep = {i for i, value in enumerate(vector) if value >= tau or maximum - value <= delta}
        memberships[node] = keep if keep else {int(np.argmax(vector))}

    label_to_nodes: dict[int, set] = defaultdict(set)
    for node, labels in memberships.items():
        for label in labels:
            label_to_nodes[label].add(node)
    overlap_communities = [label_to_nodes[label] for label in sorted(label_to_nodes)]
    return overlap_communities, memberships, probabilities, hard_labels
