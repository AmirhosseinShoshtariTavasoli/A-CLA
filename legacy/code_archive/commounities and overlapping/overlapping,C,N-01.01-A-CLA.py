import pandas as pd
import numpy as np
from collections import defaultdict

# === Step 1: Read Adjacency Matrix from Excel ===


def read_adjacency_matrix(file_path, sheet_name=0):
    df = pd.read_excel(file_path, sheet_name=sheet_name, index_col=0)
    adj_matrix = df.values
    return adj_matrix, df.index.tolist()

# === Step 2: Mock A-CLA Community Detection Function ===
# Replace this with your actual A-CLA algorithm implementation


def a_cla_detect_communities(adj_matrix):
    """
    Simulated output for demo. Replace this with your actual A-CLA implementation.
    Output format: {node_id: [community_ids]}
    """
    # Dummy logic: Replace this block with your real A-CLA results
    return {
        0: [0],
        1: [0, 1],
        2: [1],
        3: [2],
        4: [1, 2],
        5: [0],
        6: [2],
        7: [1, 2]
    }

# === Step 3: Find Overlapping Communities ===


def find_overlapping_communities(community_assignments):
    community_overlap_map = defaultdict(set)

    for node, comms in community_assignments.items():
        if len(comms) > 1:
            for comm_id in comms:
                community_overlap_map[comm_id].add(node)

    return community_overlap_map

# === Step 4: Format Results for Excel Export ===


def export_overlap_summary(overlap_map, output_file="overlapping_communities_A_CLA.xlsx"):
    overlap_data = {
        "Overlapping Community Number": [],
        "Number of Overlapping Nodes": []
    }

    for i, (comm_id, nodes) in enumerate(overlap_map.items(), start=1):
        overlap_data["Overlapping Community Number"].append(i)
        overlap_data["Number of Overlapping Nodes"].append(len(nodes))

    result_df = pd.DataFrame(overlap_data)
    result_df.to_excel(output_file, index=False)
    print(f"✅ Saved overlapping community summary to: {output_file}")


# === Run the Whole Pipeline ===
if __name__ == "__main__":
    # Update with your actual file path
    excel_file = "adjacency_matrix_karate_output.xlsx"  # <-- CHANGE THIS
    adj_matrix, node_ids = read_adjacency_matrix(excel_file)

    community_assignments = a_cla_detect_communities(adj_matrix)
    overlap_map = find_overlapping_communities(community_assignments)
    export_overlap_summary(overlap_map)
