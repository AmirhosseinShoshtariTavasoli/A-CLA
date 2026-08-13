#!/usr/bin/env python3
# Leading Eigenvector (igraph) — Modularity only (robust version)
# pip install python-igraph

import time
from pathlib import Path
import pandas as pd

# ===== SETTINGS =====
FILE_PATH = "adjacency_matrix_yeast_output.xlsx"   # change to your file
BINARIZE = True  # True: treat >0 as edges; False: use weights
# ====================


def load_adjacency(path: Path) -> pd.DataFrame:
    if path.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(path, index_col=0)
    elif path.suffix.lower() in (".csv", ".txt"):
        df = pd.read_csv(path, index_col=0)
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")
    if df.shape[0] != df.shape[1]:
        raise ValueError("Adjacency matrix must be square.")
    if not df.index.equals(df.columns):
        if set(map(str, df.index)) == set(map(str, df.columns)):
            df = df.loc[df.index, df.index]
        else:
            raise ValueError("Row and column labels must match.")
    return df


def to_igraph_from_adjacency(df: pd.DataFrame, binarize: bool):
    import igraph as ig
    # Ensure no self-loops
    A = (df.values > 0).astype(float) if binarize else df.values.astype(float)
    g = ig.Graph.Weighted_Adjacency(
        A.tolist(), mode="UNDIRECTED", attr="weight", loops=False)
    # If binarized, force weight=1 for edges
    if binarize:
        g.es["weight"] = [1.0] * g.ecount()
    else:
        # Keep original weights; ensure non-negative
        g.es["weight"] = [float(w) for w in g.es["weight"]]
    g.vs["name"] = [str(x) for x in df.index]
    return g


def main():
    import igraph as ig
    path = Path(FILE_PATH)
    df = load_adjacency(path)
    g = to_igraph_from_adjacency(df, BINARIZE)

    t0 = time.time()
    vc = g.community_leading_eigenvector(weights=g.es["weight"])
    elapsed = time.time() - t0

    # --- Robust modularity retrieval ---
    q = None
    try:
        # Newer igraph: modularity is a property (float)
        q = float(vc.modularity)
    except Exception:
        try:
            # Fallback: compute via graph API
            q = float(g.modularity(vc.membership, weights=g.es["weight"]))
        except Exception as e:
            raise RuntimeError(f"Could not compute modularity: {e}")

    print(f"\n=== Leading Eigenvector (igraph) on {path.name} ===")
    print(f"Communities: {len(vc)}")
    print(f"Modularity:  {q:.4f}")
    print(f"Time:        {elapsed:.3f} s")

    # (Optional) small partitions preview
    if len(vc) <= 10:
        for i, comm in enumerate(sorted(vc, key=len, reverse=True), 1):
            names = [g.vs[idx]["name"] for idx in comm]
            print(f"  C{i} (|V|={len(comm)}): sample={names[:10]}")


if __name__ == "__main__":
    main()
