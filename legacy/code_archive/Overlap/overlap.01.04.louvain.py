import pandas as pd
import networkx as nx
import time
from community import community_louvain
from itertools import combinations

# Load the adjacency matrix
file_path = 'adjacency_matrix_Diseasome_output.xlsx'
df = pd.read_excel(file_path, index_col=0)

# Convert the DataFrame to a NetworkX graph
G = nx.from_pandas_adjacency(df)

# Start timing
start_time = time.time()

# Apply Louvain method for community detection
partition = community_louvain.best_partition(G)

# Reverse partition to find communities
communities = {}
for node, comm_id in partition.items():
    communities.setdefault(comm_id, []).append(node)

# Identify overlapping nodes (heuristic: top 10% in betweenness centrality)
betweenness = nx.betweenness_centrality(G)
threshold = sorted(betweenness.values())[-int(0.1 * len(betweenness))]
overlapping_nodes = [node for node,
                     score in betweenness.items() if score >= threshold]

# Stop timing
end_time = time.time()
elapsed_time = end_time - start_time

# Output results
print("Detected Communities:")
for cid, nodes in communities.items():
    print(f"Community {cid + 1}: {nodes}")

print("\nOverlapping Nodes (based on betweenness):")
print(overlapping_nodes)
print(f"Number of Overlapping Nodes: {len(overlapping_nodes)}")
print(f"Time Taken: {elapsed_time:.4f} seconds")
