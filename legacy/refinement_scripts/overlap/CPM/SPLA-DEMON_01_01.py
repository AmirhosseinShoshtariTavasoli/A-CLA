#!/usr/bin/env python3
# Overlapping communities via SLPA / DEMON (CDlib) + execution time
# Put your file name below and run.

import time
from pathlib import Path
import pandas as pd
import networkx as nx

# ========= YOUR SETTINGS =========
file_path = "adjacency_matrix_DanioRerio_output.xlsx"  # <-- change if needed
weight_threshold = None  # None => treat >0 as edge; or set a number, e.g., 0.0 or 0.2
# SLPA params:
SLPA_T = 100
SLPA_r = 0.1
# DEMON params:
DEMON_eps = 0.25
# =================================


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


def overlapping_stats(communities):
    # communities: list of sets
    counts = {}
    for c in communities:
        for n in c:
            counts[n] = counts.get(n, 0) + 1
    overlaps = sum(1 for v in counts.values() if v > 1)
    return len(communities), overlaps


def to_set_list(node_clustering):
    # cdlib NodeClustering -> list[set]
    return [set(comm) for comm in node_clustering.communities]


if __name__ == "__main__":
    path = Path(file_path)
    df = load_adjacency(path)
    df_bin = binarize(df, weight_threshold)

    # Build graph
    G = nx.from_pandas_adjacency(df_bin.astype(int))
    G.remove_edges_from(nx.selfloop_edges(G))

    print(f"\nGraph: {path.name}")
    print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")

    try:
        from cdlib import algorithms
    except Exception as e:
        print("\nCDlib is not installed. Install it with:")
        print("  pip install cdlib")
        print("Then re-run this script to use SLPA/DEMON for overlapping detection.")
        raise SystemExit(0)

    # ---- SLPA ----
    t0 = time.time()
    slpa_res = algorithms.slpa(G, SLPA_T, SLPA_r)
    t_slpa = time.time() - t0
    slpa_comms = to_set_list(slpa_res)
    ncom_s, nover_s = overlapping_stats(slpa_comms)
    print(f"\nSLPA (T={SLPA_T}, r={SLPA_r})")
    print(
        f"  Communities: {ncom_s}, Overlapping nodes: {nover_s}, Time: {t_slpa:.4f}s")

    # ---- DEMON ----
    t0 = time.time()
    demon_res = algorithms.demon(G, epsilon=DEMON_eps)
    t_demon = time.time() - t0
    demon_comms = to_set_list(demon_res)
    ncom_d, nover_d = overlapping_stats(demon_comms)
    print(f"\nDEMON (epsilon={DEMON_eps})")
    print(
        f"  Communities: {ncom_d}, Overlapping nodes: {nover_d}, Time: {t_demon:.4f}s")

    # Optional: show first few communities
    preview = 3
    print("\nPreview of first few SLPA communities:")
    for i, c in enumerate(slpa_comms[:preview], 1):
        print(
            f"  C{i} (size={len(c)}): {sorted(list(c))[:10]}{'...' if len(c) > 10 else ''}")
    print("\nPreview of first few DEMON communities:")
    for i, c in enumerate(demon_comms[:preview], 1):
        print(
            f"  C{i} (size={len(c)}): {sorted(list(c))[:10]}{'...' if len(c) > 10 else ''}")
