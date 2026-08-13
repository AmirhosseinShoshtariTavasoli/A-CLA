import pandas as pd
import networkx as nx

# Load Excel file (update 'your_file.xlsx' with the actual file path)
file_path = 'adjacency_matrix_Dolphin_output.xlsx'
# First row and column are node names
df = pd.read_excel(file_path, index_col=0)

# Create graph from adjacency matrix
G = nx.from_pandas_adjacency(df)

# List of nodes
nodes = list(G.nodes)

# Print graph info to verify
print("Number of nodes:", G.number_of_nodes())
print("Number of edges:", G.number_of_edges())
