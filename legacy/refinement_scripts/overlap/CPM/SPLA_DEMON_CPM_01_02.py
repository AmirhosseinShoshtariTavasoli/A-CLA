#!/usr/bin/env python3
# Run CPM, SLPA, DEMON on an adjacency matrix and print only:
# "<METHOD>: overlapping_communities=<int>, time=<seconds>s"
#
# Edit the SETTINGS block below to point to your file and parameters.

import time
from pathlib import Path
import sys
import pandas as pd
import networkx as nx

# ========== SETTINGS ==========
file_path = "adjacency_matrix_Diseasome_output.xlsx"  # <-- put your file here
# None => treat >0 as edge; or set numeric (e.g., 0.0, 0.2)
weight_threshold = None
# CPM
CPM_k = 3
# SLPA
SLPA_T = 100
SLPA_r = 0.03
# DEMON
DEMON_eps = 0.25
# =============================


def load_adjacency(path: Path) -> pd.DataFrame:
    """Load an Excel/CSV adjacency matrix with node labels in both rows and columns."""
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
    """CPM/SLPA/DEMON use unweighted graphs here; binarize weights."""
    if thr is None:
        return (df > 0).astype(int)
    return (df >= thr).astype(int)


def count_overlapping_communities(communities):
    """
    communities: list of sets of node ids
    Returns number of communities that share at least one node with another community.
    """
    if not communities:
        return 0
    # node -> membership count
    counts = {}
    for comm in communities:
        for n in comm:
            counts[n] = counts.get(n, 0) + 1
    overlapping = 0
    for comm in communities:
        if any(counts[n] > 1 for n in comm):
            overlapping += 1
    return overlapping


def run_cpm(G, k):
    from networkx.algorithms.community import k_clique_communities
    t0 = time.time()
    comms = [set(c) for c in k_clique_communities(G, k)]
    elapsed = time.time() - t0
    return comms, elapsed


def run_slpa(G, T, r):
    try:
        from cdlib import algorithms
    except Exception:
        print("SLPA: cdlib not installed", file=sys.stderr)
        return [], 0.0, "missing_cdlib"
    t0 = time.time()
    # Use positional args; many cdlib versions don't accept keywords for T/r/seed
    res = algorithms.slpa(G, T, r)
    elapsed = time.time() - t0
    comms = [set(c) for c in res.communities]
    return comms, elapsed, None


def run_demon(G, eps):
    try:
        from cdlib import algorithms
    except Exception:
        print("DEMON: cdlib not installed", file=sys.stderr)
        return [], 0.0, "missing_cdlib"
    t0 = time.time()
    res = algorithms.demon(G, epsilon=eps)
    elapsed = time.time() - t0
    comms = [set(c) for c in res.communities]
    return comms, elapsed, None


if __name__ == "__main__":
    path = Path(file_path)
    df = load_adjacency(path)
    df_bin = binarize(df, weight_threshold)
    G = nx.from_pandas_adjacency(df_bin.astype(int))
    G.remove_edges_from(nx.selfloop_edges(G))

    # CPM
    comms_cpm, t_cpm = run_cpm(G, CPM_k)
    oc_cpm = count_overlapping_communities(comms_cpm)
    print(f"CPM(k={CPM_k}): overlapping_communities={oc_cpm}, time={t_cpm:.4f}s")

    # SLPA
    comms_slpa, t_slpa, err_slpa = run_slpa(G, SLPA_T, SLPA_r)
    if err_slpa is None:
        oc_slpa = count_overlapping_communities(comms_slpa)
        print(
            f"SLPA(T={SLPA_T}, r={SLPA_r}): overlapping_communities={oc_slpa}, time={t_slpa:.4f}s")
    else:
        print("SLPA: unavailable (install cdlib)")

    # DEMON
    comms_demon, t_demon, err_demon = run_demon(G, DEMON_eps)
    if err_demon is None:
        oc_demon = count_overlapping_communities(comms_demon)
        print(
            f"DEMON(eps={DEMON_eps}): overlapping_communities={oc_demon}, time={t_demon:.4f}s")
    else:
        print("DEMON: unavailable (install cdlib)")
