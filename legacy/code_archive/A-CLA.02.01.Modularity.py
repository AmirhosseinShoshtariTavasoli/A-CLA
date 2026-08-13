import pandas as pd
import networkx as nx
import community  # python-louvain package
from sklearn.metrics import normalized_mutual_info_score, f1_score

# === Step 1: Load Excel Data ===
# Make sure this is in the same folder as the script
file_path = "lesmiserables.xlsx"

# Load the two sheets
node_df = pd.read_excel(file_path, sheet_name="Node", dtype=str)
edge_df = pd.read_excel(file_path, sheet_name="Edge", dtype=str)

# === Step 2: Build Graph ===
G = nx.Graph()
edges = edge_df[['Source', 'Target']].values.tolist()
G.add_edges_from(edges)

# === Step 3: Extract Ground Truth Labels ===
# Map node IDs to ground-truth labels
ground_truth_dict = dict(
    zip(node_df['Vertex'].astype(str), node_df['Label'].astype(str)))

# Filter nodes present in both the graph and node list
graph_nodes = set(G.nodes())
ground_nodes = set(ground_truth_dict.keys())
aligned_nodes = list(graph_nodes & ground_nodes)

# Warn if any missing
missing_nodes = graph_nodes - ground_nodes
if missing_nodes:
    print(
        f"Warning: {len(missing_nodes)} nodes missing from ground truth and will be skipped.")

# Prepare ground-truth and predicted input for evaluation
ground_truth = [ground_truth_dict[node] for node in aligned_nodes]

# === Step 4: Community Detection Using Louvain (or replace with A-CLA later) ===
partition = community.best_partition(G)
predicted_labels_dict = {str(k): str(v) for k, v in partition.items()}
predicted_labels = [predicted_labels_dict[node] for node in aligned_nodes]

# === Step 5: Evaluation Metrics ===
modularity = community.modularity(partition, G)
nmi = normalized_mutual_info_score(ground_truth, predicted_labels)
f1 = f1_score(ground_truth, predicted_labels, average='macro')

# === Step 6: Display Results ===
print(f"Modularity: {modularity:.6f}")
print(f"NMI: {nmi:.6f}")
print(f"F1-Score: {f1:.6f}")
