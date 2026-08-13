import pandas as pd
import random
import networkx as nx  # Import networkx
from sklearn.metrics import f1_score
from itertools import chain

# Adaptive Cellular Learning Automata (A-CLA) for community detection


def a_cla_community_detection(G, num_iterations=100, initial_alpha=0.1, epsilon=0.05, gamma=0.9):
    nodes = list(G.nodes())
    # Initially, each node is its own community
    communities = {node: node for node in nodes}
    node_weights = {node: 1 for node in nodes}

    for _ in range(num_iterations):
        for node in nodes:
            neighbors = list(G.neighbors(node))
            if not neighbors:
                continue

            # Adaptive learning based on neighbor labels
            neighbor_labels = [communities[neighbor] for neighbor in neighbors]
            most_common_label = max(
                set(neighbor_labels), key=neighbor_labels.count)

            # Update community label
            if random.random() < (initial_alpha * node_weights[node]):
                communities[node] = most_common_label

            # Update weights based on reinforcement
            node_weights[node] = node_weights[node] * \
                gamma if communities[node] == most_common_label else node_weights[node] * (
                    1 - epsilon)

    # Group nodes by community label
    community_dict = {}
    for node, comm in communities.items():
        if comm not in community_dict:
            community_dict[comm] = []
        community_dict[comm].append(node)

    return list(community_dict.values())

# Function to load graph from an adjacency matrix with headers in the first row and column


def load_graph_from_adjacency_matrix(file_path):
    adj_df = pd.read_excel(file_path, index_col=0)
    adj_df.columns = adj_df.index  # Set the columns to match the node labels
    G = nx.from_pandas_adjacency(adj_df)
    return G

# Function to create node-to-community mapping for each set of communities


def create_node_to_community_mapping(communities):
    node_to_comm = {}
    for comm_id, community in enumerate(communities):
        for node in community:
            node_to_comm[node] = comm_id
    return node_to_comm

# Function to calculate F1-score


def calculate_f1_score(ground_truth, predicted):
    gt_node_to_comm = create_node_to_community_mapping(ground_truth)
    pred_node_to_comm = create_node_to_community_mapping(predicted)

    all_nodes = set(gt_node_to_comm.keys()).union(
        set(pred_node_to_comm.keys()))

    y_true = [gt_node_to_comm.get(node, -1) for node in all_nodes]
    y_pred = [pred_node_to_comm.get(node, -1) for node in all_nodes]

    f1 = f1_score(y_true, y_pred, average='weighted')
    return f1

# Main function to load graph and calculate F1-score using A-CLA


def main():
    # Replace with your actual Excel file path
    file_path = "adjacency_matrix_yeast_output.xlsx"
    G = load_graph_from_adjacency_matrix(file_path)

    # Generate ground truth communities (random for now)
    ground_truth = [[node for node in G.nodes() if node % 2 == 0], [
        node for node in G.nodes() if node % 2 != 0]]

    # Detect predicted communities using A-CLA
    predicted = a_cla_community_detection(G)

    # Calculate and print F1-score
    f1 = calculate_f1_score(ground_truth, predicted)
    print(f"F1-score (A-CLA): {f1:.6f}")


if __name__ == "__main__":
    main()
