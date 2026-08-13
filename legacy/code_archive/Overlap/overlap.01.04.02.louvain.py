import pandas as pd
import networkx as nx
import time
from community import community_louvain
from collections import defaultdict

# Load the adjacency matrix
file_path = 'adjacency_matrix_yeast_output.xlsx'  # <--- change file here
df = pd.read_excel(file_path, index_col=0)

# Convert the DataFrame to a NetworkX graph
G = nx.from_pandas_adjacency(df)

# Start timing
start_time = time.time()

# Apply Louvain method for community detection
partition = community_louvain.best_partition(G)

# Group nodes into communities
communities = defaultdict(list)
for node, comm_id in partition.items():
    communities[comm_id].append(node)

# Identify overlapping nodes (top 10% betweenness centrality as heuristic)
betweenness = nx.betweenness_centrality(G)
threshold = sorted(betweenness.values())[-int(0.1 * len(betweenness))]
overlapping_nodes = {node for node,
                     score in betweenness.items() if score >= threshold}

# Count overlapping communities = communities that include at least one overlapping node
overlapping_communities = [
    nodes for nodes in communities.values() if any(n in overlapping_nodes for n in nodes)
]

# Stop timing
end_time = time.time()
elapsed_time = end_time - start_time

# Output results
print(f"Number of Overlapping Communities: {len(overlapping_communities)}")
print(f"Execution Time: {elapsed_time:.4f} seconds")
