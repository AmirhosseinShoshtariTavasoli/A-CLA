import pandas as pd
import networkx as nx
import time
from networkx.algorithms.community import girvan_newman
from itertools import islice
from collections import defaultdict

# === SETTINGS ===
file_path = 'adjacency_matrix_yeast_output.xlsx'  # <--- change your file here
k = 5  # desired number of communities (after k-1 splits)
overlap_top_frac = 0.10  # top 10% betweenness as overlapping-node heuristic
# =================

# Load adjacency and build graph
df = pd.read_excel(file_path, index_col=0)
G = nx.from_pandas_adjacency(df)
G.remove_edges_from(nx.selfloop_edges(G))

start_time = time.time()

# Run Girvan–Newman and take the k-th split
comp = girvan_newman(G)
try:
    partition = next(islice(comp, k - 1, k))  # tuple of sets
except StopIteration:
    # If GN can't produce that many splits, fall back to the last available split
    # (this happens on very small graphs or already-fragmented ones)
    last = None
    for last in comp:
        pass
    partition = last if last is not None else (set(G.nodes()),)

communities = [set(c) for c in partition]

# Overlapping nodes = top X% by betweenness
betweenness = nx.betweenness_centrality(G)
n = max(1, int(len(betweenness) * overlap_top_frac))
top_nodes = {n for n, _ in sorted(
    betweenness.items(), key=lambda x: x[1], reverse=True)[:n]}

# Count overlapping communities (those containing at least one overlapping node)
overlapping_communities = sum(
    1 for c in communities if any(v in top_nodes for v in c))

elapsed = time.time() - start_time

# Output (minimal)
print(
    f"Number of Overlapping Communities (GN, k={k}): {overlapping_communities}")
print(f"Execution Time: {elapsed:.4f} seconds")
