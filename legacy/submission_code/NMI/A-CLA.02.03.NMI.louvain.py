import pandas as pd
import networkx as nx
import numpy as np
from sklearn.metrics import normalized_mutual_info_score
from networkx.algorithms.community import louvain_communities
from collections import defaultdict

# Step 1: Load the adjacency matrix from an Excel file
# Replace 'adjacency_matrix_C.elegans-Genetic_output.xlsx' with your actual file path
adj_matrix_df = pd.read_excel(
    'adjacency_matrix_yeast_output.xlsx', index_col=0
)

# Convert the DataFrame to a NumPy array (the adjacency matrix)
adj_matrix = adj_matrix_df.values

# Step 2: Create a NetworkX graph from the adjacency matrix
G = nx.from_numpy_array(adj_matrix)

# Define the A-CLA (Adaptive Community Labeling Algorithm)


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

# Function to convert communities to labels


def communities_to_labels(communities, n_nodes):
    labels = [-1] * n_nodes
    for label, community in enumerate(communities):
        for node in community:
            labels[node] = label
    return labels


# Step 3: Set up comparison with Louvain method
# Louvain method for community detection
louvain_comms = louvain_communities(G)
labels_louvain = communities_to_labels(louvain_comms, len(G.nodes()))

# Automatic Search for Best Parameters for A-CLA
best_nmi = 0
best_params = None
best_labels_pred_acla = None

# Define ranges for A-CLA parameters
num_actions_list = [2, 3, 4]
initial_alpha_list = [0.05, 0.1, 0.2]
epsilon_list = [0.0005, 0.001, 0.005]
gamma_list = [0.001, 0.005, 0.01]
max_iter_list = [100, 200, 300, 500]

# Loop through all combinations of A-CLA parameters
for num_actions in num_actions_list:
    for initial_alpha in initial_alpha_list:
        for epsilon in epsilon_list:
            for gamma in gamma_list:
                for max_iter in max_iter_list:
                    # Run A-CLA for each combination
                    communities_a_cla = a_cla(
                        G, num_actions, initial_alpha, epsilon, gamma, max_iter)
                    labels_pred_acla = communities_to_labels(
                        communities_a_cla.values(), len(G.nodes()))

                    # Calculate NMI between A-CLA and Louvain
                    nmi_score = normalized_mutual_info_score(
                        labels_louvain, labels_pred_acla)

                    # Keep track of the best result
                    if nmi_score > best_nmi:
                        best_nmi = nmi_score
                        best_params = (num_actions, initial_alpha,
                                       epsilon, gamma, max_iter)
                        best_labels_pred_acla = labels_pred_acla

# Print the best results
print(f"Best NMI Score between A-CLA and Louvain: {best_nmi:.4f}")
print(
    f"Best Params: NUM_ACTIONS = {best_params[0]}, INITIAL_ALPHA = {best_params[1]}, EPSILON = {best_params[2]}, GAMMA = {best_params[3]}, MAX_ITER = {best_params[4]}")
