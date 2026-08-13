from pathlib import Path

from acla.io import graph_from_adjacency, load_adjacency
from acla.nonoverlap import detect_nonoverlapping

root = Path(__file__).resolve().parents[1]
path = root / "data" / "adjacency_matrices" / "adjacency_matrix_Dolphin_output.xlsx"
adj = load_adjacency(path)
graph = graph_from_adjacency(adj, binarize=True)
labels, communities, q = detect_nonoverlapping(graph, seed=42)
print(f"nodes={graph.number_of_nodes()} edges={graph.number_of_edges()} communities={len(communities)} modularity={q:.6f}")
