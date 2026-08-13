import networkx as nx
import pandas as pd
import time
import random
from collections import defaultdict
from itertools import combinations

# -------------------- Load Graph from Excel Dataset --------------------


def load_graph_from_excel(file_path):
    nodes_df = pd.read_excel(file_path, sheet_name="Node")
    edges_df = pd.read_excel(file_path, sheet_name="Edge")

    G = nx.Graph()
    G.add_nodes_from(nodes_df['Vertex'])

    for _, row in edges_df.iterrows():
        source = row['Source']
        target = row['Target']
        G.add_edge(source, target)

    return G

# -------------------- A-CLA Community Detection --------------------


def a_cla_community_detection(G, iterations=1000, alpha=0.1):
    nodes = list(G.nodes())
    actions = {node: [0] for node in nodes}
    probabilities = {node: [1.0] for node in nodes}

    for _ in range(iterations):
        new_actions = {}
        for node in nodes:
            neighbor_actions = [actions[neighbor][0]
                                for neighbor in G.neighbors(node)]
            best_action = max(set(
                neighbor_actions), key=neighbor_actions.count) if neighbor_actions else actions[node][0]
            if random.random() < alpha:
                best_action = max(
                    [a for a in range(len(probabilities[node]) + 1)], default=0)
            if best_action not in probabilities[node]:
                probabilities[node].append(1.0)
            new_actions[node] = [best_action]
        actions = new_actions

    community_map = defaultdict(list)
    for node, acts in actions.items():
        for act in acts:
            community_map[act].append(node)

    # Include all communities
    return [sorted(members) for members in community_map.values()]

# -------------------- Overlapping Community Detection --------------------


def count_overlapping_community_pairs(communities):
    overlapping_pairs = []
    for (i, comm1), (j, comm2) in combinations(enumerate(communities), 2):
        if set(comm1) & set(comm2):
            overlapping_pairs.append((i, j))
    return overlapping_pairs


# -------------------- Main Execution --------------------
if __name__ == "__main__":
    file_path = "yeast.xlsx"  # <== Replace with your Excel file path
    G = load_graph_from_excel(file_path)

    start_time = time.time()
    detected_communities = a_cla_community_detection(G)
    overlapping_pairs = count_overlapping_community_pairs(detected_communities)
    elapsed_time = time.time() - start_time

    # Split communities by size
    multi_node_communities = [c for c in detected_communities if len(c) > 1]
    single_node_communities = [c for c in detected_communities if len(c) == 1]

    # Output
    print("=== All Detected Communities ===")
    for idx, comm in enumerate(detected_communities):
        print(
            f"Community {idx} ({len(comm)} node{'s' if len(comm) > 1 else ''}): {comm}")

    print(f"\nTotal Communities: {len(detected_communities)}")
    print(f"  > Communities with >1 node: {len(multi_node_communities)}")
    print(f"  > Communities with 1 node: {len(single_node_communities)}")
    print(f"\nNumber of Overlapping Community Pairs: {len(overlapping_pairs)}")
    print(f"Overlapping Community Pairs (by index): {overlapping_pairs}")
    print(f"\nExecution Time: {elapsed_time:.4f} seconds")
