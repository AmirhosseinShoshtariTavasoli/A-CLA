#!/usr/bin/env python3
# Leiden (10 runs in one execution) — Modularity only
# ---------------------------------------------------
# Requirements:
#   pip install python-igraph leidenalg pandas
#
# What it does:
#   - Reads Excel/CSV adjacency (square, labels in first row/col)
#   - Builds an undirected graph (optionally binarized >0)
#   - Runs Leiden 10 times with different seeds
#   - Prints only modularity per run + mean±std
#   - Writes CSV: leiden_modularity_runs.csv

import time
from pathlib import Path
import numpy as np
import pandas as pd

# ====== SETTINGS (edit these) ======
FILE_PATH = "adjacency_matrix_DanioRerio_output.xlsx"  # <-- your file
BINARIZE = True       # True: treat >0 as edge (weight=1). False: keep weights.
NUM_RUNS = 10         # number of repetitions inside one execution
SEED_BASE = 42        # base seed; each run uses SEED_BASE + i
N_ITER = -1           # Leiden internal iterations (-1 lets algorithm decide)
# ===================================


def load_adjacency(path: Path) -> pd.DataFrame:
    suf = path.suffix.lower()
    if suf in (".xlsx", ".xls"):
        df = pd.read_excel(path, index_col=0)
    elif suf in (".csv", ".txt"):
        df = pd.read_csv(path, index_col=0)
    else:
        raise ValueError(f"Unsupported file type: {suf}")
    if df.shape[0] != df.shape[1]:
        raise ValueError(f"Adjacency must be square: got {df.shape}")
    # allow reordering if labels match as a set
    if not df.index.equals(df.columns):
        if set(map(str, df.index)) == set(map(str, df.columns)):
            df = df.loc[df.index, df.index]
        else:
            raise ValueError("Row and column labels must match.")
    return df


def to_igraph(df: pd.DataFrame, binarize: bool):
    import igraph as ig
    A = (df.values > 0).astype(float) if binarize else df.values.astype(float)
    g = ig.Graph.Weighted_Adjacency(
        A.tolist(), mode="UNDIRECTED", attr="weight", loops=False)
    if binarize:
        g.es["weight"] = [1.0] * g.ecount()
    else:
        # ensure numeric weights
        g.es["weight"] = [float(w) for w in g.es["weight"]]
    g.vs["name"] = [str(x) for x in df.index]
    return g


def run_leiden_modularity_10(g, num_runs=10, seed_base=42, n_iter=-1):
    import leidenalg as la
    mods = []
    for i in range(num_runs):
        seed = seed_base + i
        # Use the Modularity objective (you can switch to RBConfigurationVertexPartition if needed)
        part = la.find_partition(
            g,
            la.ModularityVertexPartition,
            weights=g.es["weight"],
            n_iterations=n_iter,
            seed=seed,
        )
        # In igraph/leidenalg, partition.quality gives the objective value (here: modularity)
        q = float(part.quality())
        mods.append(q)
        print(f"Leiden_modularity[{i+1}]: {q:.4f}")
    return mods


if __name__ == "__main__":
    path = Path(FILE_PATH)
    df = load_adjacency(path)
    g = to_igraph(df, BINARIZE)

    t0 = time.time()
    modularities = run_leiden_modularity_10(g, NUM_RUNS, SEED_BASE, N_ITER)
    elapsed = time.time() - t0

    mods = np.array(modularities, dtype=float)
    mean_q = mods.mean() if len(mods) else float("nan")
    std_q = mods.std(ddof=1) if len(mods) > 1 else 0.0
    print(f"\nLeiden_modularity_mean: {mean_q:.4f}")
    print(f"Leiden_modularity_std:  {std_q:.4f}")
    print(f"Total_time_for_{NUM_RUNS}_runs: {elapsed:.3f}s")

    # Save CSV for your stats pipeline
    out = pd.DataFrame({
        "run": list(range(1, len(mods)+1)),
        "modularity": mods
    })
    out.to_csv("leiden_modularity_runs.csv", index=False)
    print("Saved: leiden_modularity_runs.csv")
