import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge
from matplotlib.collections import PatchCollection
import community as community_louvain
from collections import defaultdict
import numpy as np

# === 1. Load Data ===
file_path = "adjacency_matrix_Dolphin_output.xlsx"  # Replace this
nodes_df = pd.read_excel(file_path, sheet_name="Node")
edges_df = pd.read_excel(file_path, sheet_name="Edge")

# === 2. Build Graph ===
G = nx.Graph()
for _, row in nodes_df.iterrows():
    G.add_node(row["Vertex"], label=row["Label"])

for _, row in edges_df.iterrows():
    G.add_edge(row["Source"], row["Target"])

# === 3. Louvain Community Detection ===
partition = community_louvain.best_partition(G)
communities = defaultdict(list)
for node, comm_id in partition.items():
    communities[comm_id].append(node)

# === 4. Create reverse map and overlapping detection ===
node_community_map = defaultdict(set)
for comm_id, nodes in communities.items():
    for node in nodes:
        node_community_map[node].add(comm_id)

overlapping_nodes = [
    n for n, comms in node_community_map.items() if len(comms) > 1]
normal_nodes = [n for n in G.nodes() if n not in overlapping_nodes]

# === 5. Setup Layout and Color Map ===
pos = nx.kamada_kawai_layout(G)
colors = plt.cm.tab10.colors  # 10 colors max

plt.figure(figsize=(13, 10))

# === 6. Draw non-overlapping nodes per community ===
for comm_id, nodes in communities.items():
    these_nodes = [n for n in nodes if n not in overlapping_nodes]
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=these_nodes,
        node_color=[colors[comm_id % len(colors)]] * len(these_nodes),
        node_size=[200 + 100 * G.degree(n) for n in these_nodes],
        alpha=0.9,
        label=f"Community {comm_id}"
    )

# === 7. Draw overlapping nodes as pie-chart wedges ===
ax = plt.gca()
for node in overlapping_nodes:
    x, y = pos[node]
    deg = G.degree(node)
    node_size = 300 + 100 * deg
    radius = np.sqrt(node_size) / 50

    # Get communities the node belongs to
    comms = sorted(list(node_community_map[node]))
    total = len(comms)
    patches = []

    for i, comm_id in enumerate(comms):
        theta1 = 360 * i / total
        theta2 = 360 * (i + 1) / total
        wedge = Wedge((x, y), radius, theta1, theta2, facecolor=colors[comm_id % len(
            colors)], edgecolor='black', linewidth=0.8)
        patches.append(wedge)

    for p in patches:
        ax.add_patch(p)

# === 8. Draw Edges ===
nx.draw_networkx_edges(G, pos, alpha=0.25)

# === 9. Clean up ===
plt.title("Overlapping Communities with Pie-Chart Nodes", fontsize=14)
plt.axis("off")
plt.legend(scatterpoints=1, fontsize=10)
plt.tight_layout()
plt.show()
