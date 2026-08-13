import networkx as nx
import pandas as pd
import time
import random
from collections import defaultdict

# -------------------- Load Adjacency Matrix from Excel --------------------


def load_graph_from_excel(file_path):
    df = pd.read_excel(file_path, index_col=0)
    G = nx.from_pandas_adjacency(df)
    return G

# -------------------- A-CLA Community Detection --------------------


def a_cla_community_detection(G, iterations=1000, alpha=0.1, threshold=0.01):
    nodes = list(G.nodes())
    # Each node starts in one community
    actions = {node: [0] for node in nodes}
    probabilities = {node: [1.0] for node in nodes}
    communities = defaultdict(list)

    for _ in range(iterations):
        new_actions = {}
        for node in nodes:
            # Check neighbors' actions and choose the most frequent one
            neighbor_actions = []
            for neighbor in G.neighbors(node):
                neighbor_action = actions[neighbor][0]
                neighbor_actions.append(neighbor_action)

            # Determine majority action
            if neighbor_actions:
                best_action = max(set(neighbor_actions),
                                  key=neighbor_actions.count)
            else:
                best_action = actions[node][0]

            # With probability alpha, explore new community
            if random.random() < alpha:
                best_action = max(
                    [a for a in range(len(probabilities[node]) + 1)], default=0)

            # Update action
            if best_action not in probabilities[node]:
                probabilities[node].append(1.0)
            new_actions[node] = [best_action]

        actions = new_actions

    # Organize nodes into communities
    community_map = defaultdict(list)
    for node, acts in actions.items():
        for act in acts:
            community_map[act].append(node)

    return list(community_map.values())

# -------------------- Detect Overlapping Communities --------------------


def detect_overlapping_communities(communities):
    node_to_communities = defaultdict(set)
    for i, community in enumerate(communities):
        for node in community:
            node_to_communities[node].add(i)

    overlapping_nodes = [node for node,
                         comms in node_to_communities.items() if len(comms) > 1]

    # Build overlapping communities (groups where nodes share overlaps)
    overlapping_communities = []
    seen_nodes = set()
    for node in overlapping_nodes:
        if node not in seen_nodes:
            group = set()
            for cid in node_to_communities[node]:
                group.update(communities[cid])
            overlapping_communities.append(group)
            seen_nodes.update(group)

    return overlapping_communities


# -------------------- Main --------------------
if __name__ == "__main__":
    start_time = time.time()

    # === Replace this path with your actual Excel file path ===
    file_path = "adjacency_matrix_C.elegans_output.xlsx"
    G = load_graph_from_excel(file_path)

    # Detect communities using A-CLA
    base_communities = a_cla_community_detection(G)

    # Detect overlapping communities
    overlapping_communities = detect_overlapping_communities(base_communities)

    # Output results
    print("Detected Overlapping Communities (A-CLA):")
    for i, comm in enumerate(overlapping_communities, 1):
        print(f"Community {i}: {sorted(comm)}")

    print(
        f"\nNumber of Overlapping Communities Detected: {len(overlapping_communities)}")
    print(f"\nTime Taken: {time.time() - start_time:.4f} seconds")
