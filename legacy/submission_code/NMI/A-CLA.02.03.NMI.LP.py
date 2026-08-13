import pandas as pd
import numpy as np
import networkx as nx
from networkx.algorithms.community import label_propagation_communities
from sklearn.metrics import normalized_mutual_info_score
from collections import defaultdict

# Step 1: Load the adjacency matrix
# Replace with your actual file path
file_path = 'adjacency_matrix_yeast_output.xlsx'
adj_matrix_df = pd.read_excel(file_path, index_col=0)
adj_matrix = adj_matrix_df.values

# Step 2: Create a NetworkX graph from the adjacency matrix
G = nx.from_numpy_array(adj_matrix)

# Function to convert communities to labels


def communities_to_labels(communities, n_nodes):
    labels = [-1] * n_nodes
    for label, community in enumerate(communities):
        for node in community:
            labels[node] = label
    return labels

# Define the A-CLA function


def entropy(prob_dist):
    return -np.sum([p * np.log(p + 1e-12) for p in prob_dist])


def update_prob(p_vec, action, reward, alpha):
    if reward:
        for i in range(len(p_vec)):
            if i == action:
                p_vec[i] += alpha * (1 - p_vec[i])
            else:
                p_vec[i] *= (1 - alpha)
    else:
        for i in range(len(p_vec)):
            if i == action:
                p_vec[i] *= (1 - alpha)
            else:
                p_vec[i] += alpha / (len(p_vec) - 1)
    p_vec /= np.sum(p_vec)
    return p_vec


def a_cla(G, num_actions, initial_alpha, epsilon, gamma, max_iter):
    nodes = list(G.nodes())
    prob_matrix = {node: np.ones(num_actions) / num_actions for node in nodes}
    actions = {node: np.random.choice(num_actions) for node in nodes}
    alpha = {node: initial_alpha for node in nodes}
    entropy_vec = {node: entropy(prob_matrix[node]) for node in nodes}

    for _ in range(max_iter):
        for node in nodes:
            probs = prob_matrix[node]
            actions[node] = np.random.choice(num_actions, p=probs)

        for node in nodes:
            neighbors = list(G.neighbors(node))
            if not neighbors:
                continue
            same_count = sum(
                1 for nbr in neighbors if actions[nbr] == actions[node])
            reward = 1 if same_count >= len(neighbors) / 2 else 0
            prob_matrix[node] = update_prob(
                prob_matrix[node], actions[node], reward, alpha[node])

        converged = True
        for node in nodes:
            new_entropy = entropy(prob_matrix[node])
            delta_H = abs(new_entropy - entropy_vec[node])
            entropy_vec[node] = new_entropy
            alpha[node] *= (1 - gamma * delta_H)
            if delta_H > epsilon:
                converged = False

        if converged:
            break

    final_communities = {node: np.argmax(prob_matrix[node]) for node in nodes}
    community_dict = defaultdict(set)
    for node, comm in final_communities.items():
        community_dict[comm].add(node)
    return community_dict


# Step 3: Run community detection algorithms
# Label Propagation method
lp_comms = list(label_propagation_communities(G))
labels_lp = communities_to_labels(lp_comms, len(G.nodes()))

# A-CLA method with example parameters
communities_acla = a_cla(G, num_actions=2, initial_alpha=0.1,
                         epsilon=0.001, gamma=0.005, max_iter=300)
labels_acla = communities_to_labels(communities_acla.values(), len(G.nodes()))

# Step 4: Calculate NMI between A-CLA and Label Propagation
nmi_acla_lp = normalized_mutual_info_score(labels_acla, labels_lp)

# Print the NMI result
print(f"NMI A-CLA vs Label Propagation: {nmi_acla_lp:.4f}")
