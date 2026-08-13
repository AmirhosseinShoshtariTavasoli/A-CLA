#!/usr/bin/env python3
# CPM diagnostics + k-sweep

import time
from pathlib import Path
import pandas as pd
import networkx as nx
from networkx.algorithms.community import k_clique_communities

# ==== EDIT THESE ====
file_path = "adjacency_matrix_DanioRerio_output.xlsx"
k_values = [3, 4, 5, 6]      # try a few k's
weight_threshold = None      # None => treat >0 as edge; or set e.g. 0.0 or 0.2
# =====================


def load_adjacency(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, index_col=0)
    elif path.suffix.lower() in (".csv", ".txt"):
        df = pd.read_csv(path, index_col=0)
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")
    if df.shape[0] != df.shape[1]:
        raise ValueError(f"Adjacency must be square, got {df.shape}")
    if not df.index.equals(df.columns):
        if set(df.index) == set(df.columns):
            df = df.loc[df.index, df.index]
        else:
            raise ValueError("Row/column labels must match.")
    return df


def binarize(df: pd.DataFrame, thr):
    if thr is None:
        return (df > 0).astype(int)
    return (df >= thr).astype(int)


def diagnostics(G: nx.Graph):
    n = G.number_of_nodes()
    m = G.number_of_edges()
    degs = [d for _, d in G.degree()]
    avg_deg = sum(degs)/n if n else 0
    # triangles (sum of per-node triangle counts / 3)
    tri_total = sum(nx.triangles(G).values()) // 3
    try:
        avg_clust = nx.average_clustering(G)
    except ZeroDivisionError:
        avg_clust = 0.0
    print(f"Nodes: {n}, Edges: {m}, Avg degree: {avg_deg:.3f}, Triangles: {tri_total}, Avg clustering: {avg_clust:.4f}")
    # quick connected components info
    comps = sorted((len(c) for c in nx.connected_components(G)), reverse=True)
    print(
        f"Components: {len(comps)}, Largest component size: {comps[0] if comps else 0}")


def count_k_cliques(G: nx.Graph, k: int) -> int:
    # count cliques of size exactly k
    return sum(1 for c in nx.enumerate_all_cliques(G) if len(c) == k)


def run_cpm(G: nx.Graph, k: int):
    t0 = time.time()
    comms = [set(c) for c in k_clique_communities(G, k)]
    elapsed = time.time() - t0
    # overlapping nodes count
    counts = {}
    for c in comms:
        for n in c:
            counts[n] = counts.get(n, 0) + 1
    overlaps = sum(1 for v in counts.values() if v > 1)
    return comms, overlaps, elapsed


if __name__ == "__main__":
    path = Path(file_path)
    df = load_adjacency(path)
    df_bin = binarize(df, weight_threshold)

    # Build simple, undirected, unweighted graph
    G = nx.from_pandas_adjacency(df_bin.astype(int))
    G.remove_edges_from(nx.selfloop_edges(G))

    print(
        f"\n=== Graph diagnostics for {path.name} (threshold={weight_threshold}) ===")
    diagnostics(G)

    for k in k_values:
        kc = count_k_cliques(G, k)
        print(f"\nTesting k={k}: found {kc} cliques of size {k}")
        comms, overlaps, t = run_cpm(G, k)
        print(
            f"  CPM communities: {len(comms)}, overlapping nodes: {overlaps}, time: {t:.4f}s")
        if len(comms) == 0:
            print("  -> No percolated communities; consider lowering k or threshold.")
