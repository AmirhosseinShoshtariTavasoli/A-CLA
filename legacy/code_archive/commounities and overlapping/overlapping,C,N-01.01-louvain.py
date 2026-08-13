import pandas as pd
import networkx as nx
import community as community_louvain
from collections import defaultdict

# === Load Excel file ===
file_path = "diseasome.xlsx"  # <-- Replace with your actual Excel file name
nodes_df = pd.read_excel(file_path, sheet_name="Node")
edges_df = pd.read_excel(file_path, sheet_name="Edge")

# === Build the graph ===
G = nx.Graph()
G.add_nodes_from(nodes_df["Vertex"])
G.add_edges_from(edges_df[["Source", "Target"]].values)

# === Run Louvain multiple times to simulate overlapping detection ===
num_runs = 10
node_membership = defaultdict(list)

for _ in range(num_runs):
    partition = community_louvain.best_partition(G)
    for node, comm in partition.items():
        node_membership[node].append(comm)

# === Identify overlapping nodes ===
overlapping_nodes = {
    node: set(memberships)
    for node, memberships in node_membership.items()
    if len(set(memberships)) > 1
}

# === Count how many nodes overlap with each community ===
community_overlap_map = defaultdict(set)

for node, comms in overlapping_nodes.items():
    for comm_id in comms:
        community_overlap_map[comm_id].add(node)

# === Prepare data for Excel ===
overlap_data = {
    "Overlapping Community Number": [],
    "Number of Overlapping Nodes": []
}

for i, (comm_id, nodes) in enumerate(community_overlap_map.items(), start=1):
    overlap_data["Overlapping Community Number"].append(i)
    overlap_data["Number of Overlapping Nodes"].append(len(nodes))

# === Create DataFrame and Save to Excel ===
result_df = pd.DataFrame(overlap_data)
result_df.to_excel("overlapping_communities_summary.xlsx", index=False)

print("✅ Overlapping community summary saved to 'overlapping_communities_summary.xlsx'")
