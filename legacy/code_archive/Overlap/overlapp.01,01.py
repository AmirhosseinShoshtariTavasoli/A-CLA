import time
import random

# Parameters
nodes = list(range(10))  # Example: 10 nodes
k = 3                    # Number of communities
alpha = 0.1              # Learning rate
epsilon = 0.1            # Exploration probability
T_max = 100              # Max iterations
overlap_threshold = 0.3  # Threshold for community overlap

# Initialize probability matrix
prob_matrix = {node: [1 / k for _ in range(k)] for node in nodes}

# Start timing
start_time = time.time()

# A-CLA simulation loop
for t in range(T_max):
    for node in nodes:
        if random.random() > epsilon:
            selected_community = prob_matrix[node].index(
                max(prob_matrix[node]))
        else:
            selected_community = random.randint(0, k - 1)

        # Replace with real evaluation in practice
        reward = random.uniform(0, 1)

        for i in range(k):
            if i == selected_community:
                prob_matrix[node][i] += alpha * \
                    reward * (1 - prob_matrix[node][i])
            else:
                prob_matrix[node][i] -= alpha * reward * prob_matrix[node][i]

        # Normalize probabilities
        total = sum(prob_matrix[node])
        prob_matrix[node] = [p / total for p in prob_matrix[node]]

# Stop timing
end_time = time.time()
execution_time = end_time - start_time

# Overlapping community detection
overlapping_nodes = {
    node: [i for i, p in enumerate(probs) if p >= overlap_threshold]
    for node, probs in prob_matrix.items()
    if sum(p >= overlap_threshold for p in probs) > 1
}
num_overlapping_nodes = len(overlapping_nodes)

# Results
print("========= A-CLA Community Detection Report =========")
print(f"Execution Time: {execution_time:.4f} seconds")
print(f"Number of Overlapping Nodes: {num_overlapping_nodes}")
for node, communities in overlapping_nodes.items():
    print(f"Node {node} → Communities: {communities}")
