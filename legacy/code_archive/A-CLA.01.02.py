import networkx as nx
import numpy as np
from collections import defaultdict
import math
import random
from itertools import product
from sklearn.metrics import normalized_mutual_info_score, f1_score

# --- Hyperparameter ranges ---
num_actions_list = [2, 3, 4]
initial_alpha_list = [0.05, 0.1, 0.2]
epsilon_list = [0.0005, 0.001, 0.005]
gamma_list = [0.001, 0.005, 0.01]
max_iter_list = [100, 200, 300]


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
    return final_communities


def calculate_metrics(G, pred_labels, ground_truth):
    # Convert predicted labels to list
    y_pred = [pred_labels[n] for n in G.nodes()]
    y_true = [ground_truth[n] for n in G.nodes()]

    # Modularity
    comm_dict = defaultdict(set)
    for node, label in pred_labels.items():
        comm_dict[label].add(node)
    modularity = nx.algorithms.community.modularity(G, comm_dict.values())

    # NMI
    nmi = normalized_mutual_info_score(y_true, y_pred)

    # F1-score (macro)
    f1 = f1_score(y_true, y_pred, average='macro')

    # Edge Density
    num_edges = G.number_of_edges()
    num_nodes = G.number_of_nodes()
    edge_density = 2 * num_edges / (num_nodes * (num_nodes - 1))

    # Betweenness Centrality (average)
    bc = nx.betweenness_centrality(G)
    avg_bc = np.mean(list(bc.values()))

    return modularity, nmi, f1, edge_density, avg_bc


# --- Main Tuning Code ---
G = nx.karate_club_graph()
ground_truth = [0 if G.nodes[i]['club'] == 'Mr. Hi' else 1 for i in G.nodes()]
ground_truth_dict = {i: gt for i, gt in enumerate(ground_truth)}

best_modularity = -1
best_result = None

print("🔍 Tuning A-CLA on Karate Club...\n")

for (num_actions, alpha_init, eps, gam, max_it) in product(
        num_actions_list, initial_alpha_list, epsilon_list, gamma_list, max_iter_list):

    labels = a_cla(G, num_actions, alpha_init, eps, gam, max_it)
    mod, nmi, f1, ed, bc = calculate_metrics(G, labels, ground_truth_dict)

    print(f"actions={num_actions}, alpha={alpha_init}, eps={eps}, gamma={gam}, iter={max_it} => "
          f"Mod: {mod:.4f}, NMI: {nmi:.4f}, F1: {f1:.4f}, ED: {ed:.4f}, BC: {bc:.4f}")

    if mod > best_modularity:
        best_modularity = mod
        best_result = (num_actions, alpha_init, eps,
                       gam, max_it, mod, nmi, f1, ed, bc)

# --- Final Output ---
print("\n✅ Best Configuration (Optimized for Modularity):")
print(f"NUM_ACTIONS: {best_result[0]}, INITIAL_ALPHA: {best_result[1]}, EPSILON: {best_result[2]}, "
      f"GAMMA: {best_result[3]}, MAX_ITER: {best_result[4]}")
print(f"Modularity: {best_result[5]:.4f}, NMI: {best_result[6]:.4f}, F1-score: {best_result[7]:.4f}, "
      f"Edge Density: {best_result[8]:.4f}, Avg Betweenness Centrality: {best_result[9]:.4f}")
