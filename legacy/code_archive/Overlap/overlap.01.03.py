import pandas as pd
import networkx as nx
import numpy as np
import time

# Load Excel adjacency matrix (skip first row and column)
file_path = 'adjacency_matrix_Dolphin_output.xlsx'
df = pd.read_excel(file_path, index_col=0)
adj_matrix = df.to_numpy()

# Create graph
G = nx.from_numpy_array(adj_matrix)

# Parameters
k = 5  # Number of communities
alpha = 0.1
epsilon = 0.1
P_min = 0.0001
T_max = 100

# Initialization
nodes = list(G.nodes())
probabilities = {node: np.ones(k) / k for node in nodes}

# Start timing
start_time = time.time()

prev_modularity = -1.0
for t in range(T_max):
    node_assignments = {}
    for node in nodes:
        if np.random.rand() < epsilon:
            action = np.random.randint(k)
        else:
            action = np.argmax(probabilities[node])
        node_assignments[node] = action

    # Build community structure
    community_map = [[] for _ in range(k)]
    for node, comm in node_assignments.items():
        community_map[comm].append(node)

    # Compute modularity
    modularity = nx.community.modularity(G, community_map)

    if abs(modularity - prev_modularity) < P_min:
        break
    prev_modularity = modularity

    # Update probabilities
    for node in nodes:
        action = node_assignments[node]
        for a in range(k):
            if a == action:
                probabilities[node][a] += alpha * (1 - probabilities[node][a])
            else:
                probabilities[node][a] -= alpha * probabilities[node][a]

# Final community assignment based on thresholds
threshold = 0.5
final_communities = {i: [] for i in range(k)}
overlapping_nodes = []

for node in nodes:
    assigned = 0
    for i in range(k):
        if probabilities[node][i] > threshold:
            final_communities[i].append(node)
            assigned += 1
    if assigned > 1:
        overlapping_nodes.append(node)

# End timing
end_time = time.time()
execution_time = end_time - start_time

# Print results
print("Detected Communities:")
for i, members in final_communities.items():
    print(f"Community {i+1}: {members}")
print(f"\nNumber of Overlapping Nodes: {len(overlapping_nodes)}")
print(f"Overlapping Nodes: {overlapping_nodes}")
print(f"Time Taken: {execution_time:.4f} seconds")
