import pandas as pd
import networkx as nx
from collections import defaultdict
from networkx.algorithms.community import girvan_newman
import itertools

# === Load Excel file ===
file_path = "diseasome.xlsx"  # <-- Replace with your Excel file path
nodes_df = pd.read_excel(file_path, sheet_name="Node")
edges_df = pd.read_excel(file_path, sheet_name="Edge")

# === Build the graph ===
G = nx.Graph()
G.add_nodes_from(nodes_df["Vertex"])
G.add_edges_from(edges_df[["Source", "Target"]].values)

# === Run Girvan–Newman multiple times with different levels ===
node_membership = defaultdict(list)
num_levels = 5  # Number of hierarchical levels to simulate

comp_generator = girvan_newman(G)
for level in itertools.islice(comp_generator, num_levels):
    communities = list(level)
    for comm_id, community in enumerate(communities):
        for node in community:
            node_membership[node].append(comm_id)

# === Identify overlapping nodes ===
overlapping_nodes = {
    node: set(memberships)
    for node, memberships in node_membership.items()
    if len(set(memberships)) > 1
}

# === Group overlapping nodes by community IDs ===
community_overlap_map = defaultdict(set)

for node, comm_ids in overlapping_nodes.items():
    for comm_id in comm_ids:
        community_overlap_map[comm_id].add(node)

# === Prepare data for Excel ===
overlap_data = {
    "Overlapping Community Number": [],
    "Number of Overlapping Nodes": []
}

for i, (comm_id, nodes) in enumerate(community_overlap_map.items(), start=1):
    overlap_data["Overlapping Community Number"].append(i)
    overlap_data["Number of Overlapping Nodes"].append(len(nodes))

# === Save to Excel ===
result_df = pd.DataFrame(overlap_data)
result_df.to_excel("overlapping_communities_gn.xlsx", index=False)

print("✅ Overlapping community summary saved to 'overlapping_communities_gn.xlsx'")
