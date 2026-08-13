import pandas as pd
import networkx as nx
import numpy as np
import random
from itertools import product
from collections import defaultdict
import math


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


def calculate_metrics(graph, communities):
    # Calculate Edge Density
    num_edges = graph.number_of_edges()
    num_nodes = graph.number_of_nodes()
    edge_density = 2 * num_edges / \
        (num_nodes * (num_nodes - 1)) if num_nodes > 1 else 0

    # Calculate Betweenness Centrality and get top 3 nodes
    betweenness = nx.betweenness_centrality(graph)
    top_3_nodes = sorted(betweenness.items(),
                         key=lambda x: x[1], reverse=True)[:3]

    return edge_density, top_3_nodes


# Load Dataset
# Replace 'your_dataset.xlsx' with your actual file path
file_path = 'yeast.xlsx'
nodes_df = pd.read_excel(file_path, sheet_name='Node')
edges_df = pd.read_excel(file_path, sheet_name='Edge')

# Create Graph
G = nx.Graph()

for _, row in nodes_df.iterrows():
    G.add_node(str(row['Vertex']), label=row['Label'])

for _, row in edges_df.iterrows():
    G.add_edge(str(row['Source']), str(row['Target']))

# --- Main Tuning Code ---
# Hyperparameter definition
num_actions_list = [2, 3, 4]
initial_alpha_list = [0.05, 0.1, 0.2]
epsilon_list = [0.0005, 0.001, 0.005]
gamma_list = [0.001, 0.005, 0.01]
max_iter_list = [100, 200, 300]

best_modularity = -1
best_params = None

print("Starting hyperparameter search...\n")

for (num_actions, alpha_init, eps, gam, max_it) in product(
        num_actions_list, initial_alpha_list, epsilon_list, gamma_list, max_iter_list):

    communities = a_cla(G, num_actions, alpha_init, eps, gam, max_it)
    mod = nx.algorithms.community.modularity(G, communities.values())

    print(
        f"Params: actions={num_actions}, alpha={alpha_init}, eps={eps}, gamma={gam}, iter={max_it} => Modularity: {mod:.4f}")

    if mod > best_modularity:
        best_modularity = mod
        best_params = (num_actions, alpha_init, eps, gam, max_it)

# --- Final Output ---
print("\n✅ Best configuration found:")
print(f"Modularity: {best_modularity:.4f}")
print(
    f"NUM_ACTIONS: {best_params[0]}, INITIAL_ALPHA: {best_params[1]}, EPSILON: {best_params[2]}, GAMMA: {best_params[3]}, MAX_ITER: {best_params[4]}")

# Run A-CLA with best parameters
communities = a_cla(G, best_params[0], best_params[1],
                    best_params[2], best_params[3], best_params[4])

# Calculate and print metrics
edge_density, top_3_nodes = calculate_metrics(G, communities)

print(f"\nEdge Density: {edge_density:.4f}")
print("Top 3 Nodes by Betweenness Centrality:")
for node, centrality in top_3_nodes:
    print(f"Node: {node}, Betweenness Centrality: {centrality:.4f}")
