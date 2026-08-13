import networkx as nx
import numpy as np
from collections import defaultdict
import math
import random
from itertools import product

# --- Hyperparameter ranges ---
num_actions_list = [2, 3, 4]
initial_alpha_list = [0.05, 0.1, 0.2]
epsilon_list = [0.0005, 0.001, 0.005]
gamma_list = [0.001, 0.005, 0.01]
max_iter_list = [100, 200, 300]

# --- Helper functions ---


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


# --- Main Tuning Code ---
G = nx.karate_club_graph()
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
