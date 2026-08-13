import pandas as pd
import networkx as nx
import time
from networkx.algorithms.community import girvan_newman
from itertools import islice

# Load the adjacency matrix
file_path = 'adjacency_matrix_Dolphin_output.xlsx'
df = pd.read_excel(file_path, index_col=0)

# Convert DataFrame to undirected graph
G = nx.from_pandas_adjacency(df)

# Start timing
start_time = time.time()

# Apply Girvan-Newman algorithm: extract top 3 communities
k = 5  # number of communities desired
comp = girvan_newman(G)
limited = next(islice(comp, k - 1, k))  # take the k-th split

# Format communities
communities = [list(c) for c in limited]

# Identify overlapping nodes (heuristic: top 10% betweenness centrality)
betweenness = nx.betweenness_centrality(G)
sorted_btw = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)
num_overlap = max(1, int(len(betweenness) * 0.1))
overlapping_nodes = [node for node, _ in sorted_btw[:num_overlap]]

# Stop timing
end_time = time.time()
elapsed_time = end_time - start_time

# Output results
print("Detected Communities:")
for i, community in enumerate(communities):
    print(f"Community {i+1}: {community}")

print("\nOverlapping Nodes (based on betweenness centrality):")
print(overlapping_nodes)
print(f"Number of Overlapping Nodes: {len(overlapping_nodes)}")
print(f"Time Taken: {elapsed_time:.4f} seconds")
