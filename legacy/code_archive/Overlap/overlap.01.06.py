import numpy as np
import networkx as nx
import pandas as pd
import time
import random

# --- 1. Load adjacency matrix from Excel file ---


def load_adjacency_matrix_from_excel(file_path):
    df = pd.read_excel(file_path, index_col=0)
    adj_matrix = df.to_numpy()
    return adj_matrix

# --- 2. Build graph from adjacency matrix ---


def create_graph_from_adjacency(adj_matrix):
    G = nx.from_numpy_array(adj_matrix)
    return G

# --- 3. A-CLA algorithm with overlapping detection ---


def run_A_CLA(G, num_communities=3, alpha=0.1, epsilon=0.1, T_max=100, epsilon_conv=1e-4):
    num_nodes = len(G.nodes)
    P = np.ones((num_nodes, num_communities)) / num_communities
    actions = np.zeros(num_nodes, dtype=int)
    prev_modularity = -1.0
    start_time = time.time()

    for t in range(T_max):
        for i in range(num_nodes):
            if random.random() < epsilon:
                a = random.randint(0, num_communities - 1)
            else:
                a = np.argmax(P[i])
            actions[i] = a

            # Reward based on neighbors
            neighbors = list(G.neighbors(i))
            same_comm = sum(1 for n in neighbors if actions[n] == a)
            total_deg = len(neighbors)
            reward = same_comm / total_deg if total_deg > 0 else 0.0

            # Update probabilities
            for k in range(num_communities):
                if k == a:
                    P[i][k] += alpha * reward * (1 - P[i][k])
                else:
                    P[i][k] -= alpha * reward * P[i][k]
            P[i] = np.clip(P[i], 0, 1)
            P[i] /= P[i].sum()

        # Modularity check
        partition = {i: np.argmax(P[i]) for i in range(num_nodes)}
        communities = {}
        for node, com in partition.items():
            communities.setdefault(com, []).append(node)
        current_mod = nx.algorithms.community.quality.modularity(
            G, communities.values())
        if abs(current_mod - prev_modularity) < epsilon_conv:
            break
        prev_modularity = current_mod

    # Overlap detection
    overlap_nodes = []
    for i in range(num_nodes):
        sorted_probs = sorted(P[i], reverse=True)
        if sorted_probs[0] - sorted_probs[1] < 0.2:
            overlap_nodes.append(i)

    # Format output
    detected_comms = {k: [] for k in range(num_communities)}
    for i in range(num_nodes):
        detected_comms[np.argmax(P[i])].append(i)

    duration = time.time() - start_time
    return detected_comms, overlap_nodes, duration


# --- 4. Main execution ---
if __name__ == "__main__":
    # <-- change to your actual file path
    file_path = "adjacency_matrix_yeast_output.xlsx"
    adj_matrix = load_adjacency_matrix_from_excel(file_path)
    G = create_graph_from_adjacency(adj_matrix)
    detected_comms, overlap_nodes, duration = run_A_CLA(G)

    # Output results
    print("\nDetected Communities:")
    for cid, members in detected_comms.items():
        print(f"Community {cid + 1}: {members}")

    print(f"\nOverlapping Nodes: {overlap_nodes}")
    print(f"Number of Overlapping Nodes: {len(overlap_nodes)}")
    print(f"\nTime Taken: {duration:.4f} seconds")
